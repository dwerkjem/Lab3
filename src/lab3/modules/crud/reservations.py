import questionary
from lab3.modules.crud.database import Database
from lab3.modules.crud.rooms import get_room_by_name
from lab3.modules.crud.main import CRUD
import datetime
import sys

db = Database()

crud = CRUD(db)


def edit_reservations(name_dict: dict):
    db.cursor.execute(f"SELECT room_id, name FROM rooms")
    room_list = db.cursor.fetchall()
    room_names = ["Quit"] + [name for _, name in room_list]

    user_id = name_dict["id"]
    user_name = name_dict["value"]

    db.cursor.execute(f"SELECT {user_id}, event_name FROM reservations")
    reservation_list = db.cursor.fetchall()
    reservation_names = [name for _, name in reservation_list]

    if reservation_list == []:
        # make new reservation
        if room_names != []:
            _post_room_setup(room_names, user_name)


def _post_room_setup(room_names, user_name):
    event_name = _set_event_name()
    if event_name is None:
        sys.exit(0)
    room = _get_room(room_names, user_name)
    room_id = room["id"]
    if room_id is None:
        sys.exit(0)
    date_string = _set_date(room_id)
    if date_string is None:
        sys.exit(0)
    attendees_count = _get_attendees_count()
    if attendees_count is None:
        sys.exit(0)
    notes = _set_notes()


def _is_reserved_date_in_range(room_id: str, start_date: str, end_date: str):
    db.cursor.execute(
        """
        SELECT start_datetime, end_datetime
        FROM reservations
        WHERE room_id = ?
          AND status = 'approved'
          AND start_datetime <= ?
          AND end_datetime >= ?
    """,
        (int(room_id), end_date, start_date),
    )  # This woks only because it is YYYY-MM-DD and
    # therefore there in the right order and can be compared like this.

    reserved_dates = db.cursor.fetchall()

    if not reserved_dates:
        return False

    return reserved_dates


def validate_datetime(room_id):
    def validator(dates: str):
        parts = dates.split()
        today = datetime.date.today()

        if len(parts) > 2:
            return "Use only 2 dates"

        parsed_dates = []

        for date in parts:
            try:
                parsed_date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
                parsed_dates.append(parsed_date)
            except ValueError:
                return f"{date} is invalid, use this format `YYYY-MM-DD`."

            if parsed_date < today:
                return f"{date} is in the past. Please enter today or a future date."

        if len(parsed_dates) == 2:
            start, end = parsed_dates

            if start > end:
                return f"The start date {parts[0]} must be before {parts[1]}"

            if (end - start).days > 30:
                return "Reservations cannot be longer than 30 days without special approval."

            reserved_dates = _is_reserved_date_in_range(room_id, parts[0], parts[1])
            if reserved_dates:
                return f"That room is already reserved during: {reserved_dates}"

        return True

    return validator


def _get_room(room_names: list[str], user_name: str) -> dict[str, str | int] | None:
    room_name = questionary.select(
        f"Hello {user_name} please select a room for your first reservation", room_names
    ).ask()
    return get_room_by_name(room_name)


def _get_attendees_count() -> str:
    attendees_count = questionary.text(
        "How many people will be attending?", "30", crud.integer_validator
    ).ask()
    return attendees_count


def _set_event_name():
    event_name = questionary.text("What is your event called").ask()
    return event_name


def _set_date(room_id) -> str | None:
    instruction_text = """Use format `start-date end-date`, where both dates are in `YYYY-MM-DD` format and separated by a space.
Example: `2026-05-01 2026-05-29`
Or enter one date for a single day."""
    date = questionary.text(
        "What day would the event start",
        validate=validate_datetime(room_id),
        instruction=instruction_text,
    ).ask()
    return date


def _set_notes():
    date = questionary.text("Do you want to add any note?")
