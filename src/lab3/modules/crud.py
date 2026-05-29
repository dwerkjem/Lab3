import questionary
import sqlite3
from collections.abc import Callable


class CRUD:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

    def create_room(self, room_name: str, capacity: int, day_rate_cents: int):
        print(self.db_path)

    def make_or_select_existing_autocomplete(
        self,
        id_col: str,
        row_col: str,
        table: str,
        autocomplete_prompt: str,
        validator: Callable,
    ) -> dict[str, int | bool] | None:

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
