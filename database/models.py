import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, ClassVar, Tuple, Union
from hashlib import shake_128

from helpers.config import Configuration


ERRORMSG_RE = re.compile(r"(/var/task/)([A-Za-z0-9_/.]+)(.*\n[\u00a0]{4})(.+)(\n[\u00a0]{2}|$)")
SPRINT_RE = re.compile(r"\d+")


#--- Sources ---#

class Sources:
    CLOUDWATCH = "cloudwatch"
    GITLAB = "gitlab"
    JIRA = "jira"


#--- CloudWatch ---#

@dataclass
class Account:
    """Dataclass representing an AWS Account."""
    name: str
    region: str
    id: int | None = None

    LABEL: ClassVar[str] = "account"

@dataclass
class LogGroup:
    """Dataclass representing an AWS CloudWatch log group."""
    name: str
    project_id: int
    account: str

    LABEL: ClassVar[str] = "loggroup"

    @staticmethod
    def hash_name(name: str) -> str:
        """Return a hash to mask the name of the log group."""
        return shake_128(name.encode("UTF-8")).hexdigest(8)

    @staticmethod
    def transform_mapping(name: str, project_id: int, account: str) -> Dict[str,str|int]:
        """Transform Configuration mappings into a dictionary representation of this class."""
        return {"name": LogGroup.hash_name(name), "project_id": project_id, "account": account}

