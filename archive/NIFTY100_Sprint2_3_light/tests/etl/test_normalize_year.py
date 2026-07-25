import pytest
from src.etl.normaliser import normalize_year

@pytest.mark.parametrize("inp,expected",[
("2024","2024"),
("Mar-24","2024-03"),
("MAR24","2024-03"),
("Dec-2023","2023-12"),
("Sep24","2024-09"),
("Jun 25","2025-06"),
("2020","2020"),
("2019","2019"),
("2018","2018"),
("2017","2017"),
("2016","2016"),
("2015","2015"),
("2014","2014"),
("2013","2013"),
("2012","2012"),
("2011","2011"),
("2010","2010"),
("2009","2009"),
("2008","2008"),
("2007","2007"),
])
def test_normalize_year(inp,expected):
    assert normalize_year(inp)==expected
