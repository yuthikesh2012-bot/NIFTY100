"""
src/analytics/cashflow_kpis.py

Cash Flow KPIs & Capital Allocation classifier (Sprint 2, Day 11).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Sequence


# ---------------------------------------------------------------------------
# Free Cash Flow
# ---------------------------------------------------------------------------

def free_cash_flow(operating_activity: float, investing_activity: float) -> float:
    """FCF = CFO + CFI. Negative values are allowed (real business outcome)."""
    return operating_activity + investing_activity


# ---------------------------------------------------------------------------
# CFO Quality Score
# ---------------------------------------------------------------------------

def cfo_quality_score(cfo_series: Sequence[float], pat_series: Sequence[float]) -> Optional[float]:
    """
    CFO Quality Score = average(CFO / PAT) over up to 5 years.
    Years where PAT == 0 are skipped (undefined ratio for that year).
    Returns None if no year has a usable PAT.
    """
    ratios = []
    for cfo, pat in zip(cfo_series[-5:], pat_series[-5:]):
        if pat == 0:
            continue
        ratios.append(cfo / pat)
    if not ratios:
        return None
    return sum(ratios) / len(ratios)


def cfo_quality_label(score: Optional[float]) -> Optional[str]:
    """>1.0 = High Quality, 0.5-1.0 = Moderate, <0.5 = Accrual Risk."""
    if score is None:
        return None
    if score > 1.0:
        return "High Quality"
    if score >= 0.5:
        return "Moderate"
    return "Accrual Risk"


# ---------------------------------------------------------------------------
# CapEx Intensity
# ---------------------------------------------------------------------------

def capex_intensity(investing_activity: float, sales: float) -> Optional[float]:
    """CapEx Intensity (%) = abs(investing_activity) / sales * 100."""
    if sales == 0:
        return None
    return (abs(investing_activity) / sales) * 100.0


def capex_intensity_label(intensity_pct: Optional[float]) -> Optional[str]:
    """<3% = Asset Light, 3-8% = Moderate, >8% = Capital Intensive."""
    if intensity_pct is None:
        return None
    if intensity_pct < 3.0:
        return "Asset Light"
    if intensity_pct <= 8.0:
        return "Moderate"
    return "Capital Intensive"


# ---------------------------------------------------------------------------
# FCF Conversion Rate
# ---------------------------------------------------------------------------

def fcf_conversion_rate(fcf: float, operating_profit: float) -> Optional[float]:
    """FCF Conversion Rate (%) = FCF / operating_profit * 100."""
    if operating_profit == 0:
        return None
    return (fcf / operating_profit) * 100.0


# ---------------------------------------------------------------------------
# Capital Allocation 8-pattern classifier
# ---------------------------------------------------------------------------

PATTERN_LABELS = {
    ("+", "-", "-"): "Reinvestor",
    ("+", "+", "-"): "Liquidating Assets",
    ("-", "+", "+"): "Distress Signal",
    ("-", "-", "+"): "Growth Funded by Debt",
    ("+", "+", "+"): "Cash Accumulator",
    ("-", "-", "-"): "Pre-Revenue",
    ("+", "-", "+"): "Mixed",
}


def _sign(x: float) -> str:
    if x > 0:
        return "+"
    if x < 0:
        return "-"
    return "+"  # treat exact zero as non-negative for classification purposes


@dataclass
class CapitalAllocationResult:
    cfo_sign: str
    cfi_sign: str
    cff_sign: str
    pattern_label: str


def classify_capital_allocation(cfo: float, cfi: float, cff: float,
                                 pat: Optional[float] = None) -> CapitalAllocationResult:
    """
    Classify a company-year into one of the 8 capital-allocation patterns
    based on the signs of (CFO, CFI, CFF).

    The (+,-,-) bucket splits into "Reinvestor" vs "Shareholder Returns"
    based on CFO/PAT quality (a high-quality-earnings Reinvestor that is
    predominantly returning cash to shareholders via the financing outflow
    is labelled "Shareholder Returns" instead of the default "Reinvestor").
    """
    cfo_s, cfi_s, cff_s = _sign(cfo), _sign(cfi), _sign(cff)
    key = (cfo_s, cfi_s, cff_s)

    if key == ("+", "-", "-"):
        cfo_over_pat = (cfo / pat) if (pat not in (None, 0)) else None
        if cfo_over_pat is not None and cfo_over_pat > 1.0:
            label = "Shareholder Returns"
        else:
            label = "Reinvestor"
    else:
        label = PATTERN_LABELS.get(key, "Mixed")

    return CapitalAllocationResult(cfo_s, cfi_s, cff_s, label)
