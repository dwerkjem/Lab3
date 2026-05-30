import questionary

from lab3.modules.crud.database import Database
from lab3.modules.crud.main import CRUD

db = Database()

crud = CRUD(db)


def get_list_of_services():
    rows = db.fetchall("""
        SELECT service_id, name, description, cost_cents, charge_by
        FROM services
        ORDER BY name
    """)

    return [
        questionary.Choice(
            title=(  # this will flatten to one line also convert cents to dollars
                f"{row['name']} - ${row['cost_cents'] / 100:.2f} ({row['charge_by']}) "
                f"{'| ' + row['description'] if row['description'] else ''}"
            ),
            value=row["service_id"],
        )
        for row in rows
    ]


def choose_services():
    choices = get_list_of_services()

    if not choices:
        print("No services are available.")
        return []

    return (
        questionary.checkbox(
            "Choose services:",
            choices=choices,
        ).ask()
        or []
    )


def add_service():
    name = questionary.text("Service name:").ask()
    if not name:
        return

    description = questionary.text("Description:").ask()

    cost_dollars = questionary.text(
        "Cost in dollars:", validate=crud.dollar_validator
    ).ask()
    if not cost_dollars:
        return

    charge_by = questionary.select(
        "Charge by:",
        choices=[
            "one time",
            "daily",
            "attendees",
            "daily attendees",
        ],
    ).ask()

    if not charge_by:
        return

    cost_cents = int(float(cost_dollars) * 100)

    db.cursor.execute(
        """
        INSERT INTO services (
            name,
            description,
            cost_cents,
            charge_by
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            name,
            description,
            cost_cents,
            charge_by,
        ),
    )

    db.commit()
    print(f"Added service: {name}")