@dataclass
class ErrorLog:
    """Dataclass representing an AWS CloudWatch error log."""
    loggroup: str
    account: str
    timestamp: int
    message: str | None = None
    author_id: int | None = None

    LABEL: ClassVar[str] = "errorlog"

    @staticmethod
    def log_timestamp_to_epoch(timestamp: str):
        """Transform the AWS log timestamp format to a unix / epoch timestamp."""
        return int(datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f").timestamp())

    @staticmethod
    def query_result_extract_group(data: dict) -> str:
        """Extract the log group name from a CloudWatch query result."""
        return data[0]["value"].split(":")[1]

    @staticmethod
    def query_result_transform_timestamp(data: dict) -> str:
        """Transform the AWS log timestamp format directly from a query result."""
        return ErrorLog.log_timestamp_to_epoch(data[1]["value"])

    @staticmethod
    def transform_query_result(data: dict, account: str) -> Dict[str,str|int]:
        """Transform a CloudWatch query result into a dictionary representation of the class."""
        loggroup = ErrorLog.query_result_extract_group(data)
        return {
            "loggroup": LogGroup.hash_name(loggroup),
            "account": account,
            "timestamp": ErrorLog.query_result_transform_timestamp(data),
            "message": data[2]["value"]
        }

    @staticmethod
    def from_query_result(data: dict, account: str) -> "ErrorLog":
        """Transform a CloudWatch query result into an instance of this class."""
        return ErrorLog(**ErrorLog.transform_query_result(data, account))

    @staticmethod
    def timestamp_to_zulustr(timestamp) -> str:
        """Parse a timestamp to a Zulu-style datetime string."""
        return f"{datetime.fromtimestamp(timestamp).replace(microsecond=0).isoformat()}Z"

    @staticmethod
    def get_error_info(message) -> List[Tuple[str,str]]:
        """Extract the source code lines from the message which potentially caused the error."""
        potential_errors = []
        for prefix, file, infix, statement, suffix in ERRORMSG_RE.findall(message):
            potential_errors.insert(0, (file, statement))
        return potential_errors


#--- GitLab ---#

@dataclass
class User:
    """Dataclass representing a GitLab user."""
    id: str

    LABEL: ClassVar[str] = "user"

    @staticmethod
    def hash_id(id: str) -> str:
        """Return a hash to mask the ID of the user."""
        return shake_128(id.encode("UTF-8")).hexdigest(4)

    @staticmethod
    def transform_user_id(user_id: str) -> Dict[str,str]:
        """Transform a user ID into a dictionary representation of this class."""
        return {
            "id": User.hash_id(user_id)
        }

    @staticmethod
    def from_user_id(user_id: str) -> "User":
        """Transform a user ID into an instance of this class."""
        return User(**User.transform_user_id(user_id))

    @staticmethod
    def transform_merge_participants_input(data: dict) -> Dict[str,str]:
        """Transform merge participants data into a dictionary representation of this class."""
        return {
            "id": User.hash_id(data["username"])
        }

    @staticmethod
    def from_merge_participants_input(data: dict) -> "User":
        """Transform merge participants data into an instance of this class."""
        return User(**User.transform_merge_participants_input(data))

@dataclass
class Commit:
    """Dataclass representing a Git commit in GitLab."""
    id: int
    short_id: str
    timestamp: int
    changed_loc: int
    project_id: int
    author_id: int

    LABEL: ClassVar[str] = "commit"

    @staticmethod
    def transform_input(data: dict, project_id: int, author_id: int) -> Dict[str,str|int]:
        """Transform GitLab commit data into a dictionary representation of this class."""
        return {
            "id": data["id"],
            "short_id": data["short_id"],
            "timestamp": int(datetime.fromisoformat(data["authored_date"]).timestamp()),
            "author_id": author_id,
            "changed_loc": data["stats"]["total"],
            "project_id": project_id
        }

    @staticmethod
    def from_input(data: dict, project_id: int, author_id: int) -> "Commit":
        """Transform GitLab commit data into an instance of this class."""
        return Commit(**Commit.transform_input(data, project_id, author_id))

@dataclass
class Merge:
    """Dataclass representing a merge request in GitLab."""
    id: int
    internal_id: int
    project_id: int
    author_id: int
    timestamp: int
    contributor_ids: List[int] = field(default_factory=lambda:[])
    story_id: int | None = None

    LABEL: ClassVar[str] = "merge"

    @staticmethod
    def transform_input(data: dict, project_acronym: str) -> Dict[str,str|int]:
        """Transform GitLab merge request data into a dictionary representation of the class."""
        story_result = re.search(
            fr"([{project_acronym}]{{5,}}[\s_-]*)(\d+)",
            data["title"]+data["description"], flags=re.I)
        story_id = int(story_result.group(2)) if story_result else None

        return {
            "id": data["id"],
            "internal_id": data["iid"],
            "project_id": data["project_id"],
            "author_id": User.hash_id(data["author"]["username"]),
            "timestamp": int(datetime.fromisoformat(data["merged_at"]).timestamp()),
            "story_id": story_id if story_id and story_id < 1000 else None
        }

    @staticmethod
    def from_input(data: dict, project_acronym: str) -> "Merge":
        """Transform GitLab merge request data into an instance of this class."""
        return Merge(**Merge.transform_input(data, project_acronym))

@dataclass
class Project:
    """Dataclass representing a GitLab project."""
    id: int
    default_branch: str
    log_groups: List[str]
    platforms: List[str]
    technologies: List[str]
    group_id: int | None = None

    LABEL: ClassVar[str] = "project"

    @staticmethod
    def transform_input(data: dict, config: Configuration) -> Dict[str,str|int|List[str]]:
        """Transform GitLab project data into a dictionary representation of this class."""
        project_id = data["id"]
        log_groups = [LogGroup.hash_name(name)for name in
            config.get_log_groups_for_project(project_id)]
        return {
            "id": project_id,
            "default_branch": data["default_branch"],
            "log_groups": log_groups,
            "platforms": config.get_platforms_for_project(project_id),
            "technologies": config.get_technologies_for_project(project_id),
            "group_id": data.get("namespace", {}).get("id", None)
        }

    @staticmethod
    def from_input(data: dict, config: Configuration) -> "Project":
        """Transform GitLab project data into an instance of this class."""
        return Project(**Project.transform_input(data, config))

@dataclass
class Group:
    """Dataclass representing a GitLab group."""
    id: int
    parent_id: int | None = None

    LABEL: ClassVar[str] = "group"

    @staticmethod
    def transform_input(data: dict) -> Dict[str,str|int]:
        """Transform GitLab group data into a dictionary representation of this class."""
        return {
            "id": data["id"],
            "parent_id": data["parent_id"]
        }

    @staticmethod
    def from_input(data: dict) -> "Group":
        """Transform GitLab group data into an instance of this class."""
        return Group(**Group.transform_input(data))


#--- Jira ---#

@dataclass
class Story:
    """Dataclass representing a user story in Jira."""
    id: int
    sprints: List[str] = field(default_factory=lambda:[])

    LABEL: ClassVar[str] = "story"

    @staticmethod
    def transform_input(data: List[str]) -> Dict[str,str|int|List[int]]:
        """Transform exported jira data into a dictionary representation of this class."""
        sprints = []
        for i in range(1, len(data)):
            sprints.append(data[i])

        return {
            "id": int(data[0]),
            "sprints": [int(SPRINT_RE.search(sprint).group()) for sprint in sprints if sprint]
        }

    @staticmethod
    def from_input(data: List[str]) -> "Story":
        """Transform exported jira data into an instance of this class."""
        return Story(**Story.transform_input(data))


#--- Helpers ---#

SOURCE_MAP = {
    Sources.CLOUDWATCH: {Account.LABEL, LogGroup.LABEL, ErrorLog.LABEL},
    Sources.GITLAB: {User.LABEL, Commit.LABEL, Merge.LABEL, Project.LABEL, Group.LABEL},
    Sources.JIRA: {Story.LABEL}
}

TYPE_MAP = {
    Account.LABEL: Account,
    LogGroup.LABEL: LogGroup,
    ErrorLog.LABEL: ErrorLog,
    User.LABEL: User,
    Commit.LABEL: Commit,
    Merge.LABEL: Merge,
    Project.LABEL: Project,
    Group.LABEL: Group,
    Story.LABEL: Story
}

ALL_TYPES = Union[Account, LogGroup, ErrorLog, User, Commit, Merge, Project, Group, Story]
