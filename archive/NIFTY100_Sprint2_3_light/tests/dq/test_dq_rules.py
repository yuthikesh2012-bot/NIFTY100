"""
tests/dq/test_dq_rules.py

14 data-quality rule tests for the Sprint 3 Screener + Peer Engine.
Uses small synthetic DataFrames (no DB dependency) so these run fast and
in isolation from the real, occasionally-messy source data.
"""

import math
import pandas as pd
import pytest

from src.screener.engine import apply_metric_filter, load_config
from src.screener.composite import winsorize, scale_0_100, compute_composite_score
from src.analytics.peer import _percent_rank, compute_peer_percentiles, unassigned_companies

CONFIG = load_config()


def _base_df():
    return pd.DataFrame({
        "company_id": ["A", "B", "C"],
        "broad_sector": ["IT", "Financials", "IT"],
        "debt_to_equity": [0.5, 8.0, 3.0],
        "interest_coverage": [3.0, None, 1.0],
        "icr_label": [None, None, None],
        "icr_effective": [3.0, float("nan"), 1.0],
    })


# 1. D/E filter: Financials-sector companies automatically pass a D/E max filter.
def test_de_filter_skips_financials_sector():
    df = _base_df()
    result = apply_metric_filter(df, "de_max", 2.0, CONFIG)
    assert set(result["company_id"]) == {"A", "B"}  # B (Financials, D/E=8) still passes


# 2. Non-Financials company with high D/E correctly fails the D/E max filter.
def test_de_filter_excludes_high_leverage_non_financials():
    df = _base_df()
    result = apply_metric_filter(df, "de_max", 2.0, CONFIG)
    assert "C" not in set(result["company_id"])


# 3. ICR filter: a Debt Free company (icr_effective = +inf) always passes an ICR minimum.
def test_icr_filter_debt_free_treated_as_infinity():
    df = _base_df()
    df.loc[df["company_id"] == "A", "icr_effective"] = float("inf")
    result = apply_metric_filter(df, "icr_min", 100, CONFIG)
    assert "A" in set(result["company_id"])


# 4. ICR filter correctly excludes a company below the threshold.
def test_icr_filter_excludes_below_threshold():
    df = _base_df()
    result = apply_metric_filter(df, "icr_min", 2.0, CONFIG)
    assert "C" not in set(result["company_id"])  # C has ICR 1.0


# 5. Winsorization caps values beyond P10/P90.
def test_winsorize_caps_extremes():
    s = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 1000])
    w = winsorize(s, lower_pct=10, upper_pct=90)
    assert w.max() < 1000


# 6. scale_0_100 output is always within [0, 100] for finite input.
def test_scale_0_100_bounded():
    s = pd.Series([10, 20, 30, 40, 50])
    scaled = scale_0_100(s)
    assert scaled.min() >= 0 and scaled.max() <= 100


# 7. scale_0_100 with invert=True reverses ranking (lower raw value -> higher score).
def test_scale_0_100_invert_reverses_order():
    s = pd.Series([10, 20, 30])
    normal = scale_0_100(s)
    inverted = scale_0_100(s, invert=True)
    assert normal.iloc[0] < normal.iloc[2]
    assert inverted.iloc[0] > inverted.iloc[2]


# 8. Composite score is bounded 0-100 and NaN sub-metrics don't zero it out.
def test_composite_score_renormalises_missing_components():
    df = pd.DataFrame({
        "roe_score": [80.0], "roce_score": [None], "npm_score": [None],
        "fcf_cagr_score": [None], "cfo_pat_ratio_score": [None], "fcf_positive_flag_score": [None],
        "revenue_cagr_score": [None], "pat_cagr_score": [None],
        "de_score": [None], "icr_score": [None],
    })
    result = compute_composite_score(df)
    # Only roe_score (weight 15) is available -> composite should equal 80, not a diluted value.
    assert result["composite_score"].iloc[0] == pytest.approx(80.0)


# 9. percent_rank: highest raw value gets percentile 1.0.
def test_percent_rank_top_value_is_one():
    s = pd.Series([10, 20, 30, 40])
    pct = _percent_rank(s)
    assert pct.iloc[3] == 1.0


# 10. percent_rank: lowest raw value gets percentile 0.0.
def test_percent_rank_bottom_value_is_zero():
    s = pd.Series([10, 20, 30, 40])
    pct = _percent_rank(s)
    assert pct.iloc[0] == 0.0


# 11. D/E peer ranking is inverted: lowest D/E gets the highest percentile.
def test_peer_percentile_de_inversion():
    snapshot = pd.DataFrame({
        "company_id": ["X", "Y", "Z"],
        "year": ["2024-03"] * 3,
        "peer_group_name": ["Grp"] * 3,
        "return_on_equity_pct": [10, 20, 30],
        "net_profit_margin_pct": [1, 2, 3],
        "debt_to_equity": [2.0, 1.0, 0.5],  # Z lowest D/E -> should rank highest
        "free_cash_flow_cr": [1, 2, 3],
        "pat_cagr_5yr": [1, 2, 3],
        "revenue_cagr_5yr": [1, 2, 3],
        "eps_cagr_5yr": [1, 2, 3],
        "asset_turnover": [1, 2, 3],
        "icr_effective": [1, 2, 3],
    })
    result = compute_peer_percentiles(snapshot)
    de_rows = result[result["metric"] == "D/E"].set_index("company_id")
    assert de_rows.loc["Z", "percentile_rank"] == 1.0
    assert de_rows.loc["X", "percentile_rank"] == 0.0


# 12. Companies with no peer group are reported via a message, not an exception.
def test_unassigned_companies_returns_message_not_error():
    snapshot = pd.DataFrame({
        "company_id": ["Q"],
        "peer_group_name": ["No peer group assigned"],
    })
    result = unassigned_companies(snapshot)
    assert result == ["Q"]


# 13. Companies with no peer group are excluded from compute_peer_percentiles output (no crash).
def test_compute_peer_percentiles_skips_unassigned_without_error():
    snapshot = pd.DataFrame({
        "company_id": ["Q"],
        "year": ["2024-03"],
        "peer_group_name": ["No peer group assigned"],
        "return_on_equity_pct": [10], "net_profit_margin_pct": [1],
        "debt_to_equity": [1.0], "free_cash_flow_cr": [1], "pat_cagr_5yr": [1],
        "revenue_cagr_5yr": [1], "eps_cagr_5yr": [1], "asset_turnover": [1],
        "icr_effective": [1],
    })
    result = compute_peer_percentiles(snapshot)
    assert result.empty


# 14. A single-company peer group gets percentile 1.0 (top of a group of one), not a divide-by-zero error.
def test_percent_rank_single_company_group_no_divide_by_zero():
    s = pd.Series([42.0])
    pct = _percent_rank(s)
    assert pct.iloc[0] == 1.0
