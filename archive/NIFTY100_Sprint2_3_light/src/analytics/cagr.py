"""
src/analytics/cagr.py

CAGR engine for Revenue / PAT / EPS growth metrics (3yr, 5yr, 10yr windows).

CAGR = ((end / start) ** (1 / n) - 1) * 100

Six edge cases are handled explicitly (per sprint spec). Each returns
(value=None, flag=<FLAG>) except the normal case, which returns
(value=<float>, flag=None).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Sequence


# Flags
DECLINE_TO_LOSS = "DECLINE_TO_LOSS"   # start > 0, end < 0
TURNAROUND = "TURNAROUND"             # start < 0, end > 0
BOTH_NEGATIVE = "BOTH_NEGATIVE"       # start < 0, end < 0
ZERO_BASE = "ZERO_BASE"               # start == 0
INSUFFICIENT = "INSUFFICIENT"         # fewer than n years of data


@dataclass
class CagrResult:
    value: Optional[float]
    flag: Optional[str]


def compute_cagr(start: Optional[float], end: Optional[float], years: int,
                  data_points_available: Optional[int] = None) -> CagrResult:
    """
    Compute CAGR between `start` (n years ago) and `end` (latest), over
    `years` years. `data_points_available` lets the caller signal that there
    isn't actually `years` worth of history (-> INSUFFICIENT), independent of
    whatever start/end were passed in.
    """
    if data_points_available is not None and data_points_available < years:
        return CagrResult(None, INSUFFICIENT)

    if start is None or end is None:
        return CagrResult(None, INSUFFICIENT)

    if start == 0:
        return CagrResult(None, ZERO_BASE)

    if start > 0 and end < 0:
        return CagrResult(None, DECLINE_TO_LOSS)

    if start < 0 and end > 0:
        return CagrResult(None, TURNAROUND)

    if start < 0 and end < 0:
        return CagrResult(None, BOTH_NEGATIVE)

    # Positive + Positive (or trivially end == start == positive) -> normal case
    cagr = ((end / start) ** (1.0 / years) - 1.0) * 100.0
    return CagrResult(cagr, None)


def cagr_for_window(series: Sequence[Optional[float]], years: int) -> CagrResult:
    """
    Convenience wrapper: given a chronologically-ordered series of yearly
    values (oldest -> newest), compute the CAGR over the trailing `years`
    window. Handles INSUFFICIENT automatically based on series length.
    """
    if len(series) < years + 1:
        return CagrResult(None, INSUFFICIENT)
    start = series[-(years + 1)]
    end = series[-1]
    if start is None or end is None:
        return CagrResult(None, INSUFFICIENT)
    return compute_cagr(start, end, years)


@dataclass
class GrowthMetrics:
    revenue_cagr_3yr: CagrResult
    revenue_cagr_5yr: CagrResult
    revenue_cagr_10yr: CagrResult
    pat_cagr_3yr: CagrResult
    pat_cagr_5yr: CagrResult
    pat_cagr_10yr: CagrResult
    eps_cagr_3yr: CagrResult
    eps_cagr_5yr: CagrResult
    eps_cagr_10yr: CagrResult


def compute_growth_metrics(revenue_series: Sequence[Optional[float]],
                            pat_series: Sequence[Optional[float]],
                            eps_series: Sequence[Optional[float]]) -> GrowthMetrics:
    """Compute all 9 CAGR figures (3 metrics x 3 windows) for a single company."""
    return GrowthMetrics(
        revenue_cagr_3yr=cagr_for_window(revenue_series, 3),
        revenue_cagr_5yr=cagr_for_window(revenue_series, 5),
        revenue_cagr_10yr=cagr_for_window(revenue_series, 10),
        pat_cagr_3yr=cagr_for_window(pat_series, 3),
        pat_cagr_5yr=cagr_for_window(pat_series, 5),
        pat_cagr_10yr=cagr_for_window(pat_series, 10),
        eps_cagr_3yr=cagr_for_window(eps_series, 3),
        eps_cagr_5yr=cagr_for_window(eps_series, 5),
        eps_cagr_10yr=cagr_for_window(eps_series, 10),
    )
