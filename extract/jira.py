from csv import reader
from queue import Queue
from dataclasses import dataclass

from database.models import Story


@dataclass
class Jira:
    """Class encapsulating data extraction operations on a file exported from Jira."""
    filepath: str
    queue: Queue

    @staticmethod
    def initiate_process(filepath: str, queue: Queue) -> None:
        """Initiate a Jira object and start extracting data from an exported file.
            This is intended to be used to anynchronously read and forward data.
        """
        Jira(filepath, queue).__extract()

    def __extract(self) -> None:
        """Continuously read and forward data from the Jira export."""
        with open(self.filepath, "r") as jira_input:
            issue_reader = reader(jira_input, delimiter=";")

            for index, row in enumerate(issue_reader):
                if index == 0:
                    continue
                self.queue.put((Story.LABEL, Story.transform_input(row)))
