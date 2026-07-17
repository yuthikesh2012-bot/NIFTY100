"""
Normalization utilities for the NIFTY100 ETL pipeline.
"""

import re
from typing import Any

import pandas as pd

MONTHS = {
    "MAR": "03",
    "MARCH": "03",
    "DEC": "12",
    "DECEMBER": "12",
    "SEP": "09",
    "SEPT": "09",
    "SEPTEMBER": "09",
    "JUN": "06",
    "JUNE": "06",
}


def normalize_ticker(value: Any) -> str | None:
    if value is None or pd.isna(value):
        return None
    s = str(value).strip().upper()
    s = re.sub(r"\.NS$", "", s)
    s = re.sub(r"\.BO$", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    s = s.replace("&", "AND")
    if not s:
        return None
    return s


def normalize_year(value: Any) -> str | None:
    if value is None or pd.isna(value):
        return None
    s = str(value).strip().upper()
    if not s:
        return None

    m = re.match(r"(MAR|DEC|SEP|JUN|MARCH|DECEMBER|SEPT|SEPTEMBER|JUN|JUNE)[-\s]?(\d{2,4})", s)
    if m:
        mon = MONTHS[m.group(1)]
        yr = m.group(2)
        if len(yr) == 2:
            yr = f"20{yr}"
        return f"{yr}-{mon}"

    if re.fullmatch(r"\d{4}", s):
        return s
    if re.fullmatch(r"\d{4}-\d{2}", s):
        return s
    return s


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [
        re.sub(r"_+", "_", c.strip().lower().replace(" ", "_"))
        for c in df.columns
    ]
    return df


def trim_strings(df: pd.DataFrame) -> pd.DataFrame:
    return df.apply(lambda c: c.str.strip() if c.dtype == "object" else c)


def replace_empty_with_none(df: pd.DataFrame) -> pd.DataFrame:
    return df.replace(r"^\s*$", None, regex=True)
