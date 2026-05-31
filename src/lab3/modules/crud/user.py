"""
Name: Derek R. Neilson
Description: Customer name validation and customer record editing helpers.
"""

import re
from typing import Callable, Literal

import questionary

from .database import Database

db = Database()


def edit_validate_name(
    names_list: list[str], current_name: str
) -> Callable[[str], str | Literal[True]]:
    """Return a validator for edited customer names.

    Allows the current customer name but rejects duplicate names.
    """

    def validate(full_name: str) -> str | Literal[True]:
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


def edit_customer(customer_id: str, customer_name: str) -> None:
    """Prompt for a new customer name and update the customer record."""

    # Existing names are used to prevent duplicate customer names.
    names_list = [
        row[0]
        for row in db.fetchall("""
        SELECT full_name
        FROM customers
        ORDER BY full_name
    """)
    ]

    new_customer_name = questionary.text(
        "What would you like to change the name to?",
        default=customer_name,
        validate=edit_validate_name(names_list, customer_name),
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

    if new_customer_name is None:
        return  # Exit if the prompt is cancelled.

    db.commit()
