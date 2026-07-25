"""
src/analytics/quality_score.py

composite_quality_score: a single 0-100 blended score used for quick
screening. It averages whichever of the following sub-scores are available
for a given company-year (missing inputs are simply skipped, not treated
as zero):

  - ROE score       : return_on_equity_pct scaled to /30 -> 0-100, capped
  - ROCE score       : return_on_capital_employed_pct scaled to /20 -> 0-100, capped
  - Interest safety score : 100 if debt-free or ICR >= 3, 60 if 1.5 <= ICR < 3,
                            20 if ICR < 1.5
  - CFO quality score     : High Quality=100, Moderate=60, Accrual Risk=20

This is a heuristic screening aid, not a rigorous valuation metric.
"""

from __future__ import annotations
from typing import Optional


def _clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))


def _roe_score(roe_pct: Optional[float]) -> Optional[float]:
    if roe_pct is None:
        return None
    return _clamp((roe_pct / 30.0) * 100.0)


def _roce_score(roce_pct: Optional[float]) -> Optional[float]:
    if roce_pct is None:
        return None
    return _clamp((roce_pct / 20.0) * 100.0)


def _interest_safety_score(icr: Optional[float], is_debt_free: bool) -> Optional[float]:
    if is_debt_free:
        return 100.0
    if icr is None:
        return None
    if icr >= 3.0:
        return 100.0
    if icr >= 1.5:
        return 60.0
    return 20.0


def _cfo_quality_score_component(cfo_quality_label: Optional[str]) -> Optional[float]:
    mapping = {"High Quality": 100.0, "Moderate": 60.0, "Accrual Risk": 20.0}
    if cfo_quality_label is None:
        return None
    return mapping.get(cfo_quality_label)


def composite_quality_score(roe_pct: Optional[float], roce_pct: Optional[float],
                             icr: Optional[float], is_debt_free: bool,
                             cfo_quality_label_value: Optional[str]) -> Optional[float]:
    components = [
        _roe_score(roe_pct),
        _roce_score(roce_pct),
        _interest_safety_score(icr, is_debt_free),
        _cfo_quality_score_component(cfo_quality_label_value),
    ]
    usable = [c for c in components if c is not None]
    if not usable:
        return None
    return round(sum(usable) / len(usable), 2)
