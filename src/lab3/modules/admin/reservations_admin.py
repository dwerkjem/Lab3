from lab3.modules.crud.database import Database
import questionary

db = Database()


def chose_reservations():
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

    choices = [
        questionary.Choice(
            title=(
                f"{row['customer_name']} has reserved {row['room_name']} "
                f"between {row['start_datetime']} and {row['end_datetime']} "
                f"and is currently {row['status']}."
            ),
            value=row["reservation_id"],
        )
        for row in rows
    ]

    choices.append(questionary.Choice(title="Quit", value=None))

    return questionary.select(
        "Choose a reservation:",
        choices=choices,
    ).ask()
