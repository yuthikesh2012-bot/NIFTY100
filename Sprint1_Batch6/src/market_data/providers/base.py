from abc import ABC, abstractmethod
import pandas as pd
class MarketDataProvider(ABC):
    @abstractmethod
    def fetch_daily_data(self,symbol:str,start:str|None=None,end:str|None=None)->pd.DataFrame: ...
    @abstractmethod
    def fetch_metadata(self,symbol:str)->dict: ...
