"""
src/analytics/peer.py

Day 18 — Peer Percentile Rankings.

Computes PERCENT_RANK for 10 metrics within each peer group, on each
company's latest reported year, and writes the results into a
`peer_percentiles` table in SQLite.

Metrics ranked (10): ROE, ROCE (proxy), Net Profit Margin, D/E (inverted -
lower is better), FCF, PAT CAGR 5yr, Revenue CAGR 5yr, EPS CAGR 5yr,
Interest Coverage, Asset Turnover.

Companies with no peer group assigned are skipped with a message returned
to the caller rather than raising an error.
"""

from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Optional
import pandas as pd

from src.screener.data_loader import load_screener_dataframe, latest_year_snapshot

REPO_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = REPO_ROOT / "database" / "nifty100.db"

# metric_name -> (dataframe column, invert)
PEER_METRICS = {
    "ROE": ("return_on_equity_pct", False),
    "ROCE": ("roce_proxy", False),
    "Net Profit Margin": ("net_profit_margin_pct", False),
    "D/E": ("debt_to_equity", True),          # lower D/E = higher percentile
    "FCF": ("free_cash_flow_cr", False),
    "PAT CAGR 5yr": ("pat_cagr_5yr", False),
    "Revenue CAGR 5yr": ("revenue_cagr_5yr", False),
    "EPS CAGR 5yr": ("eps_cagr_5yr", False),
    "Interest Coverage": ("icr_for_peer_ranking", False),
    "Asset Turnover": ("asset_turnover", False),
}


def _percent_rank(series: pd.Series) -> pd.Series:
    """
    PERCENT_RANK equivalent: for each value, the fraction of the group's
    values it is >= to (0 = lowest, 1 = highest). NaNs stay NaN.
    Matches SQL PERCENT_RANK() = (rank - 1) / (n - 1) when ties are handled
    by average rank; for n == 1 the sole company gets 1.0 (top of a group of one).
    """
    n = series.notna().sum()
    if n <= 1:
        return series.apply(lambda x: 1.0 if pd.notna(x) else None)
    ranks = series.rank(method="average", ascending=True)
    return (ranks - 1) / (n - 1)


def compute_peer_percentiles(snapshot_df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns a long-format DataFrame: company_id, peer_group_name, metric,
    value, percentile_rank, year — one row per (company, metric) within a
    peer group. Companies with no peer group are excluded from this frame
    (caller can report them via `unassigned_companies`).
    """
    df = snapshot_df.copy()
    if "roce_proxy" not in df.columns:
        df["roce_proxy"] = df["return_on_equity_pct"]  # fallback consistent with composite.py
    finite_icr = df["icr_effective"].replace([float("inf")], pd.NA)
    icr_cap = finite_icr.max()
    df["icr_for_peer_ranking"] = df["icr_effective"].replace([float("inf")], icr_cap)

    assigned = df[df["peer_group_name"] != "No peer group assigned"]

    rows = []
    for group_name, grp in assigned.groupby("peer_group_name"):
        for metric_name, (col, invert) in PEER_METRICS.items():
            if col not in grp.columns:
                continue
            pct = _percent_rank(grp[col])
            if invert:
                pct = 1 - pct
            for cid, year, value, p in zip(grp["company_id"], grp["year"], grp[col], pct):
                rows.append({
                    "company_id": cid, "peer_group_name": group_name, "metric": metric_name,
                    "value": value, "percentile_rank": p, "year": year,
                })
    return pd.DataFrame(rows)


def unassigned_companies(snapshot_df: pd.DataFrame) -> list[str]:
    """Companies with 'No peer group assigned' -> message, not an error."""
    return sorted(snapshot_df.loc[
        snapshot_df["peer_group_name"] == "No peer group assigned", "company_id"
    ].unique().tolist())


def write_peer_percentiles_table(con: sqlite3.Connection, percentiles_df: pd.DataFrame) -> int:
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS peer_percentiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id TEXT,
            peer_group_name TEXT,
            metric TEXT,
            value REAL,
            percentile_rank REAL,
            year TEXT
        )
    """)
    cur.execute("DELETE FROM peer_percentiles")
    cur.executemany(
        "INSERT INTO peer_percentiles (company_id, peer_group_name, metric, value, percentile_rank, year) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        list(percentiles_df[["company_id", "peer_group_name", "metric", "value",
                              "percentile_rank", "year"]].itertuples(index=False, name=None)),
    )
    con.commit()
    cur.execute("SELECT COUNT(*) FROM peer_percentiles")
    return cur.fetchone()[0]


def get_message_for_company(company_id: str, snapshot_df: pd.DataFrame) -> Optional[str]:
    """Returns 'No peer group assigned' if applicable, else None."""
    rows = snapshot_df[snapshot_df["company_id"] == company_id]
    if rows.empty:
        return None
    if (rows["peer_group_name"] == "No peer group assigned").all():
        return "No peer group assigned"
    return None
