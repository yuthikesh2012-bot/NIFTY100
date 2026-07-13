from .loader import Loader
class ETLPipeline:
    def __init__(self,data_dir):
        self.loader=Loader(data_dir)
    def execute(self):
        return self.loader.load_all()
