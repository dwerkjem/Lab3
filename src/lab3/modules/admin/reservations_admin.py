"""
Name: Derek R. Neilson
Description: Admin TUI module for viewing, deleting, and approving reservations while checking for room scheduling conflicts.
"""

import questionary

from lab3.modules.crud.database import Database

db = Database()

reservation_style = questionary.Style(
    # Sets colors for status
    [
        ("approved", "fg:green"),
        ("pending", "fg:red"),
    ]
)


def choose_reservations() -> None:
    """Let an admin choose a reservation and perform an action on it."""
    while True:
        reservation_id = choose_reservation()

        if reservation_id is None:
            return

        operation = questionary.select(
            "What would you like to do?",
            choices=[
                "View reservation",
                "Update status",
                "Delete reservation",
                "Quit",
            ],
        ).ask()

        if operation in (None, "Quit"):
            return

        if operation == "View reservation":
            view_reservation(reservation_id)
        elif operation == "Update status":
            toggle_reservation_status(reservation_id)
        elif operation == "Delete reservation":
            delete_reservation(reservation_id)


def choose_reservation() -> int | None:
    """Prompt the admin to choose a reservation.

    Returns:
        int | None: The selected reservation ID, or None if there are no
        reservations or the admin chooses Quit.
    """
    rows = db.fetch_all_dict("""
        SELECT
            reservations.reservation_id,
            customers.full_name AS customer_name,
            rooms.name AS room_name,
            reservations.start_datetime,
            reservations.end_datetime,
            reservations.status
        FROM reservations
        JOIN customers
            ON reservations.customer_id = customers.customer_id
        JOIN rooms
            ON reservations.room_id = rooms.room_id
        ORDER BY reservations.start_datetime
    """)  # Gets reservations and orders them by start time
    # Include customer and room names so the reservation choices are readable.

    if not rows:
        print("No reservations found.")
        return None

    choices = []

    for row in rows:
        status_class = "approved" if row["status"] == "approved" else "pending"

        choices.append(
            questionary.Choice(
                title=[
                    (
                        "class:text",
                        f"{row['customer_name']} has reserved {row['room_name']} "
                        f"between {row['start_datetime']} and {row['end_datetime']} "
                        "and is currently ",
                    ),
                    (f"class:{status_class}", row["status"]),
                    ("class:text", "."),
                ],
                value=row["reservation_id"],
            )
        )  # Use the status as a style class so approved and pending reservations display differently.

    choices.append(questionary.Choice(title="Quit", value=None))

    return questionary.select(
        "Choose a reservation:",
        choices=choices,
        style=reservation_style,
    ).ask()


def view_reservation(reservation_id: int) -> None:
    """Fetch and print the full details for a reservation.

    Args:
        reservation_id (int): ID of the reservation to display.
    """

    # Join customers and rooms so the displayed reservation shows names instead of IDs.
    row = db.fetch_one_dict(
        """
        SELECT
            reservations.reservation_id,
            customers.full_name AS customer_name,
            rooms.name AS room_name,
            reservations.attendees,
            reservations.event_name,
            reservations.event_type,
            reservations.start_datetime,
            reservations.end_datetime,
            reservations.status,
            reservations.notes
        FROM reservations
        JOIN customers
            ON reservations.customer_id = customers.customer_id
        JOIN rooms
            ON reservations.room_id = rooms.room_id
        WHERE reservations.reservation_id = ?
        """,
        (reservation_id,),
    )

    if not row:
        print("Reservation not found.")
        return

    print(f"""
    Reservation #{row["reservation_id"]}
    Customer: {row["customer_name"]}
    Room: {row["room_name"]}
    Event: {row["event_name"]} ({row["event_type"]})
    Attendees: {row["attendees"]}
    Start: {row["start_datetime"]}
    End: {row["end_datetime"]}
    Status: {row["status"]}
    Notes: {row["notes"] or "None"}
    """)


def update_reservation_status(reservation_id: int, status: str) -> None:
    """Update a reservation's status and display the new value.

    Args:
        reservation_id (int): Reservation to update.
        status (str): New reservation status.
    """
    db.cursor.execute(
        """
        UPDATE reservations
        SET status = ?
        WHERE reservation_id = ?
        """,
        (status, reservation_id),
    )

    db.commit()  # Save the status change before reading it back.

    # Read the updated status from the database to confirm the change.
    updated = db.fetch_one_dict(
        """
        SELECT status
        FROM reservations
        WHERE reservation_id = ?
        """,
        (reservation_id,),
    )

    if updated:
        print(f"Reservation status is now {updated['status']}.")


def delete_reservation(reservation_id: int) -> None:
    """Delete a reservation and any optional services linked to it."""
    confirm = questionary.confirm(
        "Are you sure you want to delete this reservation?",
        default=False,
    ).ask()

    if not confirm:
        return  # Do not delete anything if the admin cancels.

    db.cursor.execute(
        """
        DELETE FROM reservation_services
        WHERE reservation_id = ?
        """,
        (reservation_id,),
    )

    db.cursor.execute(
        """
        DELETE FROM reservations
        WHERE reservation_id = ?
        """,
        (reservation_id,),
    )

    db.commit()
    print("Reservation deleted.")


def find_approved_overlap(reservation_id: int) -> dict | None:
    """Return an approved reservation that overlaps with the selected reservation.

    Only reservations for the same room are checked. Returns the first overlap
    found, or None if there is no conflicts.

    Is used to verify that there are no over laps.
    """

    return db.fetch_one_dict(
        """
        SELECT
            existing.reservation_id,
            customers.full_name AS customer_name,
            rooms.name AS room_name,
            existing.start_datetime,
            existing.end_datetime
        FROM reservations AS target
        JOIN reservations AS existing
            ON target.room_id = existing.room_id
        JOIN customers
            ON existing.customer_id = customers.customer_id
        JOIN rooms
            ON existing.room_id = rooms.room_id
        WHERE target.reservation_id = ?
            AND existing.reservation_id != target.reservation_id
            AND existing.status = 'approved'
            -- Two reservations overlap when each reservation starts before the other ends.
            AND target.start_datetime < existing.end_datetime
            AND target.end_datetime > existing.start_datetime
        LIMIT 1
        """,
        (reservation_id,),
    )


def approve_reservation(reservation_id: int) -> None:
    """Approve a reservation if it does not overlap an existing approved reservation.

    Args:
        reservation_id (int): Reservation to approve.
    """
    overlap = find_approved_overlap(reservation_id)

    if overlap:
        print(
            f"Cannot approve reservation.\n"
            f"It overlaps with reservation #{overlap['reservation_id']} "
            f"for {overlap['room_name']} "
            f"from {overlap['start_datetime']} "
            f"to {overlap['end_datetime']}."
        )
        return

    update_reservation_status(reservation_id, "approved")


def toggle_reservation_status(reservation_id: int) -> None:
    """Toggle a reservation between approved and pending approval.

    If the reservation is currently approved, it is changed back to pending
    approval. Otherwise, the reservation is approved only if it does not
    overlap with another approved reservations.
    """
    row = db.fetch_one_dict(
        """
        SELECT status
        FROM reservations
        WHERE reservation_id = ?
        """,
        (reservation_id,),
    )

    if not row:
        print("Reservation not found.")
        return  # Exit if the reservation ID is invalid or was deleted.

    if row["status"] == "approved":
        # Approved reservations can always be moved back to pending approval.
        update_reservation_status(reservation_id, "pending approval")
    else:
        approve_reservation(reservation_id)
