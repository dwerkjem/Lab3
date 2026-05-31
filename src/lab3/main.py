"""
Name: Derek R. Neilson
Description: CRUD-compliant event booking TUI for Fountain View Hall.
"""

import os
import sys
from pathlib import Path
from typing import Union

import questionary

from lab3.modules.admin import admin_flow
from lab3.modules.user.user_flow import Customer
from lab3.modules.crud.database import Database

db = Database()

BASE_DIR = Path(__file__).parent
ROOT_DIR = BASE_DIR.parent.parent


def run_sql_file(sql_file: Union[str, bytes, os.PathLike]):
    """Runs an sql query from the src directory

    Args:
        sql_file (Union[str, bytes, os.PathLike]): The sql query to run
    """
    sql_file = ROOT_DIR / "src/lab3" / sql_file
    db.cursor.executescript(sql_file.read_text())


run_sql_file("sql/schema.sql")


db.conn.commit()


def user_type() -> str:
    return questionary.select(
        "What type of user are you?", choices=["Customer ", "Admin", "Quit"]
    ).ask()


def main() -> None:
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
