"""
src/screener/engine.py

Day 15-16 — Filter Engine Core + 6 Preset Screeners.

Loads config/screener_config.yaml and applies threshold filters to the
merged screener DataFrame (see data_loader.load_screener_dataframe /
latest_year_snapshot / year_over_year_de).

Special-case handling (per sprint spec):
  - D/E filter: Financials-sector companies automatically pass any D/E max
    filter (high leverage is structurally normal for banks/NBFCs/insurers).
  - ICR filter: a "Debt Free" company (icr_label == 'Debt Free') is treated
    as ICR = +inf, so it always clears any ICR minimum threshold.
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional
import yaml
import numpy as np
import pandas as pd

from src.screener.data_loader import (
    load_screener_dataframe, latest_year_snapshot, year_over_year_de,
)
from src.screener.composite import add_component_scores, compute_composite_score

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "config" / "screener_config.yaml"


def load_config(path: Path = CONFIG_PATH) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Generic threshold filters (Day 15) — 15 filterable metrics
# ---------------------------------------------------------------------------

def apply_metric_filter(df: pd.DataFrame, metric_key: str, threshold: float,
                         config: dict) -> pd.DataFrame:
    """Apply a single filterable_metrics entry (see screener_config.yaml) to df."""
    spec = config["filterable_metrics"][metric_key]
    col, direction, special = spec["column"], spec["direction"], spec.get("special")

    if special == "debt_free_is_infinity":
        series = df["icr_effective"]
    else:
        series = df[col]

    if direction == "min":
        mask = series >= threshold
    else:  # max
        mask = series <= threshold

    if special == "skip_financials_sector":
        mask = mask | (df["broad_sector"] == "Financials")

    return df[mask.fillna(False)]


def apply_filters(df: pd.DataFrame, filters: dict, config: dict) -> pd.DataFrame:
    """Apply a dict of {metric_key: threshold} filters in sequence."""
    result = df
    for metric_key, threshold in filters.items():
        if metric_key in config["filterable_metrics"]:
            result = apply_metric_filter(result, metric_key, threshold, config)
    return result


# ---------------------------------------------------------------------------
# Day 16 — 6 Preset Screeners
# ---------------------------------------------------------------------------

def run_preset(snapshot_df: pd.DataFrame, preset_name: str, config: dict) -> pd.DataFrame:
    """
    Runs one named preset (as defined in screener_config.yaml presets:) against
    a one-row-per-company snapshot DataFrame (must already carry
    `composite_score`, `de_declining_yoy` if turnaround_watch is used).
    Returns a DataFrame sorted by composite_score descending.
    """
    rules = config["presets"][preset_name]["rules"]
    df = snapshot_df

    for key, val in rules.items():
        if key == "de_equals":
            df = df[df["debt_to_equity"] == val]
        elif key == "dividend_payout_max":
            df = df[df["dividend_payout_ratio_pct"] <= val]
        elif key == "fcf_positive_latest_year":
            df = df[df["free_cash_flow_cr"] > 0]
        elif key == "de_declining_yoy":
            df = df[df["de_declining_yoy"] == True]  # noqa: E712
        elif key.endswith("_min"):
            metric_key = key
            df = apply_metric_filter(df, metric_key, val, config)
        elif key.endswith("_max"):
            metric_key = key
            df = apply_metric_filter(df, metric_key, val, config)
        else:
            raise ValueError(f"Unrecognised preset rule key: {key}")

    return df.sort_values("composite_score", ascending=False)


def run_all_presets(snapshot_df: pd.DataFrame, config: dict) -> dict:
    """Returns {preset_name: filtered_df} for every preset in the config."""
    return {name: run_preset(snapshot_df, name, config) for name in config["presets"]}


def build_full_snapshot(con=None, sector_relative: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    End-to-end: loads all data, builds the latest-year-per-company snapshot
    with year-over-year D/E and composite score attached.
    Returns (snapshot_df, full_history_df).
    """
    full = load_screener_dataframe(con)
    full = year_over_year_de(full)
    snapshot = latest_year_snapshot(full)

    with_components = add_component_scores(snapshot, full, sector_relative=sector_relative)
    scored = compute_composite_score(with_components)
    return scored, full
