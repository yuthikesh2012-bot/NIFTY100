from typing import Iterable
class MarketDataRepository:
    def __init__(self,session):
        self.session=session
    def bulk_upsert(self,records:Iterable):
        for r in records:
            self.session.append(r)
        return len(list(records)) if not isinstance(records,list) else len(records)
