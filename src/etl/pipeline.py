from pathlib import Path
import sqlite3

import pandas as pd

from .loader import Loader
from .validator import Validator


class ETLPipeline:
    def __init__(self, data_dir, db_path, output_dir):
        self.data_dir = Path(data_dir)
        self.db_path = Path(db_path)
        self.output_dir = Path(output_dir)
        self.loader = Loader(data_dir)
        self.validator = Validator()

    def execute(self):
        datasets = self.loader.load_all()
        self._write_database(datasets)
        self._write_audit(datasets)
        self._write_validation_failures(datasets)
        return datasets

    def _write_database(self, datasets):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        try:
            for name, frame in datasets.items():
                if isinstance(frame, pd.DataFrame):
                    frame.to_sql(self._table_name(name), conn, if_exists="replace", index=False)
        finally:
            conn.close()

    def _write_audit(self, datasets):
        rows = []
        for name, frame in datasets.items():
            if isinstance(frame, pd.DataFrame):
                rows.append({"table": self._table_name(name), "row_count": len(frame), "rejections": 0})
        pd.DataFrame(rows, columns=["table", "row_count", "rejections"]).to_csv(self.output_dir / "load_audit.csv", index=False)

    def _write_validation_failures(self, datasets):
        failures = self.validator.validate(datasets)
        failures.to_csv(self.output_dir / "validation_failures.csv", index=False)

    def _table_name(self, name):
        return name
