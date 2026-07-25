import sqlite3
from pathlib import Path

def create_database(schema_file, db_file):
    conn=sqlite3.connect(db_file)
    conn.executescript(Path(schema_file).read_text())
    conn.commit()
    conn.close()
