"""
Name: Derek R. Neilson
Description: CRUD-compliant event booking CLI for Fountain View Hall.
"""

import datetime
from typing import Union
import os
import holidays
import sys
import sqlite3
import questionary
from pathlib import Path
from lab3.modules import crud
from lab3.modules.admin.admin_flow import Admin
from lab3.modules.user.user_flow import Customer

BASE_DIR = Path(__file__).parent
ROOT_DIR = BASE_DIR.parent.parent


data_dir = ROOT_DIR / "data"

db_path = data_dir / "fountainViewHall.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()


def run_sql_file(sql_file: Union[str, bytes, os.PathLike]):
    """Runs an sql query from the src directory

    Args:
        sql_file (Union[str, bytes, os.PathLike]): The sql query to run
    """
    sql_file = ROOT_DIR / "src/lab3" / sql_file
    cursor.executescript(sql_file.read_text())


run_sql_file("sql/schema.sql")
run_sql_file("sql/drop_quit.sql")


conn.commit()


def user_type() -> str:
    return questionary.select(
        "What type of user are you?", choices=["Customer", "Admin", "Quit"]
    ).ask()


def tui() -> None:
    questionary.print(
        "Welcome to Fountain View Hall's text user interface!",
        style="bold fg:ansigreen",
    )
    user = user_type()
    if user == "Admin":
        Admin.main()
    elif user == "Customer":
        Customer().auth()
    else:
        print("Good bye!")
        sys.exit(0)


if __name__ == "__main__":
    tui()
