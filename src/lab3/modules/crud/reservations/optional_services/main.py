import questionary

from lab3.modules.crud.database import Database

db = Database()


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
