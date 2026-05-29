import questionary
import sqlite3
from collections.abc import Callable
from decimal import Decimal


class CRUD:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

    @staticmethod
    def dollar_validator(dollars: str):
        try:
            value = Decimal(dollars)
        except Exception:
            return "Only type numbers"

        if value < 0:
            return "Enter a positive amount"

        if abs(value.as_tuple().exponent) > 2:
            return "At most 2 decimal places"

        return True

    def _rooms_validator(room_name: str):
        if room_name != room_name.title():
            return "Please make title case."
        return True

    def edit_rooms(self):
        ID_FIELD = "room_id"
        NAME_FIELD = "name"
        TABLE_FIELD = "rooms"
        self.cursor.execute(f"SELECT {ID_FIELD}, {NAME_FIELD} FROM {TABLE_FIELD}")
        room_list = self.cursor.fetchall()
        room_name = self.chose_autocomplete_or_text_prompt(
            "What room do you want to edit/create?", CRUD._rooms_validator, room_list
        )

        if room_name is None:
            return None

        room_name = room_name
        capacity = questionary.text(f"What is the capacity of {room_name}?").ask()
        day_rate = questionary.text(
            f"What is the rate of {room_name}?", "139.99", CRUD.dollar_validator
        ).ask()

        day_rate_cents = int(Decimal(day_rate) * 100)
        self.cursor.execute(
            f"""
            UPDATE {TABLE_FIELD}
            SET capacity = ?, day_rate_cents = ?
            WHERE {ID_FIELD} = ?
            """,
            (
                capacity,
                day_rate_cents,
            ),
        )

        self.conn.commit()

    @staticmethod
    def chose_autocomplete_or_text_prompt(
        autocomplete_prompt: str,
        validator: Callable,
        list_of_options: list[str] | None = None,
    ):
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
    ) -> dict[str, str | bool] | None:
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
            instant_push (bool): Whether to immediately commit inserts to the
                database.

        Returns:
            dict[str, str | bool | int] | None:
                A dictionary containing:
                    - "value": The selected or inserted value.
                    - "existed": Whether the value already existed.
                    - "id": The row ID .
                Returns None if the prompt is cancelled.
        """

        query = f"SELECT {id_col}, {row_col} FROM {table}"
        self.cursor.execute(query)

        rows = self.cursor.fetchall()

        dictionary_val_id = {value: row_id for row_id, value in rows}
        list_of_options = list(dictionary_val_id.keys())

        selected_row_col = CRUD.chose_autocomplete_or_text_prompt(
            autocomplete_prompt, validator, list_of_options
        )

        if selected_row_col in dictionary_val_id:
            # if it is in the data base
            return {
                "value": selected_row_col,
                "existed": True,
                "id": dictionary_val_id[selected_row_col],
            }
        elif selected_row_col is not None:
            # if it is not in the data base
            self.cursor.execute(
                f"INSERT INTO {table} ({row_col}) VALUES (?)",
                (selected_row_col,),
            )
            self.conn.commit()
            print(f"{selected_row_col}has been created!")

            return {
                "value": selected_row_col,
                "existed": False,
                "id": self.cursor.lastrowid,
            }
        else:
            print("None was queried.")
