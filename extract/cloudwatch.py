from queue import Queue
from typing import List
from boto3.session import Session
from botocore.exceptions import ClientError

from extract.gitlab import GitLab
from helpers.config import Configuration, Secrets
from database.models import Account, LogGroup, ErrorLog


QUERY_LIMIT = 10000
ERROR_LOGS_QUERY = """
fields @log, @timestamp, @message
| sort @timestamp asc
| filter @message like 'ERROR'
"""

class QueryStatus:
    IN_PROGRESS = 0
    THROTTLED = 1
    LIMIT_REACHED = 2
    NOT_FOUND = 3

class CloudWatchError(Exception):
    pass

class CloudWatch:
    """Class encapsulating data extraction operations on AWS CloudWatch."""
    def __init__(self, account_id: int, config: Configuration, secrets: Secrets,
        queue: Queue) -> None:

        self.account = Account(**config.get_account_information(account_id), id=account_id)
        self.config = config
        self.queue = queue
        self.gitlab = GitLab(config, secrets)

        self.client = Session(
            profile_name=str(account_id), region_name=self.account.region).client("logs")

    @staticmethod
    def initiate_process(account_id: str, config: Configuration, secrets: Secrets,
        queue: Queue) -> None:
        """Initiate a CloudWatch object and start extracting data.
            This is intended to be used to anynchronously fetch and forward data.
        """
        CloudWatch(account_id, config, secrets, queue).__extract()


    def __start_error_query(self, log_group: str, start: int, limit: int) -> str | int:
        """Start an error query on a specific log group (+ time interval) in CloudWatch."""
        try:
            return self.client.start_query(
                logGroupNames=[log_group],
                startTime=start,
                endTime=limit,
                queryString=ERROR_LOGS_QUERY,
                limit=QUERY_LIMIT
            )["queryId"]
        except ClientError as error:
            if error.response["Error"]["Code"] == "LimitExceededException":
                return QueryStatus.LIMIT_REACHED
            elif error.response["Error"]["Code"] == "ResourceNotFoundException":
                return QueryStatus.NOT_FOUND
            else:
                raise

    def __get_query_results(self, query_id: str) -> List[dict] | int:
        """Try to get the result of a previously started query."""
        try:
            result = self.client.get_query_results(queryId=query_id)
        except ClientError as error:
            if error.response["Error"]["Code"] == "ThrottlingException":
                return QueryStatus.THROTTLED
            else:
                raise

        if result["status"] == "Complete":
            return result["results"]
        elif result["status"] in ("Scheduled","Running"):
            return QueryStatus.IN_PROGRESS
        else:
            raise CloudWatchError(f"Error running query {query_id}: Status {result['status']}")

    def __handle_query_results(self, results: List[dict], log_group: str) -> None:
        """Extract information from a query result and forward it to the database."""
        for result in results:
            log = ErrorLog.transform_query_result(result, self.account.name)
            log["author_id"] = self.gitlab.blame(log, log_group)
            self.queue.put((ErrorLog.LABEL, {k:log[k] for k in log.keys() if k!="message"}))

    def __query_logs(self, log_groups: List[str]):
        """Repeatedly start queries and extract the results once they have finished.
            This spins up as many queries as CloudWatch allows on a single account.
        """
        log_groups = {log_group: (self.config.start_timestamp, self.config.limit_timestamp)
            for log_group in log_groups}
        queries = {}

        while True:
            while log_groups:
                log_group, time_restriction = next(iter(log_groups.items()))
                query = self.__start_error_query(
                    log_group, time_restriction[0], time_restriction[1])

                if query == QueryStatus.LIMIT_REACHED:
                    break
                elif query == QueryStatus.NOT_FOUND:
                    pass
                else:
                    queries[log_group] = query
                log_groups.pop(log_group)

            for i in range(len(queries)-1, -1, -1):
                log_group, query = list(queries.items())[i]

                results = self.__get_query_results(query)

                if results == QueryStatus.IN_PROGRESS:
                    continue
                elif results == QueryStatus.THROTTLED:
                    continue
                else:
                    self.__handle_query_results(results, log_group)

                if len(results) >= QUERY_LIMIT:
                    last_timestamp = ErrorLog.query_result_transform_timestamp(results[-1])
                    log_groups[log_group] = (last_timestamp, self.config.limit_timestamp)

                queries.pop(log_group)

            if not log_groups and not queries:
                break

    def __add_account(self) -> None:
        """Forward the information about the AWS account itself to the database."""
        self.queue.put((Account.LABEL,
            {i:self.account.__dict__[i] for i in self.account.__dict__ if i!="id"}))

    def __add_loggroups(self) -> None:
        """Forward the information about the log groups themselves to the database."""
        for mapping in self.config.get_log_group_mappings():
            self.queue.put((LogGroup.LABEL,
                LogGroup.transform_mapping(*mapping, self.account.name)))

    def __extract(self) -> None:
        """Wrapper for the entire process of fetching data from CloudWatch."""
        self.__add_account()
        self.__add_loggroups()
        self.__query_logs(self.config.log_groups)
