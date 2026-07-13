from pathlib import Path
from .dataset_registry import DATASETS
from .excel_reader import ExcelReader
from .normaliser import normalize_columns

class Loader:
    def __init__(self,data_dir):
        self.data_dir=Path(data_dir)
        self.reader=ExcelReader()

    def load_dataset(self,name):
        if name not in DATASETS:
            raise KeyError(name)
        df=self.reader.read(self.data_dir/DATASETS[name])
        return normalize_columns(df)

    def load_all(self):
        result={}
        for k in DATASETS:
            try:
                result[k]=self.load_dataset(k)
            except Exception as e:
                result[k]=e
        return result
