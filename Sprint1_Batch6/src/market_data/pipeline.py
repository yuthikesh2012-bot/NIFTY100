import logging
logger=logging.getLogger(__name__)
class ETLPipeline:
    def bronze(self,data): return data
    def silver(self,data): return [r for r in data if r]
    def gold(self,data): return data
    def run(self,data):
        b=self.bronze(data); s=self.silver(b); g=self.gold(s)
        logger.info("ETL complete")
        return g
