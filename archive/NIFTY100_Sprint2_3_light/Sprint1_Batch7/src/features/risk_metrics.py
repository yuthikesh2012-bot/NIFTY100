import pandas as pd
import numpy as np
def daily_returns(s): return s.pct_change()
def weekly_returns(s): return s.resample("W").last().pct_change()
def monthly_returns(s): return s.resample("ME").last().pct_change()
def rolling_volatility(r,w=20): return r.rolling(w).std()
def sharpe_ratio(r,rf=0.0):
    ex=r-rf/252
    return np.sqrt(252)*ex.mean()/ex.std()
def max_drawdown(s):
    peak=s.cummax(); dd=(s-peak)/peak; return dd.min()
