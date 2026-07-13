"""
Normalization utilities for the NIFTY100 ETL pipeline.
"""

import re
import pandas as pd

MONTHS={
    "MAR":"03","MARCH":"03",
    "DEC":"12","DECEMBER":"12",
    "SEP":"09","SEPT":"09","SEPTEMBER":"09",
    "JUN":"06","JUNE":"06"
}

def normalize_ticker(value):
    if value is None:
        return None
    s=str(value).strip().upper()
    s=re.sub(r"\.NS$","",s)
    s=re.sub(r"\.BO$","",s)
    s=re.sub(r"\s+","",s)
    s=s.replace("&","AND")
    return s

def normalize_year(value):
    if pd.isna(value):
        return None
    s=str(value).strip().upper()

    m=re.match(r"(MAR|DEC|SEP|JUN)[-\s]?(\d{2,4})",s)
    if m:
        mon=MONTHS[m.group(1)]
        yr=m.group(2)
        if len(yr)==2:
            yr="20"+yr
        return f"{yr}-{mon}"

    if re.fullmatch(r"\d{4}",s):
        return s

    return s

def normalize_columns(df):
    df=df.copy()
    df.columns=[
        re.sub(r"_+","_",
               c.strip().lower().replace(" ","_"))
        for c in df.columns
    ]
    return df

def trim_strings(df):
    return df.apply(
        lambda c: c.str.strip() if c.dtype=="object" else c
    )

def replace_empty_with_none(df):
    return df.replace(r"^\s*$",None,regex=True)
