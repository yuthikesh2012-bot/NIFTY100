from src.market_data.repository import MarketDataRepository
class S(list):
    def commit(self): pass
    def rollback(self): pass
def test_repo():
 s=S(); r=MarketDataRepository(s)
 assert r.bulk_upsert([1,2,3])==3
