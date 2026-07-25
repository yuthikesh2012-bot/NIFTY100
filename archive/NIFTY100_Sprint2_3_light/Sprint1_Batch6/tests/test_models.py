from datetime import date
from src.market_data.models import OHLCVRecord
def test_model():
 r=OHLCVRecord(symbol="INFY",date=date.today(),open=1,high=2,low=1,close=2,volume=100)
 assert r.symbol=="INFY"
