import sqlite3
def connect(path):
    conn=sqlite3.connect(path)
    conn.execute('PRAGMA foreign_keys=ON')
    return conn
