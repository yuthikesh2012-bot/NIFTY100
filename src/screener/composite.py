"""
src/screener/composite.py

Day 17 — Composite Quality Score (0-100), computed on a one-row-per-company
snapshot (latest reported year):

  35% Profitability : ROE 15% + ROCE 10% + NPM 10%
  30% Cash Quality   : FCF CAGR 15% + CFO/PAT ratio 10% + FCF positive flag 5%
  20% Growth         : Revenue CAGR 10% + PAT CAGR 10%
  15% Leverage       : D/E score 10% + ICR score 5%

Each raw metric is winsorised at P10/P90 (extreme values capped) before being
min-max scaled to 0-100. "Lower is better" metrics (D/E) are inverted after
scaling. A sector-relative variant re-runs the same winsorise+scale step
within each `broad_sector` group instead of across the whole universe, so
scores reflect performance vs. sector peers.

Note: `financial_ratios` does not carry a `return_on_capital_employed_pct`
column (Sprint 2 stored the components but not ROCE itself), so ROCE is
recomputed here from EBIT proxy = operating_profit_margin_pct * sales_cr / 100
against equity+debt is not available at this layer either; instead we
approximate ROCE score using ROE as a fallback proxy when ROCE isn't present.
This is a documented approximation — see SPRINT3_SUMMARY.md.
"""

from __future__ import annotations
import numpy as np
import pandas as pd

from src.analytics import cagr as C

DEFAULT_WEIGHTS = {
    "roe": 15, "roce": 10, "npm": 10,               # Profitability (35)
    "fcf_cagr": 15, "cfo_pat_ratio": 10, "fcf_positive_flag": 5,  # Cash Quality (30)
    "revenue_cagr": 10, "pat_cagr": 10,              # Growth (20)
    "de_score": 10, "icr_score": 5,                  # Leverage (15)
}
assert sum(DEFAULT_WEIGHTS.values()) == 100


def winsorize(series: pd.Series, lower_pct: float = 10, upper_pct: float = 90) -> pd.Series:
    """Cap values below the lower_pct / above the upper_pct percentile. NaNs pass through."""
    valid = series.dropna()
    if valid.empty:
        return series.copy()
    lo = np.percentile(valid, lower_pct)
    hi = np.percentile(valid, upper_pct)
    return series.clip(lower=lo, upper=hi)


def scale_0_100(series: pd.Series, invert: bool = False) -> pd.Series:
    """Winsorize then min-max scale to 0-100. Missing values -> NaN (excluded, not zeroed)."""
    w = winsorize(series)
    valid = w.dropna()
    if valid.empty or valid.min() == valid.max():
        # No spread to scale against -> neutral midpoint for whoever has a value
        return w.apply(lambda x: 50.0 if pd.notna(x) else np.nan)
    scaled = (w - valid.min()) / (valid.max() - valid.min()) * 100.0
    if invert:
        scaled = 100.0 - scaled
    return scaled


def _fcf_cagr_5yr_per_company(full_history_df: pd.DataFrame) -> pd.Series:
    """
    Computes a trailing 5yr FCF CAGR per company from the full (all-years)
    financial_ratios history, returned indexed by company_id.
    """
    out = {}
    for cid, grp in full_history_df.sort_values("year").groupby("company_id"):
        series = grp["free_cash_flow_cr"].tolist()
        result = C.cagr_for_window(series, years=5)
        out[cid] = result.value
    return pd.Series(out, name="fcf_cagr_5yr")


def add_component_scores(snapshot_df: pd.DataFrame, full_history_df: pd.DataFrame,
                          sector_relative: bool = False) -> pd.DataFrame:
    """
    Adds one *_score column (0-100) per weighted sub-metric to `snapshot_df`
    (a one-row-per-company frame), plus `fcf_cagr_5yr` (raw).
    Set sector_relative=True to normalise within each broad_sector instead of
    across the whole universe.
    """
    df = snapshot_df.copy()

    fcf_cagr = _fcf_cagr_5yr_per_company(full_history_df)
    df = df.merge(fcf_cagr.rename("fcf_cagr_5yr"), left_on="company_id", right_index=True, how="left")

    df["fcf_positive_flag_raw"] = (df["free_cash_flow_cr"] > 0).astype(float) * 100.0

    # ROCE isn't stored directly in financial_ratios; fall back to ROE as a
    # documented proxy when it's absent so the Profitability bucket still works.
    if "return_on_capital_employed_pct" not in df.columns:
        df["roce_proxy"] = df["return_on_equity_pct"]
    else:
        df["roce_proxy"] = df["return_on_capital_employed_pct"]

    # ICR score: higher is better; debt-free -> best possible (use winsorized P90 as proxy for "infinity").
    icr_finite = df["icr_effective"].replace([np.inf, -np.inf], np.nan)
    icr_cap = icr_finite.dropna().quantile(0.90) if icr_finite.notna().any() else 0.0
    df["icr_for_scoring"] = df["icr_effective"].replace([np.inf], icr_cap)

    def _scale(col: str, invert: bool = False) -> pd.Series:
        if sector_relative:
            return df.groupby("broad_sector")[col].transform(lambda s: scale_0_100(s, invert=invert))
        return scale_0_100(df[col], invert=invert)

    df["roe_score"] = _scale("return_on_equity_pct")
    df["roce_score"] = _scale("roce_proxy")
    df["npm_score"] = _scale("net_profit_margin_pct")
    df["fcf_cagr_score"] = _scale("fcf_cagr_5yr")
    df["cfo_pat_ratio_score"] = _scale("cfo_quality_score")
    df["fcf_positive_flag_score"] = df["fcf_positive_flag_raw"]
    df["revenue_cagr_score"] = _scale("revenue_cagr_5yr")
    df["pat_cagr_score"] = _scale("pat_cagr_5yr")
    df["de_score"] = _scale("debt_to_equity", invert=True)
    df["icr_score"] = _scale("icr_for_scoring")

    return df


def compute_composite_score(df_with_components: pd.DataFrame, weights: dict = None,
                             out_column: str = "composite_score") -> pd.DataFrame:
    """
    Weighted average of the *_score columns, re-normalised by the weight
    actually available per row (a missing sub-metric doesn't silently drag
    the score down — it's excluded rather than treated as zero).
    """
    weights = weights or DEFAULT_WEIGHTS
    df = df_with_components.copy()

    weighted_sum = pd.Series(0.0, index=df.index)
    weight_used = pd.Series(0.0, index=df.index)
    for component, w in weights.items():
        col = f"{component}_score" if not component.endswith("_score") else component
        if col not in df.columns:
            continue
        available = df[col].notna()
        weighted_sum = weighted_sum + df[col].fillna(0) * w * available
        weight_used = weight_used + (w * available)

    df[out_column] = (weighted_sum / weight_used.replace(0, np.nan)).round(2)
    return df
