import pandas as pd
from src.features.pipeline import FeaturePipeline
from src.features.validator import validate_features
def test_pipeline():
    df=pd.DataFrame({"Close":[100,101,102]})
    out=FeaturePipeline().process(df)
    assert validate_features(out)
