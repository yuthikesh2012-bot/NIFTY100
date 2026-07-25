from .base import MarketDataProvider
class NSEProvider(MarketDataProvider):
    def fetch_daily_data(self,*a,**k): raise NotImplementedError
    def fetch_metadata(self,*a,**k): raise NotImplementedError
