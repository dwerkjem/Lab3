"""
Name: Derek R. Neilson
Description: Customer TUI workflow for authentication, reservations, payments, and profile editing.
"""

import re
import sys
from typing import Literal

import questionary

from lab3.modules.crud.database import Database
from lab3.modules.crud.main import CRUD
from lab3.modules.crud.reservations.main import edit_reservations
from lab3.modules.crud.user import edit_customer
from lab3.modules.crud.pricing.verify_payments import make_or_view_payment

db = Database()

crud = CRUD(db)


class Customer:
    """Customer-facing TUI for account lookup, reservations, payments, and profile editing."""

    def __init__(self) -> None:
        """Authenticate or register the customer and store their customer data."""
        self.name_dict = self.auth()
        self.user_name = self.name_dict["value"]
        self.user_id = self.name_dict["id"]
        self.user_existed = self.name_dict["existed"]

    @staticmethod  # use this decorator to make independent of class https://www.geeksforgeeks.org/python/python-staticmethod/
    def validate_full_name(full_name: str) -> str | Literal[True]:
        """Validate a customer's full name."""
        words = full_name.strip().split()

        if len(words) < 2:
            return "Name must have at least two words."

        first_name = words[0]

        if first_name.endswith("."):
            return "First name cannot end in a period."

        if not re.fullmatch(r"[A-Za-z.]+", full_name.replace(" ", "")):
            return "Name can only contain letters, spaces, and periods."

        for word in words:
            if not re.fullmatch(r"[A-Za-z.]+", word):
                return f"'{word}' contains invalid characters."

        return True

    def auth(self) -> dict[str, str | bool | int] | None:
        """Authenticate an existing customer or create a new customer record."""
        return crud.make_or_select_existing_autocomplete(
            "customer_id",
            "full_name",
            "customers",
            "What is your full name?",
            self.validate_full_name,
        )

    def user_options(self) -> str | None:
        """Prompt the customer to choose a main menu option."""
        return questionary.select(
            "What would you like to do?",
            [
                "Make Reservation or Edit Reservations",
                "Make or View Payment",
                "Edit Profile",
                "Back",
                "Quit",
            ],
        ).ask()

    def main(self) -> None:
        """Run the selected customer workflow."""
        if self.user_existed:
            print(f"Welcome back {self.user_name}")
        else:
            print(f"Thank you for registering {self.user_name}")

        while True:
            option = self.user_options()

            if option == "Quit" or option is None:
                print("Good bye!")
                sys.exit(0)

            if option == "Back":
                return

            elif option == "Edit Profile":
                edit_customer(self.user_id, self.user_name)

            elif option == "Make Reservation or Edit Reservations":
                edit_reservations(self.name_dict)

            elif option == "Make or View Payment":
                make_or_view_payment(self.user_id)

if __name__ == "__main__":
    Customer().main()
