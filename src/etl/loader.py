from pathlib import Path

import pandas as pd

from .dataset_registry import DATASETS
from .excel_reader import ExcelReader
from .normaliser import normalize_columns, normalize_ticker, normalize_year, replace_empty_with_none, trim_strings


class Loader:
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.reader = ExcelReader()
        self.datasets = {}

    def load_dataset(self, name):
        if name not in DATASETS:
            raise KeyError(name)
        raw_path = self.data_dir / DATASETS[name]
        df = self.reader.read(raw_path)
        cleaned = self._clean_dataframe(name, df)
        self.datasets[name] = cleaned
        return cleaned

    def load_all(self):
        result = {}
        for key in DATASETS:
            try:
                result[key] = self.load_dataset(key)
            except Exception as exc:  # noqa: BLE001
                result[key] = exc
        return result

    def _clean_dataframe(self, name, df):
        df = df.copy()
        df = self._infer_header(df, name)
        df = normalize_columns(df)
        df = trim_strings(df)
        df = replace_empty_with_none(df)
        df = self._apply_name_specific_normalisation(name, df)
        return df

    def _infer_header(self, df, name):
        if name in {"profitandloss", "balancesheet", "cashflow"}:
            return df.iloc[1:].copy()
        if name == "companies":
            return df.iloc[1:].copy()
        return df

    def _apply_name_specific_normalisation(self, name, df):
        if name == "companies":
            if "company_name" in df.columns:
                df["company_name"] = df["company_name"].astype(str).str.title()
            if "ticker" in df.columns:
                df["ticker"] = df["ticker"].apply(normalize_ticker)
            if "company_id" in df.columns:
                df["company_id"] = df["company_id"].astype(str)
        elif name in {"profitandloss", "balancesheet", "cashflow"}:
            if "year" in df.columns:
                df["year"] = df["year"].apply(normalize_year)
            if "company_id" in df.columns:
                df["company_id"] = df["company_id"].astype(str)
        elif name == "stock_prices":
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"], errors="coerce")
        return df
