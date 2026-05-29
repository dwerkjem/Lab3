from decimal import Decimal
import questionary


from .crud import CRUD
from lab3.modules.crud.database import Database


db = Database()
crud = CRUD(db)

def _rooms_validator(room_name: str):
    if room_name != room_name.title():
        return "Please make title case."
    return True

def _edit_room_validator(existing_room_names: list[str], current_name: str):
    def validator(room_name: str):
        if room_name != room_name.title():
            return "Please make title case."

        if room_name != current_name and room_name in existing_room_names:
            return "That room already exists."

        return True

    return validator

def edit_rooms():
    ID_FIELD = "room_id"
    NAME_FIELD = "name"
    TABLE_FIELD = "rooms"
    db.cursor.execute(f"SELECT {ID_FIELD}, {NAME_FIELD} FROM {TABLE_FIELD}")
    room_list = db.cursor.fetchall()
    room_names = [name for _, name in room_list]
    room_name: str = crud.chose_autocomplete_or_text_prompt(
        "What room do you want to edit/create?", _rooms_validator, room_names
    )

    if room_name is None:
        return None

    if room_name in room_names:
        db.cursor.execute(
            """
            SELECT room_id, name, capacity, day_rate_cents
            FROM rooms
            WHERE name = ?
            """,
            (room_name,),
        )

        row = db.cursor.fetchone()

        if row is None:
            return None

        room_id, old_name, old_capacity, old_day_rate_cents = row
        old_day_rate = str(Decimal(old_day_rate_cents) / 100)
        new_name = questionary.text(
            f"What is the new name for {room_name} leave unchanged to keep as is?",
            room_name,
            _edit_room_validator(room_names, room_name),
        ).ask()

        new_capacity = questionary.text(
            f"What is the capacity of {room_name} leave unchanged to keep as is?",
            str(old_capacity),
            crud.integer_validator,
        ).ask()

        new_day_rate_cents = questionary.text(
            f"What is the rate of {room_name}leave unchanged to keep as is?",
            str(old_day_rate),
            crud.dollar_validator,
        ).ask()
        new_day_rate_cents = int(Decimal(new_day_rate_cents) * 100)
        db.cursor.execute(
            """
            UPDATE rooms
            SET name = ?,
                capacity = ?,
                day_rate_cents = ?
            WHERE room_id = ?
            """,
            (
                new_name,
                new_capacity,
                new_day_rate_cents,
                room_id,
            ),
        )

        db.conn.commit()
    else:
        capacity = questionary.text(f"What is the capacity of {room_name}?").ask()
        day_rate = questionary.text(
            f"What is the rate of {room_name}?", "139.99", crud.dollar_validator
        ).ask()

        day_rate_cents = int(Decimal(day_rate) * 100)
        db.cursor.execute(
            f"""
            INSERT INTO {TABLE_FIELD} (name, capacity, day_rate_cents)
            VALUES (?, ?, ?)
            """,
            (
                room_name,
                capacity,
                day_rate_cents,
            ),
        )

        db.commit()