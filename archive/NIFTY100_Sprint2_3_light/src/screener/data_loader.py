"""
src/screener/data_loader.py

Builds the single merged DataFrame the screener/composite-score engine
operates on: financial_ratios + sales/net_profit (P&L) + broad_sector +
company_name + market valuation fields (P/E, P/B, dividend yield, market cap).

Latest-year convenience helper included since most presets and the
Day 21 spot-checks are run against each company's most recent reported year.
"""

from __future__ import annotations
import sqlite3
from pathlib import Path
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = REPO_ROOT / "database" / "nifty100.db"


def _calendar_year(fr_year: str) -> int:
    """financial_ratios.year is 'YYYY-MM' text -> calendar year int for the market_cap join."""
    return int(str(fr_year)[:4])


def load_screener_dataframe(con: sqlite3.Connection | None = None) -> pd.DataFrame:
    own_con = con is None
    if own_con:
        con = sqlite3.connect(DB_PATH)

    fr = pd.read_sql_query("SELECT * FROM financial_ratios", con)
    pnl = pd.read_sql_query("SELECT company_id, year, sales, net_profit FROM profitandloss", con)
    sectors = pd.read_sql_query("SELECT company_id, broad_sector, sub_sector FROM sectors", con)
    companies = pd.read_sql_query("SELECT id AS company_id, company_name FROM companies", con)
    mcap = pd.read_sql_query(
        "SELECT company_id, year AS mcap_year, market_cap_crore, pe_ratio, pb_ratio, dividend_yield_pct "
        "FROM market_cap", con
    )
    peer = pd.read_sql_query("SELECT company_id, peer_group_name, is_benchmark FROM peer_groups", con)

    df = fr.merge(pnl, on=["company_id", "year"], how="left")
    df = df.rename(columns={"sales": "sales_cr", "net_profit": "net_profit_cr"})
    df = df.merge(sectors, on="company_id", how="left")
    df = df.merge(companies, on="company_id", how="left")

    df["calendar_year"] = df["year"].apply(_calendar_year)
    df = df.merge(mcap, left_on=["company_id", "calendar_year"], right_on=["company_id", "mcap_year"],
                  how="left")
    df = df.drop(columns=["mcap_year"])

    df = df.merge(peer, on="company_id", how="left")
    df["peer_group_name"] = df["peer_group_name"].fillna("No peer group assigned")
    df["is_benchmark"] = df["is_benchmark"].fillna(0).astype(int)

    # Effective ICR for filtering: "Debt Free" (icr_label set, interest_coverage is NULL) -> +inf
    # so an ICR-min filter never excludes a debt-free company.
    df["icr_effective"] = df["interest_coverage"]
    debt_free_mask = df["icr_label"] == "Debt Free"
    df.loc[debt_free_mask, "icr_effective"] = float("inf")

    return df


def latest_year_snapshot(df: pd.DataFrame) -> pd.DataFrame:
    """One row per company_id: the row for that company's most recent `year`."""
    idx = df.groupby("company_id")["year"].idxmax()
    return df.loc[idx].reset_index(drop=True)


def year_over_year_de(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds `de_prior_year` and `de_declining_yoy` (bool) columns: compares each
    row's debt_to_equity against the same company's immediately preceding
    reported year.
    """
    df = df.sort_values(["company_id", "year"]).copy()
    df["de_prior_year"] = df.groupby("company_id")["debt_to_equity"].shift(1)
    df["de_declining_yoy"] = df["de_prior_year"].notna() & (df["debt_to_equity"] < df["de_prior_year"])
    return df
