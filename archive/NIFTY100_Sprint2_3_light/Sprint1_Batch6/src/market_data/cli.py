import argparse
from .pipeline import ETLPipeline
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--run",action="store_true")
 a=p.parse_args()
 if a.run:
  ETLPipeline().run([])
if __name__=="__main__": main()
