"""
Name: Derek R. Neilson
Description: CRUD-compliant event booking TUI for Fountain View Hall.
"""

import os
import sys
from pathlib import Path

import questionary

from lab3.modules.admin import admin_flow
from lab3.modules.user.user_flow import Customer
from lab3.modules.crud.database import Database

db = Database()

BASE_DIR = Path(__file__).parent
ROOT_DIR = BASE_DIR.parent.parent


def run_sql_file(sql_file: str | bytes | os.PathLike) -> None:
    """Run a SQL script file from the lab3 source directory.

    Args:
        sql_file (str | bytes | os.PathLike): SQL file path relative to src/lab3.
    """
    sql_file = ROOT_DIR / "src/lab3" / sql_file
    db.cursor.executescript(sql_file.read_text())


# Ensure the database schema exists before the application starts.
run_sql_file("sql/schema.sql")


db.conn.commit()


def user_type() -> str | None:
    """Prompt the user to choose Customer, Admin, or Quit."""
    return questionary.select(
        "What type of user are you?", choices=["Customer", "Admin", "Quit"]
    ).ask()


def main() -> None:
    """Start the Fountain View Hall TUI and route the user by role."""
    questionary.print(
        "Welcome to Fountain View Hall's text user interface!",
        style="bold fg:ansigreen",
    )
    user = user_type()
    if user == "Admin":
        admin_flow.main()
    elif user == "Customer":
        Customer().main()
    else:
        print("Good bye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
