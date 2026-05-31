import sys

import questionary

from lab3.modules.admin.customer_admin import AdminEditCustomer
from lab3.modules.crud import rooms
from lab3.modules.crud.reservations.optional_services import (
    edit_add_service,
)
from lab3.modules.admin.reservations_admin import chose_reservations

UNSECURE_PASSWORD = "pas"


def main() -> None:
    if not auth():
        sys.exit(0)

    option = admin_options()

    if option == "Customers":
        AdminEditCustomer().main()
    elif option == "Rooms":
        rooms.edit_rooms()
    elif option == "Services":
        edit_add_service()
    elif option == "Reservations":
        chose_reservations()

    else:
        print("Bye admin! Come back soon!")
        sys.exit(0)


def auth() -> bool:
    password = questionary.password(
        f"Verify with a password\n"
        f"  The password is `{UNSECURE_PASSWORD}` for demo purposes"
    ).ask()

    if password == UNSECURE_PASSWORD:
        questionary.print("Welcome Admin", style="bold fg:ansigreen")
        return True

    questionary.print("You are unauthorized", style="bold fg:ansired")
    return False


def admin_options():
    return questionary.select(
        "What do you want to change?",
        ["Rooms", "Customers", "Reservations", "Services", "Quit"],
    ).ask()
