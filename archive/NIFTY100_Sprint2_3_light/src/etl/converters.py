import pandas as pd

def to_numeric(series):
    return pd.to_numeric(series,errors="coerce")

def to_datetime(series):
    return pd.to_datetime(series,errors="coerce")
