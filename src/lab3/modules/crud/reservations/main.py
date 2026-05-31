"""
Name: Derek R. Neilson
Description: Reservation creation and editing workflow.
"""

import sys

import questionary

from lab3.modules.crud.database import Database
from lab3.modules.crud.main import CRUD
from lab3.modules.crud.pricing.verify_payments import make_payment
from lab3.modules.crud.reservations.optional_services import choose_reservation_services
from lab3.modules.crud.reservations.values import (
    get_attendees_count,
    get_room,
    room_name_from_id,
    set_date,
    set_event_name,
    set_event_type,
    set_notes,
)

from lab3.modules.crud.pricing.main import (
    preview_reservation_pricing,
    print_price_breakdown,
)

db = Database()
crud = CRUD(db)


def _split_dates(date_string: str) -> tuple[str, str]:
    """Split a date string into start and end dates.

    Args:
        date_string (str): One date or two dates separated by whitespace.

    Returns:
        tuple[str, str]: Start date and end date. If only one date is given,
        the same date is returned for both values.
    """
    parts = date_string.split()
    return (parts[0], parts[0]) if len(parts) == 1 else (parts[0], parts[1])


def _room_choice_label(name: str, day_rate_cents: int) -> str:
    """Create a display label for a room selection option.

    Args:
        name (str): Room name.
        day_rate_cents (int): Room daily rate stored in cents.

    Returns:
        str: Formatted room label including the room name and daily rate.
    """
    return (
        f"{name} - ${day_rate_cents / 100:.2f}"  # Convert cents to dollars for display.
    )


def edit_reservations(name_dict: dict[str, int | str]) -> None:
    """Let a customer create a new reservation or edit an existing one.

    Args:
        name_dict (dict): Selected customer data containing the customer's ID
        and display name.
    """
    room_list = db.fetchall("SELECT room_id, name, day_rate_cents FROM rooms")

    # Rooms are required before a reservation can be created or edited.
    if not room_list:
        print("No rooms are created. Contact admin!")
        return

    customer_id = name_dict["id"]
    user_name = name_dict["value"]

    # Map the displayed room label back to the room name stored in the database.
    room_display_to_name = {
        _room_choice_label(name, day_rate_cents): name
        for _, name, day_rate_cents in room_list
    }

    room_names = ["Quit"] + list(room_display_to_name.keys())

    reservation_list = db.fetchall(
        """
        SELECT reservation_id, event_name
        FROM reservations
        WHERE customer_id = ?
        """,
        (customer_id,),
    )

    # If the customer has no reservations, go directly to the reservation setup flow.
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


def _setup(customer_id: int, room_names: list[str], user_name: str) -> None:
    """Collect reservation details, preview pricing, and create a reservation.

    Prompts the user for event information, room, dates, attendees, optional
    services, and notes. The reservation is saved only after the user confirms
    the pricing and required deposit.
    """
    event_name = set_event_name()
    event_type = set_event_type()
    room = get_room(user_name)

    if event_name is None or event_type in (None, "Quit") or room is None:
        sys.exit(
            0
        )  # Exit if the user cancels before required reservation details are collected.

    room_id = room["id"]
    date_string = set_date(room_id)
    attendees_count = get_attendees_count(crud.integer_validator)

    if date_string is None or attendees_count is None:
        sys.exit(0)

    start_datetime, end_datetime = _split_dates(date_string)

    selected_service_ids = choose_reservation_services()
    notes = set_notes()

    # Preview pricing before saving so the user can confirm the required deposit.
    pricing = preview_reservation_pricing(
        room_id=room_id,
        attendees=int(attendees_count),
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        service_ids=selected_service_ids,
    )

    print_price_breakdown(pricing)

    confirmed = questionary.confirm(
        f"The required deposit is "
        f"${pricing['deposit_cents'] / 100:.2f}. "
        "Would you like to continue?"
    ).ask()

    if not confirmed:
        print("Reservation cancelled.")
        return

    status = approval_status(int(attendees_count))

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
            notes,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            customer_id,
            room_id,
            int(attendees_count),
            event_name,
            event_type.lower(),
            start_datetime,
            end_datetime,
            notes,
            status,
        ),
    )

    # Save the reservation first so linked services can reference its reservation ID.
    reservation_id = db.cursor.lastrowid
    save_reservation_services(reservation_id, selected_service_ids)

    db.conn.commit()

    pay_now = questionary.confirm(
        f"Pay the deposit of ${pricing['deposit_cents'] / 100:.2f} now?"
    ).ask()

    # Deposit payment is optional at creation; unpaid reservations remain recorded.
    if pay_now:
        make_payment(
            reservation_id,
            pricing["deposit_cents"],
            "deposit",
        )


def edit_existing_reservation(
    reservation_list: list[tuple[int, str]],
    room_names: list[str],
    user_name: str,
) -> None:
    """Let a customer edit one of their existing reservations.

    Existing reservation values are used as defaults. After editing, the
    reservation status is reset to pending approval.
    """

    # Map event names to reservation IDs for the selection menu.
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

    # Convert separate start and end values into the format expected by `set_date()`.
    date_default = start if start == end else f"{start} {end}"

    event_name = set_event_name(default=event_name_default)
    event_type = set_event_type(default=event_type_default.title())
    room = get_room(user_name, default=room_name_from_id(room_id))

    if event_name is None or event_type in (None, "Quit") or room is None:
        return

    date_string = set_date(room["id"], default=date_default)
    attendees_count = get_attendees_count(
        crud.integer_validator,
        default=str(attendees),
    )

    selected_service_ids = choose_reservation_services()

    notes = set_notes(default=notes_default or "")

    if date_string is None or attendees_count is None:
        return

    start_datetime, end_datetime = _split_dates(date_string)

    db.cursor.execute(  # Reset edited reservations to pending approval so changes can be reviewed.
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

    save_reservation_services(reservation_id, selected_service_ids)

    db.conn.commit()


def save_reservation_services(reservation_id: int, service_ids: list[int]) -> None:
    """Replace the optional services linked to a reservation.

    Args:
        reservation_id (int): Reservation whose services should be updated.
        service_ids (list[int]): Service IDs to attach to the reservation.
    """

    # Clear old service links so the saved list exactly matches the current selection.
    db.cursor.execute(
        """
        DELETE FROM reservation_services
        WHERE reservation_id = ?
        """,
        (reservation_id,),
    )

    # Add the currently selected services for this reservation.
    for service_id in service_ids:
        db.cursor.execute(
            """
            INSERT INTO reservation_services (reservation_id, service_id)
            VALUES (?, ?)
            """,
            (reservation_id, service_id),
        )


def approval_status(attendees_count: int) -> str:
    """Return the reservation approval status based on attendee count.

    Args:
        attendees_count (int): Number of guests for the reservation.

    Returns:
        str: "approved" if fewer than 300 guests are attending; otherwise
        "pending approval".
    """
    if attendees_count < 300:
        print("You are auto-approved because you have under 300 guests.")
        return "approved"

    return "pending approval"
