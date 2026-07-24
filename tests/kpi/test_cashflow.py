import pytest
from src.analytics import cashflow_kpis as CF


def test_free_cash_flow_allows_negative():
    assert CF.free_cash_flow(operating_activity=100, investing_activity=-150) == -50


def test_cfo_quality_score_high_quality_label():
    score = CF.cfo_quality_score(cfo_series=[120, 130], pat_series=[100, 100])
    assert score == pytest.approx(1.25)
    assert CF.cfo_quality_label(score) == "High Quality"


def test_cfo_quality_score_accrual_risk_label():
    score = CF.cfo_quality_score(cfo_series=[30], pat_series=[100])
    assert CF.cfo_quality_label(score) == "Accrual Risk"


def test_cfo_quality_score_skips_zero_pat_years():
    score = CF.cfo_quality_score(cfo_series=[50, 60], pat_series=[0, 60])
    assert score == pytest.approx(1.0)


def test_capex_intensity_label_asset_light():
    intensity = CF.capex_intensity(investing_activity=-20, sales=1000)
    assert intensity == pytest.approx(2.0)
    assert CF.capex_intensity_label(intensity) == "Asset Light"


def test_capex_intensity_label_capital_intensive():
    intensity = CF.capex_intensity(investing_activity=-150, sales=1000)
    assert CF.capex_intensity_label(intensity) == "Capital Intensive"


def test_fcf_conversion_rate_zero_operating_profit_returns_none():
    assert CF.fcf_conversion_rate(fcf=50, operating_profit=0) is None


def test_classify_capital_allocation_reinvestor_pattern():
    result = CF.classify_capital_allocation(cfo=100, cfi=-50, cff=-30, pat=200)
    assert (result.cfo_sign, result.cfi_sign, result.cff_sign) == ("+", "-", "-")
    assert result.pattern_label == "Reinvestor"


def test_classify_capital_allocation_distress_signal_pattern():
    result = CF.classify_capital_allocation(cfo=-50, cfi=30, cff=40, pat=-10)
    assert result.pattern_label == "Distress Signal"


def test_classify_capital_allocation_shareholder_returns_variant():
    # High CFO/PAT ratio within the (+,-,-) bucket -> Shareholder Returns
    result = CF.classify_capital_allocation(cfo=150, cfi=-20, cff=-40, pat=100)
    assert result.pattern_label == "Shareholder Returns"
