import pytest
from src.etl.normaliser import normalize_ticker

@pytest.mark.parametrize("inp,expected",[
("tcs","TCS"),
("TCS ","TCS"),
(" tcs ","TCS"),
("INFY.NS","INFY"),
("RELIANCE.BO","RELIANCE"),
("l&t","LANDT"),
("abc","ABC"),
("xyz.ns","XYZ"),
("abc.bo","ABC"),
("HDFCBANK","HDFCBANK"),
("SBIN","SBIN"),
("ITC ","ITC"),
("LTIM","LTIM"),
("M&M","MANDM"),
("ONGC","ONGC"),
])
def test_normalize_ticker(inp,expected):
    assert normalize_ticker(inp)==expected
