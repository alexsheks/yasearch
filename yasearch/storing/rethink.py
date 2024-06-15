from pathlib import Path
from datetime import datetime
import abc

import rethinkdb as r
import uuid
import os
import yaml

with open(str(Path(os.getcwd()).parent / "config.yaml"), 'r') as file:
    config = yaml.safe_load(file)

rdb = r.RethinkDB()

class IDBDocStore(abc.ABC):
    @abc.abstractmethod
    async def add_search(self, description: str):
        pass


class IReDocStore(IDBDocStore):
    def __init__(self) -> None:
        super().__init__()
    async def add_search(self, description):
        async with await rdb.connect(host=config["db"]["host"], port=config["db"]["port"]) as connection:
            rdb.db(str(config["db"]["database"])).table('events').insert(
                {'description': description}).run(connection)



__all__ = ["IReDocStore"]
