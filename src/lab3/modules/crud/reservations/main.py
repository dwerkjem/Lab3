import sys

import questionary

from lab3.modules.crud.database import Database
from lab3.modules.crud.main import CRUD
from lab3.modules.crud.reservations.values import (
    get_attendees_count,
    get_room,
    room_name_from_id,
    set_date,
    set_event_name,
    set_event_type,
    set_notes,
)

db = Database()
crud = CRUD(db)


def _split_dates(date_string):
    parts = date_string.split()
    return (parts[0], parts[0]) if len(parts) == 1 else (parts[0], parts[1])


def edit_reservations(name_dict: dict):
    room_list = db.fetchall("SELECT room_id, name FROM rooms")

    if not room_list:
        print("No rooms are created. Contact admin!")
        return

    customer_id = name_dict["id"]
    user_name = name_dict["value"]
    room_names = ["Quit"] + [name for _, name in room_list]

    reservation_list = db.fetchall(
        """
        SELECT reservation_id, event_name
        FROM reservations
        WHERE customer_id = ?
        """,
        (customer_id,),
    )

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
        edit_existing_reservation(reservation_list, room_names, user_name)


def _setup(customer_id, room_names, user_name):
    event_name = set_event_name()
    event_type = set_event_type()
    room = get_room(room_names, user_name)

    if event_name is None or event_type in (None, "Quit") or room is None:
        sys.exit(0)

    room_id = room["id"]
    date_string = set_date(room_id)
    attendees_count = get_attendees_count(crud.integer_validator)

    if date_string is None or attendees_count is None:
        sys.exit(0)

    start_datetime, end_datetime = _split_dates(date_string)

    db.cursor.execute(
        """
        INSERT INTO reservations (
            customer_id,
            room_id,
            attendees,
            event_name,
            event_type,
            start_datetime,
            end_datetime,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            customer_id,
            room_id,
            int(attendees_count),
            event_name,
            event_type.lower(),
            start_datetime,
            end_datetime,
            set_notes(),
        ),
    )

    db.conn.commit()


def edit_existing_reservation(reservation_list, room_names, user_name) -> None:
    reservation_options = {
        event_name: reservation_id for reservation_id, event_name in reservation_list
    }

    selected_event = questionary.select(
        "Which reservation do you want to edit?",
        ["Quit"] + list(reservation_options),
    ).ask()

    if selected_event in (None, "Quit"):
        return

    reservation_id = reservation_options[selected_event]

    db.cursor.execute(
        """
        SELECT
            room_id,
            attendees,
            event_name,
            event_type,
            start_datetime,
            end_datetime,
            notes
        FROM reservations
        WHERE reservation_id = ?
        """,
        (reservation_id,),
    )

    current = db.cursor.fetchone()
    (
        room_id,
        attendees,
        event_name_default,
        event_type_default,
        start,
        end,
        notes_default,
    ) = current
    date_default = start if start == end else f"{start} {end}"

    event_name = set_event_name(default=event_name_default)
    event_type = set_event_type(default=event_type_default.title())
    room = get_room(room_names, user_name, default=room_name_from_id(room_id))

    if event_name is None or event_type in (None, "Quit") or room is None:
        return

    date_string = set_date(room["id"], default=date_default)
    attendees_count = get_attendees_count(
        crud.integer_validator,
        default=str(attendees),
    )
    notes = set_notes(default=notes_default or "")

    if date_string is None or attendees_count is None:
        return

    start_datetime, end_datetime = _split_dates(date_string)

    db.cursor.execute(
        """
        UPDATE reservations
        SET room_id = ?,
            attendees = ?,
            event_name = ?,
            event_type = ?,
            start_datetime = ?,
            end_datetime = ?,
            notes = ?,
            status = 'pending approval'
        WHERE reservation_id = ?
        """,
        (
            room["id"],
            int(attendees_count),
            event_name,
            event_type.lower(),
            start_datetime,
            end_datetime,
            notes,
            reservation_id,
        ),
    )

    db.conn.commit()
