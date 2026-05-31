"""
Name: Derek R. Neilson
Description: Admin and customer management of optional reservation services.
"""

from typing import Literal

import questionary

from lab3.modules.crud.database import Database
from lab3.modules.crud.main import CRUD

db = Database()

crud = CRUD(db)


def edit_add_service() -> None:
    """Let an admin choose an existing service to edit or enter a new service to add."""

    # Existing service names are used both for autocomplete and to decide add vs. edit.
    rows = db.fetchall("SELECT service_id, name FROM services")
    service_names = [name for _, name in rows]

    service_name = CRUD.choose_autocomplete_or_text_prompt(
        "Choose a service to add or edit.",
        service_validator,
        service_names,
    )

    # Exit if the admin cancels the prompt.
    if service_name is None:
        return

    if service_name in service_names:
        edit_service(service_name)
    else:
        add_service(service_name)


def get_list_of_services() -> list[questionary.Choice]:
    """Return service records formatted as Questionary choices."""
    rows = db.fetchall("""
        SELECT service_id, name, description, cost_cents, charge_by
        FROM services
        ORDER BY name
    """)

    return [
        questionary.Choice(
            title=(  # Format each service as one display line and convert cents to dollars.
                f"{row['name']} - ${row['cost_cents'] / 100:,.2f} ({row['charge_by']}) "
                f"{'| ' + row['description'] if row['description'] else ''}"
            ),
            value=row["service_id"],
        )
        for row in rows
    ]


def choose_services() -> list[int]:
    """Prompt the user to choose optional services.

    Returns:
        list[int]: Selected service IDs, or an empty list if no services are
        available or the prompt is cancelled.
    """

    choices = get_list_of_services()

    if not choices:
        print("No services are available.")
        return []

    return (
        questionary.checkbox(
            "Choose services:",
            choices=choices,
        ).ask()
        or []  # Return an empty list if the user cancels without selecting services.
    )


def service_validator(service: str) -> str | Literal[True]:
    """Validate that a service name is entered in title case.

    Args:
        service (str): Service name entered by the user.

    Returns:
        str | bool: Error message if validation fails; otherwise True.
    """
    if service != service.title():
        return "Make title case."
    return True


def add_service(name: str) -> None:
    """Prompt for service details and add a new optional service.

    Args:
        name (str): Name of the service to add.
    """

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

    # Store money in cents to avoid floating-point rounding issues in the database.
    cost_cents = int(round(float(cost_dollars) * 100))

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


def edit_service(name: str) -> None:
    """Edit an existing optional service.

    Args:
        name (str): Name of the service to edit.
    """
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
    # Use existing values as defaults so unchanged fields can be kept.
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
        default=f"{old_cost_cents / 100:,.2f}",
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

    # Store money in cents to avoid floating-point rounding issues in the database.
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


def choose_reservation_services() -> list[int]:
    """Prompt the user to select optional services for a reservation.

    Returns:
        list[int]: Selected service IDs, or an empty list if no services are
        available or the prompt is cancelled.
    """
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

    # Convert service rows into checkbox choices for the reservation form.
    choices = [
        questionary.Choice(
            title=(
                f"{row[1]} - ${row[3] / 100:,.2f} ({row[4]}) "
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
        or []  # Return an empty list if the user cancels or selects no services.
    )
