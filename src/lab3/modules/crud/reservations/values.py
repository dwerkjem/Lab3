import questionary

from lab3.modules.crud.reservations.validators import validate_datetime


def set_notes():
    note = questionary.text("Do you want to add any notes?", multiline=True).ask()
    return note


def set_event_type():
    return questionary.select(
        "What type of event is this?",
        ["Wedding", "Meeting", "Party", "Conference", "Other", "Quit"],
    ).ask()


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
