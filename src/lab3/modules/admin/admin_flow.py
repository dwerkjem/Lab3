import sys

import questionary

from lab3.modules.crud import rooms
from lab3.modules.crud.database import Database
from lab3.modules.crud.main import CRUD

db = Database()

crud = CRUD(db)


class Admin:
    @staticmethod
    def main() -> None:
        authorized = Admin.auth()
        if authorized:
            option = Admin.admin_options()
        else:
            sys.exit(0)

        if option == "Quit":
            print("Bye admin! Come back soon!")
            sys.exit(0)
        elif option == "Rooms":
            rooms.edit_rooms()

    @staticmethod
    def auth() -> bool:
        """Authenticates the admin

        Returns:
            bool: whether they are authorized or not.
        """
        password = questionary.password(
            "Verify with a password\n  The password is `Password123` for demo purposes"
        ).ask()
        if (
            password == "Password123"
        ):  # in production this would be encrypted and read from a .env file
            questionary.print("Welcome Admin", style="bold fg:ansigreen")
            return True
        else:
            questionary.print("You are unauthorized", style="bold fg:ansired")
            return False

    @staticmethod
    def admin_options():
        return questionary.select(
            "What you want to change?",
            ["Rooms", "Customers", "Reservations", "Services", "Quit"],
        ).ask()
