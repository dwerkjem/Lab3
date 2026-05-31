import questionary

from lab3.modules.crud.database import Database
from lab3.modules.crud.main import CRUD

db = Database()

crud = CRUD(db)


def edit_add_service():
    rows = db.fetchall("SELECT service_id, name FROM services")
    service_names = [name for _, name in rows]

    service_name = CRUD.choose_autocomplete_or_text_prompt(
        "Choose a service to add or edit.",
        service_validator,
        service_names,
    )

    if service_name is None:
        return

    if service_name in service_names:
        edit_service(service_name)
    else:
        add_service(service_name)


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


def service_validator(service: str):
    if service != service.title():
        return "Make title case."
    return True


def add_service(name: str):
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


def edit_service(name: str):
    service = db.fetchone(
        """
        SELECT service_id, name, description, cost_cents, charge_by
        FROM services
        WHERE name = ?
        """,
        (name,),
    )

    if not service:
        print("Service not found.")
        return

    service_id = service[0]
    old_name = service[1]
    old_description = service[2] or ""
    old_cost_cents = service[3]
    old_charge_by = service[4]

    new_name = questionary.text(
        "Name:",
        default=old_name,
        validate=service_validator,
    ).ask()
    if not new_name:
        return

    description = questionary.text(
        "Description:",
        default=old_description,
    ).ask()

    cost_dollars = questionary.text(
        "Cost in dollars:",
        default=f"{old_cost_cents / 100:.2f}",
        validate=crud.dollar_validator,
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
        default=old_charge_by,
    ).ask()
    if not charge_by:
        return

    cost_cents = int(round(float(cost_dollars) * 100))

    db.cursor.execute(
        """
        UPDATE services
        SET name = ?,
            description = ?,
            cost_cents = ?,
            charge_by = ?
        WHERE service_id = ?
        """,
        (
            new_name,
            description,
            cost_cents,
            charge_by,
            service_id,
        ),
    )

    db.commit()
    print(f"Updated service: {new_name}")


def choose_reservation_services():
    rows = db.fetchall(
        """
        SELECT service_id, name, description, cost_cents, charge_by
        FROM services
        ORDER BY name
        """
    )

    if not rows:
        print("No services are available.")
        return []

    choices = [
        questionary.Choice(
            title=(
                f"{row[1]} - ${row[3] / 100:.2f} ({row[4]}) "
                f"{'| ' + row[2] if row[2] else ''}"
            ),
            value=row[0],
        )
        for row in rows
    ]

    return (
        questionary.checkbox(
            "Select optional services for this reservation:",
            choices=choices,
        ).ask()
        or []
    )
