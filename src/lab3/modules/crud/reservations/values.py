import questionary

from lab3.modules.crud.database import Database
from lab3.modules.crud.reservations.validators import validate_datetime

db = Database()


def set_notes(default=""):
    return questionary.text(
        "Do you want to add any notes?",
        default=default,
        multiline=True,
    ).ask()


def _get_room(room_names, user_name, default=None):
    room_name = questionary.select(
        f"{user_name}, which room would you like to reserve?",
        room_names,
        default=default,
    ).ask()

    if room_name in (None, "Quit"):
        return None

    db.cursor.execute(
        """
        SELECT room_id
        FROM rooms
        WHERE name = ?
        """,
        (room_name,),
    )

    room = db.cursor.fetchone()
    return {"id": room[0], "name": room_name}


def set_event_type(default="Other"):
    return questionary.select(
        "What type of event is this?",
        ["Wedding", "Meeting", "Party", "Conference", "Other", "Quit"],
        default=default,
    ).ask()


def set_date(room_id, default=""):
    instruction_text = """Use format `start-date end-date`, where both dates are in `YYYY-MM-DD`
format and separated by a space.
Example: `2026-05-01 2026-05-29`
Or enter one date for a single day."""

    return questionary.text(
        "What day would the event start",
        default=default,
        validate=validate_datetime(room_id),
        instruction=instruction_text,
    ).ask()


def set_event_name(default=""):
    return questionary.text(
        "What is your event called",
        default=default,
    ).ask()


def get_attendees_count(integer_validator, default="30") -> str | None:
    return questionary.text(
        "How many people will be attending?",
        default=default,
        validate=integer_validator,
    ).ask()
