from pathlib import Path
import pandas as pd
from .file_detector import detect_header

class ExcelReader:
    """Production-oriented Excel reader."""
    def read(self, file_path:str, sheet_name=0):
        path=Path(file_path)
        if not path.exists():
            raise FileNotFoundError(path)
        header=detect_header(path.name)
        return pd.read_excel(path, sheet_name=sheet_name, header=header)

    def read_all_sheets(self,file_path:str):
        path=Path(file_path)
        header=detect_header(path.name)
        return pd.read_excel(path,sheet_name=None,header=header)

    def validate_columns(self,df,required):
        missing=[c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"Missing columns: {missing}")
        return True
