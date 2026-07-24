"""
src/analytics/ratios.py

Profitability, Leverage, and Efficiency ratio functions for the NIFTY100
Financial Ratio Engine (Sprint 2 / Epic 02).

All functions are pure and operate on plain numeric inputs (no DB access),
which makes them trivially unit-testable. `None` is used consistently to
represent "not computable" (division by zero / undefined denominator),
matching the sprint spec.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


# ---------------------------------------------------------------------------
# Day 08 — Profitability Ratios
# ---------------------------------------------------------------------------

def net_profit_margin(net_profit: float, sales: float) -> Optional[float]:
    """Net Profit Margin (%) = net_profit / sales * 100. None if sales == 0."""
    if sales == 0:
        return None
    return (net_profit / sales) * 100.0


def operating_profit_margin(operating_profit: float, sales: float) -> Optional[float]:
    """Operating Profit Margin (%) = operating_profit / sales * 100."""
    if sales == 0:
        return None
    return (operating_profit / sales) * 100.0


def opm_cross_check(computed_opm: Optional[float], reported_opm: Optional[float],
                     tolerance_pct: float = 1.0) -> bool:
    """
    Cross-check computed OPM against the source `opm_percentage` field.
    Returns True if the two agree within `tolerance_pct` (percentage points).
    A return value of False should be logged by the caller.
    """
    if computed_opm is None or reported_opm is None:
        return True  # nothing to compare
    return abs(computed_opm - reported_opm) <= tolerance_pct


def return_on_equity(net_profit: float, equity_capital: float, reserves: float) -> Optional[float]:
    """ROE (%) = net_profit / (equity_capital + reserves) * 100. None if denom <= 0."""
    denom = equity_capital + reserves
    if denom <= 0:
        return None
    return (net_profit / denom) * 100.0


def return_on_capital_employed(ebit: float, equity_capital: float, reserves: float,
                                borrowings: float) -> Optional[float]:
    """ROCE (%) = EBIT / (equity_capital + reserves + borrowings) * 100."""
    denom = equity_capital + reserves + borrowings
    if denom <= 0:
        return None
    return (ebit / denom) * 100.0


def sector_relative_roce_flag(company_roce: Optional[float], sector_median_roce: Optional[float],
                               is_financials_sector: bool, absolute_threshold: float = 10.0) -> bool:
    """
    Returns True ("healthy") if the company clears the appropriate ROCE bar.
    Financials-sector companies are judged against the sector median rather
    than the absolute threshold, since bank/NBFC ROCE is structurally lower.
    """
    if company_roce is None:
        return False
    if is_financials_sector and sector_median_roce is not None:
        return company_roce >= sector_median_roce
    return company_roce >= absolute_threshold


def return_on_assets(net_profit: float, total_assets: float) -> Optional[float]:
    """ROA (%) = net_profit / total_assets * 100. None if total_assets == 0."""
    if total_assets == 0:
        return None
    return (net_profit / total_assets) * 100.0


# ---------------------------------------------------------------------------
# Day 09 — Leverage & Efficiency Ratios
# ---------------------------------------------------------------------------

def debt_to_equity(borrowings: float, equity_capital: float, reserves: float) -> float:
    """
    D/E = borrowings / (equity_capital + reserves).
    Returns 0 (not None) when borrowings == 0 (debt-free company).
    """
    if borrowings == 0:
        return 0.0
    denom = equity_capital + reserves
    if denom <= 0:
        # Negative/zero equity with real debt -> undefined but not "debt free";
        # surface as None so callers don't mistake it for a genuinely low D/E.
        return None
    return borrowings / denom


def high_leverage_flag(de_ratio: Optional[float], is_financials_sector: bool,
                        threshold: float = 5.0) -> bool:
    """True if D/E > threshold AND the company is NOT in the Financials sector."""
    if de_ratio is None or is_financials_sector:
        return False
    return de_ratio > threshold


def interest_coverage_ratio(operating_profit: float, other_income: float,
                             interest: float) -> Optional[float]:
    """ICR = (operating_profit + other_income) / interest. None if interest == 0."""
    if interest == 0:
        return None
    return (operating_profit + other_income) / interest


def icr_label(icr: Optional[float]) -> Optional[str]:
    """Display label for the icr_label column: 'Debt Free' when ICR is None."""
    return "Debt Free" if icr is None else None


def icr_warning_flag(icr: Optional[float], threshold: float = 1.5) -> bool:
    """True if the company may struggle to cover interest payments (ICR < threshold)."""
    if icr is None:
        return False
    return icr < threshold


def net_debt(borrowings: float, investments: float) -> float:
    """Net Debt = borrowings - investments (investments used as liquid-asset proxy)."""
    return borrowings - investments


def asset_turnover(sales: float, total_assets: float) -> Optional[float]:
    """Asset Turnover = sales / total_assets. None if total_assets == 0."""
    if total_assets == 0:
        return None
    return sales / total_assets


@dataclass
class ProfitabilityResult:
    net_profit_margin_pct: Optional[float]
    operating_profit_margin_pct: Optional[float]
    opm_mismatch: bool
    return_on_equity_pct: Optional[float]
    return_on_capital_employed_pct: Optional[float]
    return_on_assets_pct: Optional[float]


@dataclass
class LeverageEfficiencyResult:
    debt_to_equity: Optional[float]
    high_leverage_flag: bool
    interest_coverage: Optional[float]
    icr_label: Optional[str]
    icr_warning_flag: bool
    net_debt: float
    asset_turnover: Optional[float]


def compute_profitability(net_profit: float, sales: float, operating_profit: float,
                           reported_opm_pct: Optional[float], equity_capital: float,
                           reserves: float, borrowings: float, total_assets: float,
                           other_income: float = 0.0) -> ProfitabilityResult:
    npm = net_profit_margin(net_profit, sales)
    opm = operating_profit_margin(operating_profit, sales)
    mismatch = not opm_cross_check(opm, reported_opm_pct)
    roe = return_on_equity(net_profit, equity_capital, reserves)
    ebit = operating_profit + other_income
    roce = return_on_capital_employed(ebit, equity_capital, reserves, borrowings)
    roa = return_on_assets(net_profit, total_assets)
    return ProfitabilityResult(npm, opm, mismatch, roe, roce, roa)


def compute_leverage_efficiency(borrowings: float, equity_capital: float, reserves: float,
                                 operating_profit: float, other_income: float, interest: float,
                                 investments: float, sales: float, total_assets: float,
                                 is_financials_sector: bool) -> LeverageEfficiencyResult:
    de = debt_to_equity(borrowings, equity_capital, reserves)
    hlf = high_leverage_flag(de, is_financials_sector)
    icr = interest_coverage_ratio(operating_profit, other_income, interest)
    label = icr_label(icr)
    warn = icr_warning_flag(icr)
    nd = net_debt(borrowings, investments)
    at = asset_turnover(sales, total_assets)
    return LeverageEfficiencyResult(de, hlf, icr, label, warn, nd, at)
