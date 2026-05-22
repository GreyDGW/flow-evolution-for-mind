import sqlite3
from typing import Optional


class Database:
    def __init__(self, db_path: str = "data/flow_ecosystem.db"):
        self.db_path = db_path
    
    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def execute(self, sql: str, params: tuple = ()):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute(sql, params)
        conn.commit()
        conn.close()
    
    def query(self, sql: str, params: tuple = ()) -> list:
        conn = self.get_connection()
        c = conn.cursor()
        c.execute(sql, params)
        results = c.fetchall()
        conn.close()
        return results
    
    def query_one(self, sql: str, params: tuple = ()) -> Optional[tuple]:
        results = self.query(sql, params)
        return results[0] if results else None