"""
Name: Derek R. Neilson
Description: Reservation input helpers.
"""

import questionary

from lab3.modules.crud.database import Database
from lab3.modules.crud.reservations.validators import validate_datetime

db = Database()


def set_notes(default: str = "") -> str | None:
    """Prompt the user to enter optional reservation notes."""
    return questionary.text(
        "Do you want to add any notes?",
        default=default,
        multiline=True,
    ).ask()


def get_room(
    user_name: str,
    default: str | None = None,
) -> dict[str, int | str] | None:
    """Prompt the user to select a room.

    Args:
        user_name (str): Customer name shown in the prompt.
        default (str | None, optional): Room name to select by default.

    Returns:
        dict[str, int | str] | None: Selected room data, or None if the user quits.
    """
    db.cursor.execute(
        """
        SELECT room_id, name, day_rate_cents
        FROM rooms
        """
    )

    rows = db.cursor.fetchall()

    display_to_room = {"Quit": None}

    for room_id, name, day_rate_cents in rows:
        display_name = f"{name} - ${day_rate_cents / 100:.2f}"
        display_to_room[display_name] = {
            "id": room_id,
            "name": name,
        }

    default_display = None

    if default is not None:
        for display_name, room in display_to_room.items():
            if room is not None and room["name"] == default:
                default_display = display_name
                break

    selected_display = questionary.select(
        f"{user_name}, which room would you like to reserve?",
        list(display_to_room.keys()),
        default=default_display,
    ).ask()

    room = display_to_room.get(selected_display)

    if room is None:
        return None

    return room


def set_event_type(default: str = "Other") -> str | None:
    """Prompt the user to choose an event type."""
    return questionary.select(
        "What type of event is this?",
        ["Wedding", "Meeting", "Party", "Conference", "Other", "Quit"],
        default=default,
    ).ask()


def set_date(room_id: int, default: str = "") -> str | None:
    """Prompt the user for reservation dates and validate room availability."""
    instruction_text = """Use format `start-date end-date`, where both dates are in `YY-MM-DD`
format and separated by a space.
Example: `26-05-01 26-05-29`
Or enter one date for a single day."""

    return questionary.text(
        "What day would the event start",
        default=default,
        validate=validate_datetime(room_id),
        instruction=instruction_text,
    ).ask()


def set_event_name(default: str = "") -> str | None:
    """Prompt the user to enter the reservation event name."""
    return questionary.text(
        "What is your event called",
        default=default,
    ).ask()


def get_attendees_count(integer_validator, default: str = "30") -> str | None:
    """Prompt the user to enter the number of attendees."""
    return questionary.text(
        "How many people will be attending?",
        default=default,
        validate=integer_validator,
    ).ask()


def room_name_from_id(room_id: int) -> str | None:
    """Return a room name from its room ID, or None if not found."""
    db.cursor.execute(
        "SELECT name FROM rooms WHERE room_id = ?",
        (room_id,),
    )
    room = db.cursor.fetchone()
    return room[0] if room else None
