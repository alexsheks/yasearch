from justatom.storing.mask import IDBDocStore
from rethinkdb import r


class IReDocStore(IDBDocStore):

    def __init__(self, host, port, **props):
        super().__init__()
        self.client = r.connect(host=host, port=port)

    async def add_event(self, e):
        pass


__all__ = ["IReDocStore"]
