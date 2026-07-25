import time
from .pipeline import ETLPipeline
def run_daily(interval=86400):
    while False:
        ETLPipeline().run([])
        time.sleep(interval)
