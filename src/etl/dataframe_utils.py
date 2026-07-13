import pandas as pd

def report(df):
    return {
        "rows": len(df),
        "columns": len(df.columns),
        "nulls": df.isna().sum().to_dict()
    }

def reorder_columns(df, cols):
    return df[[c for c in cols if c in df.columns]]
