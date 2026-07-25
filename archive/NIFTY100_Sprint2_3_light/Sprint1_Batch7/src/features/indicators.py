import pandas as pd
def sma(s,w): return s.rolling(w).mean()
def ema(s,w): return s.ewm(span=w,adjust=False).mean()
def rsi(s,w=14):
 d=s.diff();g=d.clip(lower=0).rolling(w).mean();l=(-d.clip(upper=0)).rolling(w).mean();rs=g/l;return 100-(100/(1+rs))
def macd(s):
 e12=ema(s,12);e26=ema(s,26);m=e12-e26;sig=ema(m,9);return m,sig
def bollinger(s,w=20,n=2):
 m=sma(s,w);std=s.rolling(w).std();return m+n*std,m-n*std
