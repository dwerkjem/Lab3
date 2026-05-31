"""
Name: Derek R. Neilson
Description: Database helpers.
"""

import sqlite3


class Database:
    """Small SQLite helper class for running queries and managing the connection."""

    def __init__(
        self, db_path: str = "data/fountainViewHall.db"
    ) -> None:  # Default database path for the Fountain View Hall application.
        """Open a connection to the SQLite database."""
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

    def fetchall(self, query: str, params: tuple = ()) -> list[tuple]:
        """Run a query and return all rows as tuples."""
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def fetchone(self, query: str, params: tuple = ()) -> tuple | None:
        """Run a query and return one row as a tuple, or None if no row exists."""
        self.cursor.execute(query, params)
        return self.cursor.fetchone()

    def fetch_all_dict(self, query: str, params: tuple = ()) -> list[sqlite3.Row]:
        """Run a query and return all rows as dictionary-like rows."""
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

    def fetch_one_dict(self, query: str, params: tuple = ()) -> sqlite3.Row | None:
        """Run a query and return one dictionary-like row, or None if no row exists."""
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()

    def commit(self):
        """Save pending database changes."""
        self.conn.commit()

    def close(self):
        """Close the database connection."""
        self.conn.close()
