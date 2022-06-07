import yaml
from typing import Dict, Iterable, List, Tuple
from dataclasses import dataclass
from cachetools import cached
from cachetools.keys import hashkey

@dataclass
class Secrets:
    """Class to read and provide secrets from a configuration file."""
    gitlab_host: str
    gitlab_token: str

    @staticmethod
    def from_input_file(filepath: str) -> "Secrets":
        """Return an instance of this class based on an input file."""
        with open(filepath, "r") as file:
            return Secrets(**yaml.safe_load(file))

@dataclass
class Configuration:
    """Class to read and provide configuration data from a configuration file."""
    start_time: str
    limit_time: str
    start_timestamp: int
    limit_timestamp: int
    project_acronym: str
    parent_group: str
    aws_accounts: Dict[int,Dict[str,str]]
    technologies: List[str]
    platforms: List[str]
    log_groups: List[str]
    project_mappings: Dict[int, Dict[str,str|List[str]]]
    log_group_mappings: Dict[str, int]
    user_alias: Dict[str, Dict[str,str]]

    @staticmethod
    def from_input_file(filepath: str) -> "Configuration":
        """Return an instance of this class based on an input file."""
        with open(filepath, "r") as file:
            return Configuration(**yaml.safe_load(file))

    @cached(cache={}, key=lambda self, project_id: hashkey(project_id))
    def get_log_groups_for_project(self, project_id: int) -> List[str]:
        """Return all CloudWatch log groups linked to specific GitLab project."""
        return self.project_mappings[project_id]["log_groups"]

    @cached(cache={}, key=lambda self, loggroup: hashkey(loggroup))
    def get_project_for_log_group(self, loggroup: str) -> int:
        """Return the GitLab project linked to a specific CloudWatch log group."""
        return self.log_group_mappings[loggroup]

    def get_platforms_for_project(self, project_id: int) -> List[str]:
        """Return the platforms (AWS / Azure) for a specific GitLab project."""
        return self.project_mappings[project_id]["platforms"]

    def get_technologies_for_project(self, project_id: int) -> List[str]:
        """Return the technologies used in a specific GitLab project."""
        return self.project_mappings[project_id]["technologies"]

    def get_log_group_mappings(self) -> Iterable[Tuple[str, int]]:
        """Return the mappings linking CloudWatch log groups to GitLab projects."""
        for name, project_id in self.log_group_mappings.items():
            yield name, project_id

    def get_account_ids(self) -> List[int]:
        """Return all AWS account IDs."""
        return self.aws_accounts.keys()

    def get_account_information(self, id: int) -> Dict[str,str]:
        """Return information about a specific AWS account."""
        return self.aws_accounts[id]

    def get_user_id(self, mail: str) -> str:
        """Return the ID of a user based on its mail address."""
        return self.user_alias[mail]
