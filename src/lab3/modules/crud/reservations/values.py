import questionary

from lab3.modules.crud.reservations.validators import validate_datetime
from lab3.modules.crud.rooms import get_room_by_name


def _get_room(room_names: list[str], user_name: str) -> dict[str, str | int] | None:
    room_name = questionary.select(
        f"Hello {user_name} please select a room", room_names
    ).ask()

    if room_name == "Quit" or room_name is None:
        return None

    return get_room_by_name(room_name)


def set_notes():
    note = questionary.text("Do you want to add any notes?", multiline=True).ask()
    return note


def set_date(room_id) -> str | None:
    instruction_text = """Use format `start-date end-date`, where both dates are in `YYYY-MM-DD`
format and separated by a space.
Example: `2026-05-01 2026-05-29`
Or enter one date for a single day."""
    date = questionary.text(
        "What day would the event start",
        validate=validate_datetime(room_id),
        instruction=instruction_text,
    ).ask()
    return date


def set_event_name():
    event_name = questionary.text("What is your event called").ask()
    return event_name


def get_attendees_count(integer_validator) -> str:
    attendees_count = questionary.text(
        "How many people will be attending?", "30", integer_validator
    ).ask()
    return attendees_count
