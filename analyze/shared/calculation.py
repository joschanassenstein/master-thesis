from typing import List
from tinydb.queries import where
from database.models import Commit
from database.database import Database

def average(values: List[int|float]) -> float | None:
    """Calculate the average of a list of values."""
    if not len(values) == 0:
        return sum(values) / len(values)

def ownership(commits: int, locc: int, total_commits: int, total_locc: int) -> float:
    """Calculate the Code Ownership based on number of commits and lines changed."""
    return ((commits/total_commits)+(locc/total_locc))/2

def query_and_calculate_ownership(database: Database, project_id: int, timestamp: int, author: str = None) -> float:
    """Query data from the database and calculate the Code Ownership of a project or an author."""
    commits = database.query(Commit.LABEL,
        ((where("project_id") ==project_id) & (where("timestamp") < timestamp)))
    return calculate_ownership(commits, author)

def calculate_ownership(commits: List[Commit], author: str = None) -> float:
    """Calculate the Code Ownership of a project or an author."""
    contributors = {}
    total_commits = len(commits)
    total_locc = sum([commit.changed_loc for commit in commits])

    if not commits:
        return 1.0

    for commit in commits:
        if commit.author_id not in contributors:
            contributors[commit.author_id] = {"commits": 0, "locc": 0}

        contributors[commit.author_id]["commits"] += 1
        contributors[commit.author_id]["locc"] += commit.changed_loc

    if author:
        return ownership(
            contributors[author]["commits"], contributors[author]["locc"],
            total_commits, total_locc)
    else:
        ownership_shares = [
            ownership(
                contributors[contributor]["commits"], contributors[contributor]["locc"],
                total_commits, total_locc
            ) for contributor in contributors
        ]
        return max(ownership_shares)
