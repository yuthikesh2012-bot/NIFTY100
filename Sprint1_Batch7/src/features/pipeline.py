import logging
from .engine import FeatureEngine
logger=logging.getLogger(__name__)
class FeaturePipeline:
    def __init__(self):
        self.engine=FeatureEngine()
    def process(self,df):
        logger.info("Generating features")
        return self.engine.add_returns(df)
