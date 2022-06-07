import requests
from queue import Queue
from typing import Any, Dict, Iterable, List, Tuple
from dataclasses import dataclass
from cachetools import cached
from cachetools.keys import hashkey
from urllib.parse import quote_plus

from helpers.config import Configuration, Secrets
from database.models import ErrorLog, User, Commit, Group, Merge, Project


class GitLabError(Exception):
    pass

@dataclass
class GitLab:
    """Class encapsulating data extraction operations on GitLab."""
    config: Configuration
    secrets: Secrets
    queue: Queue | None = None

    @staticmethod
    def initiate_process(config: Configuration, secrets: Secrets, queue: Queue) -> None:
        """Initiate a GitLab object and start extracting data.
            This is intended to be used to anynchronously fetch and forward data.
        """
        GitLab(config, secrets, queue).__extract()

    @cached(cache={}, key=lambda self, url: hashkey(url))
    def __get(self, url: str) -> requests.Response:
        """Cached function for an authorized call to a specific resource on the GitLab API."""
        response = requests.get(url, headers = {"PRIVATE-TOKEN": self.secrets.gitlab_token})

        if response.ok:
            return response
        else:
            raise GitLabError(f"Requesting {url} failed: {response.text}")

    def __fetch(self, uri: str, additional_params: Dict[str, Any] = {}) -> requests.Response:
        """Prepare the URL for the GitLab API with specified parameters and fetch data."""
        url = f"{self.secrets.gitlab_host}/api/v4{uri}"
        if additional_params:
            url = self.__add_to_querystring(url, additional_params)
        return self.__get(url)

    def __fetch_single(self, uri: str, additional_params: Dict[str, Any] = {}) -> Dict | List:
        """Fetch a resource from GitLab which does not use pagination."""
        return self.__fetch(uri, additional_params).json()

    def __fetch_all(self, uri: str, additional_params: Dict[str, Any] = {}) -> Iterable[Dict]:
        """Fetch a resource from GitLab which uses pagination.
            This will call the API until there is no more information available.
        """
        while True:
            response = self.__fetch(uri, additional_params)
            for dataset in response.json():
                yield dataset

            if next_page := response.headers.get("X-Next-Page", None):
                additional_params["page"] = next_page
            else:
                break

    def __add_to_querystring(self, url: str, params: Dict[str, Any]) -> str:
        """Prepare a URL with specified query parameters."""
        updated = requests.PreparedRequest()
        updated.prepare_url(url, params)
        return updated.url

    @cached(cache={}, key=lambda self, user: hashkey(user["id"]))
    def __add_user(self, user: Dict) -> None:
        """Forward user data to the database."""
        self.queue.put((User.LABEL, user))

    def __fetch_groups(self, base_group_id: int) -> Iterable[str]:
        """Fetch group data from GitLab based on a parent group and forward to the database."""
        self.queue.put((
            Group.LABEL,
            Group.transform_input(self.__fetch_single(f"/groups/{base_group_id}/"))
        ))

        yield base_group_id

        for group in self.__fetch_all(f"/groups/{base_group_id}/descendant_groups"):
            group = Group.transform_input(group)
            self.queue.put((Group.LABEL, group))
            yield group["id"]

    def __fetch_projects(self, group_id: int) -> Iterable[str]:
        """Fetch projects contained in a GitLab group and forward them to the database."""
        for project in self.__fetch_all(f"/groups/{group_id}/projects", {"archived": "false"}):
            if (project["created_at"] >= self.config.start_time
                and project["created_at"] <= self.config.limit_time):
                project = Project.transform_input(project, self.config)
                self.queue.put((Project.LABEL, project))
                yield project["id"]

    def __fetch_commits_and_authors(self, project_id: int) -> None:
        """Fetch commits and authors of a GitLab project and forward them to the database."""
        for commit in self.__fetch_all(
            f"/projects/{project_id}/repository/commits",{
                "with_stats": "true",
                "since": self.config.start_time,
                "until": self.config.limit_time }):

            userid = self.__get_user_identifiers(commit["author_email"])
            user = User.transform_user_id(userid)

            self.__add_user(user)

            self.queue.put(
                (Commit.LABEL, Commit.transform_input(commit, project_id, user["id"])))

    def __fetch_merges_and_contributors(self, project_id: int) -> None:
        """Fetch merge requests and contributors of a GitLab project and forward the data."""
        for dataset in self.__fetch_all(
            f"/projects/{project_id}/merge_requests", {
                "state": "merged",
                "created_after": self.config.start_time,
                "updated_before": self.config.limit_time }):

            merge = Merge.from_input(dataset, self.config.project_acronym)

            for contributor in self.__fetch_single(
                f"/projects/{project_id}/merge_requests/{merge.internal_id}/participants"):

                user = User.transform_merge_participants_input(contributor)
                self.__add_user(user)
                if user["id"] != merge.author_id:
                    merge.contributor_ids.append(user["id"])

            self.queue.put((Merge.LABEL, merge.__dict__))

    def __fetch_most_recent_commit(self, project_id: int, time: str) -> str:
        """Fetch the most recent commit of a project in GitLab."""
        return self.__fetch_single(
            f"/projects/{project_id}/repository/commits",
            {"with_stats": "true", "until": time})[0]["id"]

    @cached(cache={}, key=lambda self, project_id, file, time: hashkey(project_id, file, time))
    def __fetch_blame(self, project_id: int, file: str, time: str) -> None:
        """Fetch blame information from a GitLab project based on the file and the timestamp."""
        last_commit = self.__fetch_most_recent_commit(project_id, time)

        return self.__fetch_all(
            f"/projects/{project_id}/repository/files/{quote_plus(file)}/blame",
            {"ref": last_commit})

    @cached(cache={}, key=lambda self, mail: hashkey(mail))
    def __get_user_identifiers(self, mail: str) -> str:
        """Fetch user information from GitLab and return the username."""
        try:
            data = self.__fetch_single(f"/search", {"scope": "users", "search": mail})[0]
            return data["username"]
        except IndexError:
            return self.config.get_user_id(mail)

    def __extract(self) -> None:
        """Wrapper for the entire process of fetching data from GitLab."""
        for group_id in self.__fetch_groups(self.config.parent_group):
            for project_id in self.__fetch_projects(group_id):
                self.__fetch_commits_and_authors(project_id)
                self.__fetch_merges_and_contributors(project_id)

    def blame(self, log: dict, loggroup: str) -> int | None:
        """Attempt to fetch blame information for a CloudWatch error log."""
        time = ErrorLog.timestamp_to_zulustr(log["timestamp"])
        for file, statement in ErrorLog.get_error_info(log["message"]):
            try:
                for item in self.__fetch_blame(
                    self.config.get_project_for_log_group(loggroup), file, time):

                    if statement in [line.strip() for line in item["lines"]]:
                        userid = self.__get_user_identifiers(item["commit"]["author_email"])
                        return User.hash_id(userid)

            except GitLabError:
                continue
