import sqlite3


class Database:
    def __init__(self, db_path: str = "data/fountainViewHall.db"):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

    def fetchall(self, query: str, params: tuple = ()):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def fetchone(self, query: str, params: tuple = ()):
        self.cursor.execute(query, params)
        return self.cursor.fetchone()

    def fetch_all_dict(self, query: str, params: tuple = ()):
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

    def fetch_one_dict(self, query: str, params: tuple = ()):
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()
