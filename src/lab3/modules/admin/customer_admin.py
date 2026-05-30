import re

import questionary

from lab3.modules.crud.database import Database
from lab3.modules.crud.main import CRUD

db = Database()
crud = CRUD(db)


class AdminEditCustomer:
    def __init__(self):
        self.customer = self._select_customer()

        if self.customer is None:
            self.customer_id = None
            self.customer_name = None
            return

        self.customer_id = self.customer["id"]
        self.customer_name = self.customer["value"]

    def main(self):
        if self.customer is None:
            return

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

    def _select_customer(self):
        names_list = self._get_customer_names()

        return crud.make_or_select_existing_autocomplete(
            "customer_id",
            "full_name",
            "customers",
            "Select customer to edit or delete",
            self._edit_validate_name(names_list),
        )

    def edit_name(self):
        names_list = self._get_customer_names()

        new_customer_name = questionary.text(
            "What would you like to change the name to?",
            default=self.customer_name,
            validate=self._edit_validate_name(names_list, self.customer_name),
        ).ask()

        if new_customer_name is None:
            return

        db.cursor.execute(
            """
            UPDATE customers
            SET full_name = ?
            WHERE customer_id = ?
            """,
            (new_customer_name, self.customer_id),
        )
        db.commit()

    def toggle_auto_approval(self):
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
            return

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

        status = "enabled" if new_value else "disabled"
        print(f"Auto-approval {status} for {self.customer_name}.")

    def delete_customer(self):
        confirmed = questionary.confirm(
            f"Delete {self.customer_name} and all associated reservations/services?",
            default=False,
        ).ask()

        if not confirmed:
            return

        db.cursor.execute(
            """
            SELECT reservation_id
            FROM reservations
            WHERE customer_id = ?
            """,
            (self.customer_id,),
        )
        reservation_ids = [row[0] for row in db.cursor.fetchall()]

        for reservation_id in reservation_ids:
            db.cursor.execute(
                """
                DELETE FROM reservation_services
                WHERE reservation_id = ?
                """,
                (reservation_id,),
            )

        db.cursor.execute(
            """
            DELETE FROM reservations
            WHERE customer_id = ?
            """,
            (self.customer_id,),
        )

        db.cursor.execute(
            """
            DELETE FROM customers
            WHERE customer_id = ?
            """,
            (self.customer_id,),
        )

        db.commit()

        print(f"{self.customer_name} was deleted.")

    def _get_customer_names(self):
        db.cursor.execute("""
            SELECT full_name
            FROM customers
            WHERE is_deleted = 0
            ORDER BY full_name
            """)
        return [row[0] for row in db.cursor.fetchall()]

    def _edit_validate_name(self, names_list: list[str], current_name: str = ""):
        def validate(full_name: str):
            full_name = full_name.strip()
            words = full_name.split()

            if len(words) < 2:
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

    def _select_customer(self):
        db.cursor.execute("""
            SELECT customer_id, full_name
            FROM customers
            WHERE is_deleted = 0
            ORDER BY full_name
            """)

        customers = db.cursor.fetchall()

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
