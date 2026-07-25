from __future__ import annotations
import pandas as pd
class FeatureEngine:
    def add_returns(self,df:pd.DataFrame)->pd.DataFrame:
        out=df.copy(); out["daily_return"]=out["Close"].pct_change(); return out
