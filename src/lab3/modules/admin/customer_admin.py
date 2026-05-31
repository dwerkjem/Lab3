"""
Name: Derek R. Neilson
"""

import re
from typing import Literal
from collections.abc import Callable

import questionary

from lab3.modules.crud.database import Database
from lab3.modules.crud.main import CRUD

db = Database()
crud = CRUD(db)


class AdminEditCustomer:
    """TUI used for editing an existing customer allows for three options excluding quit editing name, auto-approval, and deletion.
    This should never be accessible to a customer.
    """

    def __init__(self):
        self.customer = self._select_customer()

        if (
            self.customer is None
        ):  # If `customer` is None `customer_id` and `customer_name` must be None
            self.customer_id = None
            self.customer_name = None
            return  # Returns None, the constructor will stop early

        self.customer_id = self.customer["id"]
        self.customer_name = self.customer["value"]

    def main(self) -> None:
        """Shows the options and runs selected one."""
        if self.customer is None:
            return  # Prevents running actions when no customer was selected.

        choice = questionary.select(
            f"What would you like to do with {self.customer_name}?",
            [
                "Edit name",
                "Toggle auto-approval",
                "Delete customer",
                "Quit",
            ],
        ).ask()

        if choice == "Edit name":
            self.edit_name()
        elif choice == "Toggle auto-approval":
            self.toggle_auto_approval()
        elif choice == "Delete customer":
            self.delete_customer()

    def edit_name(self) -> None:
        """Select user name and edit it."""
        names_list = self._get_customer_names()

        new_customer_name = questionary.text(
            "What would you like to change the name to?",
            default=self.customer_name,
            validate=self._edit_validate_name(names_list, self.customer_name),
        ).ask()

        if new_customer_name is None:
            return  # prevents updating the database when the prompt is cancelled.

        db.cursor.execute(
            """
            UPDATE customers
            SET full_name = ?
            WHERE customer_id = ?
            """,
            (new_customer_name, self.customer_id),
        )
        db.commit()

    def toggle_auto_approval(self) -> None:
        """Toggle the selected customer's auto-approval setting on or off."""
        db.cursor.execute(
            """
            SELECT auto_approval
            FROM customers
            WHERE customer_id = ?
            """,
            (self.customer_id,),
        )

        current = db.cursor.fetchone()
        if current is None:
            print("Customer not found.")
            return  # Exit if the selected customer no longer exists.
        # Convert the current value to its opposite: 1 becomes 0, and 0 becomes 1.
        new_value = 0 if current[0] else 1

        db.cursor.execute(
            """
            UPDATE customers
            SET auto_approval = ?
            WHERE customer_id = ?
            """,
            (new_value, self.customer_id),
        )
        db.commit()

        # `new_value` is cast too bool as a int
        status = "enabled" if new_value else "disabled"
        print(f"Auto-approval {status} for {self.customer_name}.")

    def delete_customer(self) -> None:
        """Delete the selected customer and any reservations or services linked to them.
        Payments are not deleted for bill records."""
        confirmed = questionary.confirm(
            f"Delete {self.customer_name} and all associated reservations/services?",
            default=False,
        ).ask()

        if not confirmed:
            return  #! Do not delete anything if the admin cancels REQUIRED.

        # The linked services must be deleted first
        reservation_ids = [
            row[0]
            for row in db.fetchall(
                """
            SELECT reservation_id
            FROM reservations
            WHERE customer_id = ?
            """,
                (self.customer_id,),
            )
        ]

        # Dont let records be orphaned
        for reservation_id in reservation_ids:
            db.cursor.execute(
                """
                DELETE FROM reservation_services
                WHERE reservation_id = ?
                """,
                (reservation_id,),
            )

        # Reservations
        db.cursor.execute(
            """
            DELETE FROM reservations
            WHERE customer_id = ?
            """,
            (self.customer_id,),
        )

        # Finally delete user
        db.cursor.execute(
            """
            DELETE FROM customers
            WHERE customer_id = ?
            """,
            (self.customer_id,),
        )

        db.commit()

        print(f"{self.customer_name} was deleted.")

    def _get_customer_names(self) -> list[str]:
        """Return all customer full names, sorted alphabetically."""
        query = """
            SELECT full_name
            FROM customers
            ORDER BY full_name
            """
        return [row[0] for row in db.fetchall(query)]

    def _edit_validate_name(
        self, names_list: list[str], current_name: str = ""
    ) -> Callable[[str], str | Literal[True]]:
        """Return a validator function for customer names.

        Args:
            names_list (list[str]): list of existing names
            current_name (str, optional): Existing name allowed during edits. Defaults to "".

        Returns:
            Callable[[str], str | Literal[True]]: Validator function for customer full names.
        """

        def validate(full_name: str) -> str | Literal[True]:
            full_name = full_name.strip()
            words = full_name.split()

            if len(words) < 2:  # Names must be at least a first and last
                return "Name must have at least two words."

            if words[0].endswith("."):
                return "First name cannot end in a period."

            if not re.fullmatch(r"[A-Za-z.]+", full_name.replace(" ", "")):
                return "Name can only contain letters, spaces, and periods."

            for word in words:
                if not re.fullmatch(r"[A-Za-z.]+", word):
                    return f"'{word}' contains invalid characters."

            if full_name != current_name and full_name in names_list:
                return "That customer already exists."

            return True

        return validate

    def _select_customer(self) -> dict[str, int | str] | None:
        def _select_customer(self) -> dict[str, int | str] | None:
            """Prompt the admin to select a customer.

            Returns:
                dict[str, int | str] | None: Selected customer data, or None if no
                customers exist or the admin chooses Quit.
            """

        customers = db.fetchall("""
            SELECT customer_id, full_name
            FROM customers
            ORDER BY full_name
            """)

        if not customers:
            print("No customers found.")
            return None

        choices = [
            questionary.Choice(
                title=full_name, value={"id": customer_id, "value": full_name}
            )
            for customer_id, full_name in customers
        ]

        choices.append(questionary.Choice(title="Quit", value=None))

        return questionary.select(
            "Select customer to edit or delete",
            choices=choices,
        ).ask()
