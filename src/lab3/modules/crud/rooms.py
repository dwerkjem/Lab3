from decimal import Decimal

import questionary

from lab3.modules.crud.database import Database
from lab3.modules.crud.main import CRUD

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
    room_list = db.fetchall("SELECT room_id, name FROM rooms")
    room_names = [name for _, name in room_list]
    room_name: str = crud.choose_autocomplete_or_text_prompt(
        "What room do you want to edit/create?", _rooms_validator, room_names
    )

    if room_name is None:
        return None

    if room_name in room_names:
        room = get_room_by_name(room_name)
        room_id = room["id"]
        old_day_rate_cents = room["day_rate_cents"]
        old_capacity = room["capacity"]
        old_name = room["name"]
        old_day_rate = str(Decimal(old_day_rate_cents) / 100)
        new_name = questionary.text(
            f"What is the new name for {room_name} leave unchanged to keep as is?",
            default=room_name,
            validate=_edit_room_validator(room_names, room_name),
        ).ask()

        new_capacity = questionary.text(
            f"What is the capacity of {room_name} leave unchanged to keep as is?",
            default=str(old_capacity),
            validate=crud.integer_validator,
        ).ask()

        new_day_rate = questionary.text(
            f"What is the rate of {room_name} leave unchanged to keep as is?",
            default=str(old_day_rate),
            validate=crud.dollar_validator,
        ).ask()

        new_day_rate_cents = int((Decimal(new_day_rate) * 100).quantize(Decimal("1")))
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
        print(
            f"{old_name} updated to {new_name} with a capacity of {new_capacity} and a daily rate of {new_day_rate}"
        )
        db.conn.commit()
    else:
        capacity = questionary.text(
            f"What is the capacity of {room_name}?", validate=crud.integer_validator
        ).ask()
        day_rate = questionary.text(
            f"What is the rate of {room_name}?", "139.99", crud.dollar_validator
        ).ask()

        day_rate_cents = int(Decimal(day_rate) * 100)
        db.cursor.execute(
            """
            INSERT INTO rooms (name, capacity, day_rate_cents)
            VALUES (?, ?, ?)
            """,
            (
                room_name,
                capacity,
                day_rate_cents,
            ),
        )
        print(
            f"Room made {room_name} with capacity of {capacity} and a daily rate of {day_rate}"
        )
        db.commit()


def get_room_by_name(room_name: str) -> dict[str, str | int] | None:
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
    room_id, name, capacity, day_rate_cents = row
    return {
        "id": room_id,
        "name": name,
        "capacity": capacity,
        "day_rate_cents": day_rate_cents,
    }
