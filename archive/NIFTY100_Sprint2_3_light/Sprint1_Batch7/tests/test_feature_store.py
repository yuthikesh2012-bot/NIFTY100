from src.features.store import FeatureStore
def test_store():
 s=FeatureStore()
 s.save("INFY",{"rsi":60})
 assert s.load("INFY")["rsi"]==60
