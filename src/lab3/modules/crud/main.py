"""
Name: Derek R. Neilson
Description:Shared CRUD utilities and input validators for the TUI.
"""

from collections.abc import Callable
from decimal import Decimal
from typing import Literal

import questionary


class CRUD:
    """Shared CRUD helper methods and input validators for the TUI."""

    def __init__(self, db) -> None:
        """Store the database connection and cursor used by CRUD helpers."""
        self.db = db
        self.conn = db.conn
        self.cursor = db.cursor

    @staticmethod
    def dollar_validator(dollars: str) -> str | Literal[True]:
        """Validate a dollar amount entered by the user."""
        try:
            value = Decimal(dollars)
        except Exception:
            return "Only type numbers"

        if value < 0:
            return "Enter a positive amount"

        if abs(value.as_tuple().exponent) > 2:
            return "At most 2 decimal places"

        return True

    @staticmethod
    def integer_validator(integer_to_validate: str) -> str | Literal[True]:
        """Validate that user input is a whole number under one million."""
        try:
            value = int(integer_to_validate)
        except Exception:
            return "Only type whole numbers"
        if value > 1000000:
            return "Can not be above one million"
        return True

    @staticmethod
    def choose_autocomplete_or_text_prompt(
        autocomplete_prompt: str,
        validator: Callable,
        list_of_options: list[str] | None = None,
    ) -> str | None:
        """Prompt with autocomplete when options exist, otherwise use a text prompt."""
        if list_of_options:
            return questionary.autocomplete(
                autocomplete_prompt,
                choices=list_of_options,
                validate=validator,
            ).ask()

        return questionary.text(
            autocomplete_prompt,
            validate=validator,
        ).ask()

    def make_or_select_existing_autocomplete(
        self,
        id_col: str,
        row_col: str,
        table: str,
        autocomplete_prompt: str,
        validator: Callable,
    ) -> dict[str, str | bool | int] | None:
        """Prompts the user for a value using autocomplete. If the value already
        exists in the specified table, it is selected; otherwise, it is inserted.

        Returns a dictionary containing the selected value, whether it already
        existed.

        Args:
            id_col (str): Name of the ID column in the table.
            row_col (str): Name of the column being searched and inserted into.
            table (str): Name of the table to search.
            autocomplete_prompt (str): Prompt displayed to the user.
            validator (Callable): Validation function that accepts a single
                argument and returns True if valid or an error message if invalid.


        Returns:
            dict[str, str | bool | int] | None:
                A dictionary containing:
                    - "value": The selected or inserted value.
                    - "existed": Whether the value already existed.
                    - "id": The row ID .
                Returns None if the prompt is cancelled.
        """

        rows = self.db.fetchall(f"SELECT {id_col}, {row_col} FROM {table}")
        # Map displayed values to their database IDs.
        dictionary_val_id = {value: row_id for row_id, value in rows}
        list_of_options = list(dictionary_val_id.keys())

        selected_row_col = CRUD.choose_autocomplete_or_text_prompt(
            autocomplete_prompt, validator, list_of_options
        )

        # Existing values are selected; new values are inserted.
        if selected_row_col in dictionary_val_id:
            return {
                "value": selected_row_col,
                "existed": True,
                "id": dictionary_val_id[selected_row_col],
            }
        elif selected_row_col is not None:
            self.cursor.execute(
                f"INSERT INTO {table} ({row_col}) VALUES (?)",
                (selected_row_col,),
            )
            self.db.commit()
            print(f"{selected_row_col} has been created!")

            return {
                "value": selected_row_col,
                "existed": False,
                "id": self.cursor.lastrowid,
            }
        else:
            print("None was queried.")
            return None
