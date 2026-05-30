import questionary

from lab3.modules.crud.database import Database

db = Database()


def get_list_of_services():
    rows = db.fetchall("""
        SELECT service_id, name, cost_cents, charge_by
        FROM services
        ORDER BY name
    """)

    return [
        questionary.Choice(
            title=f"{row['name']} - ${row['cost_cents'] / 100:.2f} ({row['charge_by']})",
            value=row["service_id"],
        )
        for row in rows
    ]
