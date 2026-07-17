import pandas as pd
from src.features.indicators import sma,ema,rsi
def test_inds():
 s=pd.Series([1,2,3,4,5,6,7,8,9,10,11,12,13,14,15])
 assert len(sma(s,3))==len(s)
 assert len(ema(s,3))==len(s)
 assert len(rsi(s))==len(s)
