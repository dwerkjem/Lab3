import sys
import questionary
import sqlite3


class Customer:

    def __init__(self, cursor, conn):
        """sets up `Customer`

        Args:
            cursor (_type_): the sql cursor
            conn (_type_): the sql connection
        """
        self.cursor = cursor
        self.conn = conn

    def validate_full_name(self, name):
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
        self.cursor.execute("SELECT customer_id, full_name FROM customers")
        customers = self.cursor.fetchall()

        customer_lookup = {
            full_name: customer_id for customer_id, full_name in customers
        }
        customer_lookup["Quit"] = 0
        list_of_options = list(customer_lookup.keys())

        selected_name = questionary.autocomplete(
            "What is your full name?",
            choices=list_of_options,
            validate=self.validate_full_name,
        ).ask()
        selected_name = str(selected_name)  # unnecessary but helps with type hinting

        selected_name = selected_name.strip().title()

        if selected_name == "Quit":
            sys.exit(0)

        if selected_name in customer_lookup:
            print(f"Welcome back {selected_name}, your business is appreciated!")
            return customer_lookup[selected_name]

        if selected_name is not None:
            self.cursor.execute(
                "INSERT INTO customers (full_name) VALUES (?)", (selected_name,)
            )
            self.conn.commit()
            print(f"Welcome {selected_name}, your account has been created!")

            return self.cursor.lastrowid
        else:
            sys.exit(1)
