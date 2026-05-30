import questionary

from lab3.modules.crud.database import Database

db = Database()

reservation_style = questionary.Style(
    [
        ("approved", "fg:green"),
        ("pending", "fg:red"),
    ]
)


def chose_reservations():
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


def choose_reservation():
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
    """)

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
        )

    choices.append(questionary.Choice(title="Quit", value=None))

    return questionary.select(
        "Choose a reservation:",
        choices=choices,
        style=reservation_style,
    ).ask()


def view_reservation(reservation_id: int):
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


def update_reservation_status(reservation_id: int, status: str):
    db.cursor.execute(
        """
        UPDATE reservations
        SET status = ?
        WHERE reservation_id = ?
        """,
        (status, reservation_id),
    )
    db.commit()

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


def choose_and_update_status(reservation_id: int):
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
        return

    if row["status"] == "approved":
        update_reservation_status(reservation_id, "pending approval")
        return

    approve_reservation(reservation_id)


def delete_reservation(reservation_id: int):
    confirm = questionary.confirm(
        "Are you sure you want to delete this reservation?",
        default=False,
    ).ask()

    if not confirm:
        return

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


def find_approved_overlap(reservation_id: int):
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
            AND target.start_datetime < existing.end_datetime
            AND target.end_datetime > existing.start_datetime
        LIMIT 1
        """,
        (reservation_id,),
    )


def approve_reservation(reservation_id: int):
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


def toggle_reservation_status(reservation_id: int):
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
        return

    if row["status"] == "approved":
        update_reservation_status(reservation_id, "pending approval")
    else:
        approve_reservation(reservation_id)
