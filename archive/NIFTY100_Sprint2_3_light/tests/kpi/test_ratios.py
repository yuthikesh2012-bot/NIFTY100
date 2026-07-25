import pytest
from src.analytics import ratios as R


# --- Profitability (Day 08) -------------------------------------------------

def test_net_profit_margin_normal():
    assert R.net_profit_margin(net_profit=200, sales=1000) == pytest.approx(20.0)


def test_net_profit_margin_zero_sales_returns_none():
    assert R.net_profit_margin(net_profit=200, sales=0) is None


def test_return_on_equity_negative_equity_returns_none():
    assert R.return_on_equity(net_profit=100, equity_capital=10, reserves=-50) is None


def test_return_on_equity_normal():
    assert R.return_on_equity(net_profit=100, equity_capital=10, reserves=90) == pytest.approx(100.0)


def test_opm_cross_check_mismatch_detected():
    # computed 14.0% vs reported 12.0% -> diff of 2pp > 1pp tolerance -> mismatch
    assert R.opm_cross_check(computed_opm=14.0, reported_opm=12.0) is False


def test_opm_cross_check_within_tolerance():
    assert R.opm_cross_check(computed_opm=12.5, reported_opm=12.0) is True


def test_return_on_capital_employed_normal():
    roce = R.return_on_capital_employed(ebit=300, equity_capital=10, reserves=90, borrowings=100)
    assert roce == pytest.approx(150.0)


def test_return_on_assets_zero_total_assets_returns_none():
    assert R.return_on_assets(net_profit=100, total_assets=0) is None


def test_sector_relative_roce_flag_uses_sector_median_for_financials():
    # Financials company with ROCE below absolute threshold but above sector median -> healthy
    assert R.sector_relative_roce_flag(
        company_roce=6.0, sector_median_roce=5.0, is_financials_sector=True,
        absolute_threshold=10.0,
    ) is True


# --- Leverage & Efficiency (Day 09) ----------------------------------------

def test_debt_to_equity_debt_free_returns_zero_not_none():
    assert R.debt_to_equity(borrowings=0, equity_capital=10, reserves=90) == 0.0


def test_debt_to_equity_normal():
    assert R.debt_to_equity(borrowings=50, equity_capital=10, reserves=90) == pytest.approx(0.5)


def test_high_leverage_flag_true_for_non_financials_high_de():
    assert R.high_leverage_flag(de_ratio=6.0, is_financials_sector=False) is True


def test_high_leverage_flag_suppressed_for_financials():
    assert R.high_leverage_flag(de_ratio=6.0, is_financials_sector=True) is False


def test_interest_coverage_ratio_interest_zero_returns_none():
    assert R.interest_coverage_ratio(operating_profit=300, other_income=20, interest=0) is None


def test_icr_label_debt_free():
    assert R.icr_label(icr=None) == "Debt Free"


def test_icr_label_not_debt_free_when_icr_present():
    assert R.icr_label(icr=2.5) is None


def test_icr_warning_flag_below_threshold():
    assert R.icr_warning_flag(icr=1.2) is True


def test_icr_warning_flag_above_threshold():
    assert R.icr_warning_flag(icr=2.0) is False


def test_asset_turnover_zero_total_assets_returns_none():
    assert R.asset_turnover(sales=500, total_assets=0) is None


def test_net_debt_normal():
    assert R.net_debt(borrowings=100, investments=30) == 70
