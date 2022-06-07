from typing import List
from pathlib import Path
from datetime import datetime
from tabulate import tabulate
from tinydb.queries import where
from argparse import ArgumentParser
from multiprocessing import Process, Manager

from extract.jira import Jira
from extract.gitlab import GitLab
from extract.cloudwatch import CloudWatch

from helpers.concurrency import visualize
from helpers.config import Configuration, Secrets

from database.database import Database
from database.models import Sources, Account, LogGroup, ErrorLog
from database.models import User, Commit, Merge, Project, Group, Story


# Resolve local paths for required files.
DIR = Path().resolve()
INPUT_DIR = DIR.joinpath("_input")
CONFIG_DIR = DIR.joinpath("_config")
JIRA_PATH = INPUT_DIR.joinpath("jira.csv")
DATABASE_PATH = DIR.joinpath("database").joinpath("_db.json")


if __name__ == "__main__":

    start = datetime.now()

    #---                 Initialize console application                  ---#
    # Provide options to extract data from specific sources or all at once. #

    parser = ArgumentParser(
        description="Analyze effects of Collective Code Ownership on Software Development",
        epilog="Developed by Joscha Nassenstein"
    )

    parser.add_argument("-c", "--cloudwatch", dest="cloudwatch",
        action="store_true", help="Extract from Cloudwatch")
    parser.add_argument("-g", "--gitlab", dest="gitlab",
        action="store_true", help="Extract from GitLab")
    parser.add_argument("-j", "--jira", dest="jira",
        action="store_true", help="Extract from Jira")
    parser.add_argument("-a", "--all", dest="all",
        action="store_true", help="Extract from all sources")
    args = parser.parse_args()

    config = Configuration.from_input_file(f"{CONFIG_DIR}/configuration.yaml")
    secrets = Secrets.from_input_file(f"{CONFIG_DIR}/secrets.yaml")


    #---                       Optional: Extract data (if specified)                       ---#
    #  The application starts a process for each source and also each AWS Account separately. #

    if any([args.all, args.cloudwatch, args.gitlab, args.jira]):
        producers: List[Process] = []
        database_queue = Manager().Queue()
        database = Database(DATABASE_PATH)

        if args.cloudwatch or args.all:
            database.clear(Sources.CLOUDWATCH)
            for accountid in config.get_account_ids():
                producers.append(Process(
                    name=f"CloudWatch[{accountid}]",
                    target=CloudWatch.initiate_process,
                    args=(accountid, config, secrets, database_queue)))

        if args.gitlab or args.all:
            database.clear(Sources.GITLAB)
            producers.append(Process(
                name="GitLab",
                target=GitLab.initiate_process,
                args=(config, secrets, database_queue)))

        if args.jira or args.all:
            database.clear(Sources.JIRA)
            producers.append(Process(
                name="Jira",
                target=Jira.initiate_process,
                args=(JIRA_PATH, database_queue)))

        for process in producers:
            process.start()

        consumer = Process(
            name="Database",
            target=Database.initiate_process,
            args=(DATABASE_PATH, database_queue, True))
        consumer.start()

        visualize(producers)

        for process in producers:
            process.join()

        database_queue.put((None, None))
        consumer.join()


    #---                 Basic analysis                 ---#
    # This provides an overview of all the extracted data. #

    database = Database(DATABASE_PATH, cached=True)
    users = database.all(User.LABEL)

    print()
    print(tabulate(
        headers=["Platform", "Metric", "Value"],
        tabular_data=[
            ["Gitlab", "Groups", len(database.all(Group.LABEL))],
            ["Gitlab", "Projects", len(database.all(Project.LABEL))],
            ["Gitlab", "Commits", len(database.all(Commit.LABEL))],
            ["Gitlab", "Merges", len(database.all(Merge.LABEL))],
            ["Gitlab", "Merges with user stories",
                len(database.query(Merge.LABEL, where("story_id") != None))],
            ["Gitlab", "Merges with review",
                len(database.query(Merge.LABEL, where("contributor_ids") != []))],
            ["Gitlab", "Contributors", len(users)],
            ["Jira", "Stories", len(database.all(Story.LABEL))],
            ["Cloudwatch", "Accounts", len(database.all(Account.LABEL))],
            ["Cloudwatch", "Dev: Log groups",
                len(database.query(LogGroup.LABEL, where("account") == "development"))],
            ["Cloudwatch", "Dev: Error logs",
                len(database.query(ErrorLog.LABEL, where("account") == "development"))],
            ["Cloudwatch", "Dev: Assigned Error logs", len(database.query(ErrorLog.LABEL,
                (where("author_id") != None) & (where("account") == "development")))],
            ["Cloudwatch", "Prod: Log groups",
                len(database.query(LogGroup.LABEL, where("account") == "production"))],
            ["Cloudwatch", "Prod: Error logs",
                len(database.query(ErrorLog.LABEL, where("account") == "production"))],
            ["Cloudwatch", "Prod: Assigned Error logs", len(database.query(ErrorLog.LABEL,
                (where("author_id") != None) & (where("account") == "production")))]
        ],
        tablefmt="presto"
    ))
    print()
    print(tabulate(
        headers=["User", "Commits", "Lines Changed", "Merges"],
        tabular_data=[[
            userid,
            len(database.query(Commit.LABEL, where("author_id") == userid)),
            sum([commit.changed_loc
                for commit in database.query(Commit.LABEL, where("author_id") == userid)]),
            len(database.query(Merge.LABEL, where("author_id") == userid))
        ] for userid in [user.id for user in users]],
        tablefmt="presto"
    ))

    print(f"\n\nExecution time: {datetime.now() - start}")
