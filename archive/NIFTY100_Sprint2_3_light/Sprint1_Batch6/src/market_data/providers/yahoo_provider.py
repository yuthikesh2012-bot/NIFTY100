import logging,yfinance as yf
from .base import MarketDataProvider
from .exceptions import DownloadFailedError
logger=logging.getLogger(__name__)
class YahooFinanceProvider(MarketDataProvider):
    def fetch_daily_data(self,symbol,start=None,end=None):
        try:
            df=yf.Ticker(f"{symbol}.NS").history(start=start,end=end,auto_adjust=True)
            if df.empty: raise DownloadFailedError(symbol)
            return df
        except Exception as e:
            logger.exception(e); raise DownloadFailedError(symbol) from e
    def fetch_metadata(self,symbol): return yf.Ticker(f"{symbol}.NS").info
