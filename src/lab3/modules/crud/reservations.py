import questionary
from lab3.modules.crud.database import Database
from lab3.modules.crud.rooms import get_room_by_name
from lab3.modules.crud.main import CRUD
import datetime
import sys

db = Database()

crud = CRUD(db)


def edit_reservations(name_dict: dict):
    db.cursor.execute("SELECT room_id, name FROM rooms")
    room_list = db.cursor.fetchall()
    room_names = ["Quit"] + [name for _, name in room_list]

    customer_id = name_dict["id"]
    user_name = name_dict["value"]

    db.cursor.execute(
        """
        SELECT reservation_id, event_name
        FROM reservations
        WHERE customer_id = ?
    """,
        (customer_id,),
    )
    reservation_list = db.cursor.fetchall()

    if not room_list:
        print("No rooms are created. Contact admin!")
        return

    if not reservation_list:
        _setup(customer_id, room_names, user_name)
        return

    choice = questionary.select(
        "What would you like to do?",
        ["Make a new reservation", "Edit an existing reservation", "Quit"],
    ).ask()

    if choice == "Make a new reservation":
        _setup(customer_id, room_names, user_name)

    elif choice == "Edit an existing reservation":
        _edit_existing_reservation(reservation_list, room_names, user_name)

    else:
        return


def _setup(customer_id, room_names, user_name):
    event_name = _set_event_name()
    if event_name is None:
        sys.exit(0)

    room = _get_room(room_names, user_name)
    if room is None:
        sys.exit(0)

    room_id = room["id"]

    date_string = _set_date(room_id)
    if date_string is None:
        sys.exit(0)

    attendees_count = _get_attendees_count()
    if attendees_count is None:
        sys.exit(0)

    notes = _set_notes()

    parts = date_string.split()

    if len(parts) == 1:
        start_datetime = parts[0]
        end_datetime = parts[0]
    else:
        start_datetime = parts[0]
        end_datetime = parts[1]

    db.cursor.execute(
        """
        INSERT INTO reservations (
            customer_id,
            room_id,
            attendees,
            event_name,
            start_datetime,
            end_datetime,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (
            customer_id,
            room_id,
            int(attendees_count),
            event_name,
            start_datetime,
            end_datetime,
            notes,
        ),
    )

    db.conn.commit()


def _edit_existing_reservation(reservation_list, room_names, user_name):
    reservation_options = {
        event_name: reservation_id for reservation_id, event_name in reservation_list
    }

    selected_event = questionary.select(
        "Which reservation do you want to edit?",
        ["Quit"] + list(reservation_options.keys()),
    ).ask()

    if selected_event == "Quit" or selected_event is None:
        return

    reservation_id = reservation_options[selected_event]

    event_name = _set_event_name()
    if event_name is None:
        return

    room = _get_room(room_names, user_name)
    if room is None:
        return

    room_id = room["id"]

    date_string = _set_date(room_id)
    if date_string is None:
        return

    attendees_count = _get_attendees_count()
    if attendees_count is None:
        return

    notes = _set_notes()

    parts = date_string.split()

    if len(parts) == 1:
        start_datetime = parts[0]
        end_datetime = parts[0]
    else:
        start_datetime = parts[0]
        end_datetime = parts[1]

    db.cursor.execute(
        """
        UPDATE reservations
        SET room_id = ?,
            attendees = ?,
            event_name = ?,
            start_datetime = ?,
            end_datetime = ?,
            notes = ?,
            status = 'pending approval'
        WHERE reservation_id = ?
    """,
        (
            room_id,
            int(attendees_count),
            event_name,
            start_datetime,
            end_datetime,
            notes,
            reservation_id,
        ),
    )

    db.conn.commit()


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
        f"Hello {user_name} please select a room", room_names
    ).ask()

    if room_name == "Quit" or room_name is None:
        return None

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


def _set_notes():
    note = questionary.text("Do you want to add any notes?", multiline=True).ask()
    return note
