class Dummy:
    def fetch_daily_data(self,s,*a,**k): return {"symbol":s}
from src.market_data.downloader import MarketDataDownloader
def test_download():
 d=MarketDataDownloader(Dummy())
 r=d.download_many(["INFY","TCS"])
 assert "INFY" in r and "TCS" in r
