import questionary
import sqlite3
from collections.abc import Callable

from typing import Any


class CRUD:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

    def create_room(self, room_name: str, capacity: int, day_rate_cents: int):
        CRUD.make_or_select_existing_autocomplete(
            self,
        )

    def make_or_select_existing_autocomplete(
        self,
        id_col: str,
        row_col: str,
        table: str,
        autocomplete_prompt: str,
        validator: Callable,
    ) -> dict[str, str | bool] | None:
        """Asks for a input and autocompletes based on whether it exists if it dose it selects it and returns a dictionary with its name and whether it existed or not in `"value"` and `"existed"` respectively

        Args:
            id_col (str): What the id is called in the data base
            row_col (str): What value are you searching for.
            table (str): In what table are you searching.
            # autocomplete_prompt (str): What should the prompt be.
            validator (Callable): A Validator function that must take 1 positional argument that is to be validated and return a str if invalid and a bool of True if valid.

        Returns:
            dict[str, Any | bool] | None: A dictionary with `"value"` as the inserted/selected value and a boolean value of whether it existed or not. it can also return `None` if invalid.
        """

        query = f"SELECT {id_col}, {row_col} FROM {table}"
        self.cursor.execute(query)

        rows = self.cursor.fetchall()

        dictionary_val_id = {value: row_id for row_id, value in rows}
        list_of_options = list(dictionary_val_id.keys())

        selected_row_col = questionary.autocomplete(
            autocomplete_prompt,
            choices=list_of_options,
            validate=validator,
        ).ask()

        if selected_row_col in dictionary_val_id:
            # if it is in the data base
            return {"value": selected_row_col, "existed": True}
        elif selected_row_col is not None:
            # if it is not in the data base
            self.cursor.execute(
                f"INSERT INTO {table} ({row_col}) VALUES (?)",
                (selected_row_col,),
            )
            self.conn.commit()
            print(f"{selected_row_col}has been created!")

            return {"value": selected_row_col, "existed": False}
        else:
            print("None was queried.")
