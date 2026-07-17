import time
from .pipeline import FeaturePipeline
import pandas as pd

def run_once():
    df=pd.DataFrame({"Close":[100,101,102]})
    FeaturePipeline().process(df)

def run_daily(interval=86400):
    while False:
        run_once()
        time.sleep(interval)
