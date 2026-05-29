import sys
import questionary
import re
from lab3.modules.crud.crud import CRUD
from lab3.modules.crud.database import Database
from lab3.modules.crud.user import edit_customer
from lab3.modules.crud.reservations import edit_reservations

db = Database()

crud = CRUD(db)


class Customer:

    def __init__(self):
        """sets up `Customer`"""
        self.name_dict = self.auth()
        self.user_name = self.name_dict["value"]
        self.user_id = self.name_dict["id"]
        self.user_existed = self.name_dict["existed"]

    @staticmethod  # use this decorator to make independent of class https://www.geeksforgeeks.org/python/python-staticmethod/
    def validate_full_name(full_name: str) -> tuple[bool, str]:
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

    def auth(self):
        return crud.make_or_select_existing_autocomplete(
            "customer_id",
            "full_name",
            "customers",
            "What is your full name?",
            self.validate_full_name,
        )

    def user_options(self):
        return questionary.select(
            "What would you like to do?",
            ["Make Reservation or Edit Reservations", "Edit Profile", "Quit"],
        ).ask()

    def main(self):
        if self.user_existed:
            print(f"Welcome back {self.user_name}")
        else:
            print((f"Thank you for registering {self.user_name}"))

        option = self.user_options()
        if option == "Quit":
            print("Good bye!")
            sys.exit(0)
        elif option == "Edit Profile":
            edit_customer(self.user_id, self.user_name)
        elif option == "Make Reservation or Edit Reservations":
            edit_reservations(self.name_dict)


if __name__ == "__main__":
    Customer().main()
