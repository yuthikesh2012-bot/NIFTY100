import pandas as pd
from src.features import FeatureEngine
def test_returns():
 df=pd.DataFrame({"Close":[100,110]})
 r=FeatureEngine().add_returns(df)
 assert "daily_return" in r.columns
