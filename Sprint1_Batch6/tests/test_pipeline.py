from src.market_data.pipeline import ETLPipeline
def test_pipeline():
    p=ETLPipeline()
    assert p.run([1,None,2])==[1,2]
