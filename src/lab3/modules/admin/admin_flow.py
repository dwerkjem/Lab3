"""
Name: Derek R. Neilson
Description: All admin options are accessed here.
"""

import sys
import time

import questionary

from lab3.modules.admin.customer_admin import AdminEditCustomer
from lab3.modules.crud import rooms
from lab3.modules.crud.reservations.optional_services import edit_add_service
from lab3.modules.admin.reservations_admin import choose_reservations

DEMO_PASSWORD = "pas"  # TODO #1 move DEMO_PASSWORD to env file


def main() -> None:
    """Authenticated admin will pick an option and it will take them to the respective module."""
    if not auth():
        time.sleep(0.5)
        return

    option = admin_options()

    if option == "Customers":
        AdminEditCustomer().main()
    elif option == "Rooms":
        rooms.edit_rooms()
    elif option == "Services":
        edit_add_service()
    elif option == "Reservations":
        choose_reservations()
    else:
        print("Bye admin! Come back soon!")
        sys.exit(0)


def auth() -> bool | None:
    """Authenticates admin in production use crypto library instead.

    Returns:
        bool | None: Whether the user successfully logged in as an admin or not.
        This will return `None` if cancelled.
    """
    password = questionary.password(
        f"Verify with a password\n  The password is `{DEMO_PASSWORD}` for demo purposes"
    ).ask()

    if password == DEMO_PASSWORD:
        questionary.print("Welcome Admin", style="bold fg:ansigreen")
        return True

    questionary.print("You are unauthorized", style="bold fg:ansired")
    return False


def admin_options() -> str | None:
    """Returns choosen option.

    Returns:
        str | None: Option choosen.
    """
    return questionary.select(
        "What do you want to change?",
        ["Rooms", "Customers", "Reservations", "Services", "Quit"],
    ).ask()
