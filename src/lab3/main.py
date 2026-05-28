"""CRUD-compliant event booking CLI for Fountain View Hall."""

import datetime
import holidays
import sqlite3
import questionary
from questionary import Validator, ValidationError, prompt
from pathlib import Path

BASE_DIR = Path(__file__).parent
schema_path = BASE_DIR / "schema.sql"


conn = sqlite3.connect("data/fountainViewHall.db")
cursor = conn.cursor()

cursor.executescript(schema_path.read_text())


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


def customer_flow():
    pass


def tui() -> None:
    questionary.print(
        "Welcome to Fountain View Hall's text user interface!",
        style="bold fg:ansigreen",
    )
    user = user_type()
    if user == "Admin":
        admin_flow()


if __name__ == "__main__":
    tui()
