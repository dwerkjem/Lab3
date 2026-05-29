import questionary
from .database import Database
import re

db = Database()

def _edit_validate_name(names_list: list[str], current_name: str):
    def validate(full_name: str):
        full_name = full_name.strip()
        words = full_name.split()

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

        if full_name != current_name and full_name in names_list:
            return "That customer already exists."

        return True

    return validate

def edit_customer(customer_id: str, customer_name: str):
    db.cursor.execute("""
        SELECT full_name
        FROM customers
        ORDER BY full_name
    """)

    names_list = [row[0] for row in db.cursor.fetchall()]

    new_customer_name = questionary.text(
        "What would you like to change the name to?",
        default=customer_name,
        validate=_edit_validate_name(names_list, customer_name)
    ).ask()

    db.cursor.execute(
        """
        UPDATE customers
        SET full_name = ?
        WHERE customer_id = ?
        """,
        (
            new_customer_name,
            customer_id,
        ),
    )

    db.commit()