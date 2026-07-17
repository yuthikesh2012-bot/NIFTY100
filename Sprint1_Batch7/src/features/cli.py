import argparse
from .pipeline import FeaturePipeline
import pandas as pd

def main():
    parser=argparse.ArgumentParser(description="Feature Engineering CLI")
    parser.add_argument("--run",action="store_true")
    args=parser.parse_args()
    if args.run:
        df=pd.DataFrame({"Close":[100,101,102]})
        print(FeaturePipeline().process(df).tail())

if __name__=="__main__":
    main()
