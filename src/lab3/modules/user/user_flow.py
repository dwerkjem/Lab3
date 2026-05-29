import sys
import questionary
import sqlite3
from lab3.modules.crud import CRUD

CRUD = CRUD("data/fountainViewHall.db")


class Customer:

    def __init__(self):
        """sets up `Customer`"""

    def validate_full_name(self, name: str):
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

    def auth(self):
        name_dict = CRUD.make_or_select_existing_autocomplete(
            "customer_id",
            "full_name",
            "customers",
            "What is your full name?",
            self.validate_full_name,
        )
        name = name_dict["value"]
        if name_dict["existed"]:
            print(f"Welcome back {name}")
        else:
            print(f"Thank you for registering {name}")


if __name__ == "__main__":
    Customer().auth()
