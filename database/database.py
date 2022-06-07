from queue import Queue
from typing import List, Dict
from tinydb import TinyDB, Query
from tinydb.table import Table
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware

from database.models import SOURCE_MAP, TYPE_MAP, ALL_TYPES


class Database:
    """This class provides all required operations on the TinyDB database."""
    def __init__(self, filepath: str, cached: bool = False) -> None:
        storage = CachingMiddleware(JSONStorage) if cached else JSONStorage
        self.db: TinyDB = TinyDB(filepath, sort_keys=True, indent=4, storage=storage)
        self.tables: Dict[str,Table] = {label:self.db.table(label) for label in TYPE_MAP.keys()}

    @staticmethod
    def initiate_process(filepath: str, queue: Queue, cached: bool = False) -> None:
        """Initiate a database object and listen on a queue.
            This is intended to be used to asynchronously write data to the database.
        """
        Database(filepath, cached).__listen(queue)

    def insert(self, label: str, document: dict) -> int:
        """Insert a document to a specific table in the database."""
        return self.tables[label].insert(document)

    def query(self, label: str, query: Query) -> List[ALL_TYPES]:
        """Perform a query on a specific table."""
        return [TYPE_MAP[label](**result) for result in self.tables[label].search(query)]

    def all(self, label: str) -> List[ALL_TYPES]:
        """Get all items of a specific type / from a specific table."""
        return [TYPE_MAP[label](**result) for result in self.tables[label].all()]

    def clear(self, source: str) -> None:
        """Empty the database of a specific source. A source specifies a collection of types."""
        for label in SOURCE_MAP[source]:
            self.tables[label].truncate()

    def __listen(self, queue: Queue) -> None:
        """Listen to a queue and insert documents accordingly.
            This is intended to be used to asynchronously write data to the database.
        """
        with self.db:
            while True:
                label, document = queue.get()
                if label != None:
                    self.insert(label, document)
                else:
                    return
