import sys

import questionary

from lab3.modules.crud.database import Database
from lab3.modules.crud.main import CRUD
from lab3.modules.crud.reservations.values import (
    _get_room,
    get_attendees_count,
    set_date,
    set_event_name,
    set_notes,
)

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
        edit_existing_reservation(reservation_list, room_names, user_name)

    else:
        return


def _setup(customer_id, room_names, user_name):
    event_name = set_event_name()
    if event_name is None:
        sys.exit(0)

    room = _get_room(room_names, user_name)
    if room is None:
        sys.exit(0)

    room_id = room["id"]

    date_string = set_date(room_id)
    if date_string is None:
        sys.exit(0)

    attendees_count = get_attendees_count(crud.integer_validator)
    if attendees_count is None:
        sys.exit(0)

    notes = set_notes()

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


def edit_existing_reservation(reservation_list, room_names, user_name) -> None:
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

    event_name = set_event_name()
    if event_name is None:
        return

    room = _get_room(room_names, user_name)
    if room is None:
        return

    room_id = room["id"]

    date_string = set_date(room_id)
    if date_string is None:
        return

    attendees_count = get_attendees_count(crud.integer_validator)
    if attendees_count is None:
        return

    notes = set_notes()

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
