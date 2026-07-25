import pandas as pd
from src.features.risk_metrics import daily_returns,max_drawdown
def test_metrics():
 s=pd.Series([100,105,102,110])
 assert len(daily_returns(s))==4
 assert max_drawdown(s)<=0
