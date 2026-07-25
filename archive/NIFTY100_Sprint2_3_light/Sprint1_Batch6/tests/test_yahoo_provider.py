from src.market_data.providers import YahooFinanceProvider

def test_provider_creation(): assert YahooFinanceProvider() is not None
