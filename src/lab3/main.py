"""CRUD-compliant event booking CLI for Fountain View Hall."""

import datetime
import holidays
import sqlite3
import questionary
from questionary import Validator, ValidationError, prompt, Choice
from pathlib import Path

BASE_DIR = Path(__file__).parent
schema_path = BASE_DIR / "schema.sql"

data_dir = BASE_DIR / "data"

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
    if password == "Password123":
        questionary.print("Welcome Admin", style="bold fg:ansigreen")
    else:
        questionary.print("You are unauthorized", style="bold fg:ansired")


def validate_full_name(name):
    if not name:
        return "Name cannot be empty."

    parts = name.strip().split()

    if len(parts) < 2:
        return "Please enter at least a first and last name."

    if not all(part.isalpha() for part in parts):
        return "Name should only contain letters and spaces."

    return True


def customer_flow():
    cursor.execute("SELECT customer_id, full_name FROM customers")
    customers = cursor.fetchall()

    customer_lookup = {full_name: customer_id for customer_id, full_name in customers}

    selected_name = questionary.autocomplete(
        "What is your full name?",
        choices=list(customer_lookup.keys()),
        validate=validate_full_name,
    ).ask()

    selected_name = selected_name.strip().title()

    if selected_name in customer_lookup:
        return customer_lookup[selected_name]

    cursor.execute("INSERT INTO customers (full_name) VALUES (?)", (selected_name,))
    conn.commit()
    print(f"Welcome {selected_name}, your acount has been created!")

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
