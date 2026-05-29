import sys
import questionary
from lab3.modules.crud.crud import CRUD
from lab3.modules.crud.database import Database
from lab3.modules.crud.user_crud import edit_customer

db = Database()

crud = CRUD(db)

class Customer:

    def __init__(self):
        """sets up `Customer`"""
        name_dict = self.auth()
        self.user_name = name_dict["value"]
        self.user_id = name_dict["id"]
        self.user_existed = name_dict["existed"]


    @staticmethod  # use this decorator to make independent of class https://www.geeksforgeeks.org/python/python-staticmethod/
    def validate_full_name(name: str):
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
        return crud.make_or_select_existing_autocomplete(
            "customer_id",
            "full_name",
            "customers",
            "What is your full name?",
            self.validate_full_name,
        )
    @staticmethod
    def user_option():
        return questionary.select(
            "What would you like to do?",
            [
                "Make Reservation or Edit Reservations",
                "Edit Profile",
                "Quit"
            ]
        ).ask()
    def main(self):
        if self.user_existed:
            print(f"Welcome back {self.user_name}")
        else:
            print((f"Thank you for registering {self.user_name}"))
        
        option = self.user_option()
        if option == "Quit":
            print("Good bye!")
            sys.exit(0)
        elif option == "Edit Profile":
            edit_customer(self.user_id, self.user_name)
            

if __name__ == "__main__":
    Customer().main()
