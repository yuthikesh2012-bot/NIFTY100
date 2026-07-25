import pytest
from src.analytics import cagr as C


def test_normal_cagr_positive_positive():
    result = C.compute_cagr(start=100, end=200, years=5)
    expected = ((200 / 100) ** (1 / 5) - 1) * 100
    assert result.value == pytest.approx(expected)
    assert result.flag is None


def test_decline_to_loss_flag():
    result = C.compute_cagr(start=100, end=-50, years=3)
    assert result.value is None
    assert result.flag == C.DECLINE_TO_LOSS


def test_turnaround_flag():
    result = C.compute_cagr(start=-100, end=50, years=3)
    assert result.value is None
    assert result.flag == C.TURNAROUND


def test_both_negative_flag():
    result = C.compute_cagr(start=-100, end=-50, years=3)
    assert result.value is None
    assert result.flag == C.BOTH_NEGATIVE


def test_zero_base_flag():
    result = C.compute_cagr(start=0, end=50, years=3)
    assert result.value is None
    assert result.flag == C.ZERO_BASE


def test_insufficient_data_flag_via_data_points():
    result = C.compute_cagr(start=100, end=150, years=5, data_points_available=3)
    assert result.value is None
    assert result.flag == C.INSUFFICIENT


def test_cagr_for_window_insufficient_when_series_too_short():
    series = [100, 110, 120]  # only 3 points, need 6 for a 5yr window
    result = C.cagr_for_window(series, years=5)
    assert result.value is None
    assert result.flag == C.INSUFFICIENT


def test_cagr_for_window_normal_case():
    series = [100, 105, 110, 120, 130, 150]  # 6 points -> 5yr window start=100 end=150
    result = C.cagr_for_window(series, years=5)
    expected = ((150 / 100) ** (1 / 5) - 1) * 100
    assert result.value == pytest.approx(expected)
    assert result.flag is None


def test_compute_growth_metrics_covers_all_three_windows():
    series = list(range(100, 100 + 11 * 10, 10))  # 11 points of PnL-style history
    metrics = C.compute_growth_metrics(series, series, series)
    assert metrics.revenue_cagr_3yr.flag is None
    assert metrics.revenue_cagr_5yr.flag is None
    assert metrics.revenue_cagr_10yr.flag is None


def test_positive_positive_exact_same_value_zero_growth():
    result = C.compute_cagr(start=100, end=100, years=5)
    assert result.value == pytest.approx(0.0)
    assert result.flag is None
