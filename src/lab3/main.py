"""CRUD-compliant event booking CLI for Fountain View Hall."""

import datetime
import holidays
import sys
import sqlite3
import questionary
from pathlib import Path
from .modules import crud

BASE_DIR = Path(__file__).parent
ROOT_DIR = BASE_DIR.parent.parent
schema_path = BASE_DIR / "sql/schema.sql"

data_dir =  ROOT_DIR / "data"

db_path = data_dir / "fountainViewHall.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.executescript(schema_path.read_text())
conn.commit()


def user_type() -> str:
    return questionary.select(
        "What type of user are you?", choices=["Customer", "Admin"]
    ).ask()


def admin_flow():
    password = questionary.password(
        "Verify with a password\n  The password is `Password123` for demo purposes"
    ).ask()
    if (
        password == "Password123"
    ):  # in production this would be encrypted and read from a .env file
        questionary.print("Welcome Admin", style="bold fg:ansigreen")
    else:
        questionary.print("You are unauthorized", style="bold fg:ansired")


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

    if (
        selected_name is None
    ):  # If a keyboard interrupt happens we need to exit so it doesn't push to the database.
        sys.exit(1)

    selected_name = selected_name.strip().title()

    if selected_name == "Quit":
        sys.exit(0)

    if selected_name in customer_lookup:
        return customer_lookup[selected_name]

    cursor.execute("INSERT INTO customers (full_name) VALUES (?)", (selected_name,))
    conn.commit()
    print(f"Welcome {selected_name}, your account has been created!")

    return cursor.lastrowid


def tui() -> None:
    questionary.print(
        "Welcome to Fountain View Hall's text user interface!",
        style="bold fg:ansigreen",
    )
    user = user_type()
    if user == "Admin":
        admin_flow()
    else:
        customer_flow()


if __name__ == "__main__":
    tui()
