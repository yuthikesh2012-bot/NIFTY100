import pandas as pd
import pytest

from src.etl.loader import Loader
from src.etl.normaliser import (
    normalize_columns,
    normalize_ticker,
    normalize_year,
    replace_empty_with_none,
    trim_strings,
)
from src.etl.validator import Validator


@pytest.mark.parametrize(
    "value, expected",
    [
        ("ABB.NS", "ABB"),
        ("ABB.BO", "ABB"),
        ("Reliance", "RELIANCE"),
        ("TCS", "TCS"),
        ("adani green", "ADANI GREEN"),
        ("  bhel  ", "BHEL"),
        ("hdfc bank", "HDFC BANK"),
        ("itc.ns", "ITC"),
        ("infosys.bo", "INFOSYS"),
        ("abc-def", "ABC-DEF"),
        ("abc & co", "ABC AND CO"),
        ("sbi life", "SBI LIFE"),
    ],
)
def test_normalize_ticker_variants(value, expected):
    assert normalize_ticker(value) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        (None, None),
        ("2022", "2022"),
        ("mar-22", "2022-03"),
        ("Mar 2022", "2022-03"),
        ("DEC 2019", "2019-12"),
        ("Sep-18", "2018-09"),
        ("Jun 2020", "2020-06"),
        ("MARCH 2021", "2021-03"),
        ("2018", "2018"),
        ("  2023  ", "2023"),
        ("2023-01", "2023-01"),
        ("N/A", "N/A"),
    ],
)
def test_normalize_year_variants(value, expected):
    assert normalize_year(value) == expected


def test_normalize_columns_lowercases_and_replaces_spaces():
    df = pd.DataFrame([[1]], columns=["Company Name"])
    normalized = normalize_columns(df)
    assert normalized.columns.tolist() == ["company_name"]


def test_trim_strings_strips_object_columns():
    df = pd.DataFrame({"company_name": [" ABB ", "TCS "]})
    trimmed = trim_strings(df)
    assert trimmed.iloc[0, 0] == "ABB"


def test_replace_empty_with_none_converts_blank_strings():
    df = pd.DataFrame({"company_name": ["", "ABB"]})
    cleaned = replace_empty_with_none(df)
    assert cleaned.iloc[0, 0] is None


@pytest.mark.parametrize(
    "dataset_name, expected_columns",
    [
        ("companies", ["id", "company_name"]),
        ("profitandloss", ["id", "company_id", "year"]),
        ("balancesheet", ["id", "company_id", "year"]),
        ("cashflow", ["id", "company_id", "year"]),
        ("sectors", ["id", "company_id"]),
        ("stock_prices", ["id", "company_id", "date"]),
        ("market_cap", ["id", "company_id"]),
        ("financial_ratios", ["id", "company_id"]),
        ("peer_groups", ["id", "company_id"]),
        ("analysis", ["id", "company_id"]),
    ],
)
def test_loader_has_expected_dataset_keys(dataset_name, expected_columns):
    loader = Loader(data_dir="data/raw")
    assert dataset_name in loader.datasets
    assert all(column in loader.datasets[dataset_name].columns for column in expected_columns)


def test_loader_load_dataset_returns_dataframe():
    loader = Loader(data_dir="data/raw")
    df = loader.load_dataset("companies")
    assert isinstance(df, pd.DataFrame)
    assert not df.empty


def test_loader_load_all_returns_dictionary_of_frames():
    loader = Loader(data_dir="data/raw")
    result = loader.load_all()
    assert isinstance(result, dict)
    assert "companies" in result


@pytest.mark.parametrize(
    "frame, expected_rule",
    [
        (pd.DataFrame([{"company_id": "ABB", "year": "2022"}]), "DQ01"),
        (pd.DataFrame([{"company_id": "ABB", "year": "2022"}, {"company_id": "ABB", "year": "2022"}]), "DQ01"),
        (pd.DataFrame([{"company_id": "ABB", "year": "2022", "sales": 10}]), "DQ01"),
        (pd.DataFrame([{"company_id": "ABB", "year": "2022", "sales": None}]), "DQ06"),
        (pd.DataFrame([{"company_id": "ABB", "year": "2022", "net_profit": -1}]), "DQ11"),
        (pd.DataFrame([{"company_id": "ABB", "year": "2022", "company_name": ""}]), "DQ15"),
        (pd.DataFrame([{"company_id": "ABB", "year": "2022", "website": ""}]), "DQ10"),
        (pd.DataFrame([{"company_id": "ABB", "year": "2022", "tax_percentage": 50}]), "DQ08"),
        (pd.DataFrame([{"company_id": "ABB", "year": "2022", "sales": 0}]), "DQ06"),
        (pd.DataFrame([{"company_id": "ABB", "year": "2022", "ebitda": 0}]), "DQ16"),
    ],
)
def test_validator_reports_expected_rule(frame, expected_rule):
    validator = Validator()
    failures = validator.validate_frame("companies", frame)
    assert any(failure["rule"] == expected_rule for failure in failures)


def test_validator_returns_empty_frame_for_clean_dataset():
    validator = Validator()
    frame = pd.DataFrame([{"company_id": "ABB", "year": "2022", "company_name": "Abbott", "website": "https://example.com", "sales": 100, "net_profit": 20, "tax_percentage": 20}])
    failures = validator.validate_frame("companies", frame)
    assert failures == []


def test_validator_summarises_failures_to_dataframe():
    validator = Validator()
    frame = pd.DataFrame([{"company_id": "ABB", "year": "2022", "company_name": ""}])
    failures = validator.validate_frame("companies", frame)
    df = validator.failure_frame(failures)
    assert not df.empty
    assert "rule" in df.columns
