from concurrent.futures import ThreadPoolExecutor
import logging
logger=logging.getLogger(__name__)
class MarketDataDownloader:
    def __init__(self,provider,max_workers:int=5):
        self.provider=provider; self.max_workers=max_workers
    def download_symbol(self,symbol,start=None,end=None):
        logger.info("Downloading %s",symbol)
        return self.provider.fetch_daily_data(symbol,start,end)
    def download_many(self,symbols,start=None,end=None):
        out={}
        with ThreadPoolExecutor(max_workers=self.max_workers) as ex:
            fut={ex.submit(self.download_symbol,s,start,end):s for s in symbols}
            for f,s in fut.items():
                out[s]=f.result()
        return out
