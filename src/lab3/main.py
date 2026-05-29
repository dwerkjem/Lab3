"""CRUD-compliant event booking CLI for Fountain View Hall."""

import datetime
from typing import Union
import os
import holidays
import sys
import sqlite3
import questionary
from pathlib import Path
from .modules import crud
from .modules.admin import admin_flow

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


def validate_full_name(name):
    if not name:
        return "Name cannot be empty."

    parts = name.strip().split()

    if (
        len(parts) < 2 and name.lower() != "quit"
    ):  # quit can be typed to quit at any time
        return "Please enter at least a first and last name."

    if len(parts) > 3:
        return "Please only enter a first, (optional) middle, and a last name"

    if not all(part.isalpha() for part in parts):
        return "Name should only contain letters and spaces."

    return True


def customer_auth():
    cursor.execute("SELECT customer_id, full_name FROM customers")
    customers = cursor.fetchall()

    customer_lookup = {full_name: customer_id for customer_id, full_name in customers}
    customer_lookup["Quit"] = 0
    list_of_options = list(customer_lookup.keys())

    selected_name = questionary.autocomplete(
        "What is your full name?",
        choices=list_of_options,
        validate=validate_full_name,
    ).ask()
    selected_name = str(selected_name)  # unnecessary but helps with type hinting

    selected_name = selected_name.strip().title()

    if selected_name == "Quit":
        sys.exit(0)

    if selected_name in customer_lookup:
        return customer_lookup[selected_name]

    if selected_name is not None:
        cursor.execute("INSERT INTO customers (full_name) VALUES (?)", (selected_name,))
        conn.commit()
        print(f"Welcome {selected_name}, your account has been created!")

        return cursor.lastrowid
    else:
        sys.exit(1)


def tui() -> None:
    questionary.print(
        "Welcome to Fountain View Hall's text user interface!",
        style="bold fg:ansigreen",
    )
    user = user_type()
    if user == "Admin":
        if admin_flow.Admin.auth():
            pass
    elif user == "Customer":
        customer_auth()
    else:
        print("Good bye!")
        sys.exit(0)


if __name__ == "__main__":
    pass
