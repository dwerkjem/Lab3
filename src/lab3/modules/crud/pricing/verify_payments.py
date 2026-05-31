"""
Name: Derek R. Neilson
Description: Reservation payment workflow helpers.
"""

from lab3.modules.crud.pricing.calculations import get_reservation_pricing
from lab3.modules.crud.pricing.main import (
    get_paid_total_cents,
    has_paid_deposit,
    print_price_breakdown,
)

from lab3.modules.crud.database import Database

import questionary

db = Database()


def make_payment(reservation_id: int, amount_cents: int, payment_type: str) -> None:
    """Record a paid payment for a reservation."""
    db.cursor.execute(
        """
        INSERT INTO payments (
            reservation_id,
            amount_cents,
            payment_type,
            status
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            reservation_id,
            amount_cents,
            payment_type,
            "paid",
        ),
    )

    db.conn.commit()


def verify_and_make_deposit(reservation_id: int) -> bool:
    """Verify a reservation and collect its deposit or balance payment.

    Returns:
        bool: True if a payment or verification succeeds, otherwise False.
    """

    pricing = get_reservation_pricing(reservation_id)

    if pricing is None:
        return False

    print_price_breakdown(pricing)

    paid_total_cents = get_paid_total_cents(reservation_id)
    remaining_cents = pricing["total_cents"] - paid_total_cents

    print(f"\nAlready paid: ${paid_total_cents / 100:,.2f}")
    print(f"Remaining balance: ${remaining_cents / 100:,.2f}")

    if remaining_cents <= 0:
        print("This reservation is already fully paid.")
        return True

    deposit_paid = has_paid_deposit(reservation_id)
    # A reservation must have a paid deposit before balance payments are offered.
    if not deposit_paid:
        confirmed = questionary.confirm(
            "Do you verify this reservation and agree to make the required deposit?"
        ).ask()

        if not confirmed:
            print("Reservation was not verified. Deposit was not made.")
            return False

        # Limit deposit payment to the remaining balance in case the reservation is nearly paid off.
        deposit_cents = min(pricing["deposit_cents"], remaining_cents)

        make_payment(
            reservation_id,
            deposit_cents,
            "deposit",
        )

        db.cursor.execute(
            """
            UPDATE reservations
            SET status = 'approved'
            WHERE reservation_id = ?
            """,
            (reservation_id,),
        )

        db.conn.commit()

        print(f"Deposit paid: ${deposit_cents / 100:,.2f}")
        print("Reservation verified.")
        return True

    print("Deposit has already been paid.")

    choice = questionary.select(
        "What would you like to pay?",
        choices=[
            "Pay full remaining balance",
            "Pay part of remaining balance",
            "Cancel",
        ],
    ).ask()

    if choice in (None, "Cancel"):
        return False

    if choice == "Pay full remaining balance":
        payment_cents = remaining_cents
    else:
        amount = questionary.text(
            "How much would you like to pay?",
            validate=lambda value: (
                True
                if value.replace(".", "", 1).isdigit()
                and float(value) > 0
                and int(round(float(value) * 100)) <= remaining_cents
                else f"Enter an amount greater than $0.00 and no more than ${remaining_cents / 100:,.2f}."
            ),
        ).ask()

        if amount is None:
            return False
        # Convert the entered dollar amount to cents before storing it.
        payment_cents = int(round(float(amount) * 100))

    make_payment(
        reservation_id,
        payment_cents,
        "balance",
    )

    print(f"Payment made: ${payment_cents / 100:,.2f}")

    new_remaining_cents = remaining_cents - payment_cents
    print(f"Remaining balance: ${new_remaining_cents / 100:,.2f}")

    return True


def make_or_view_payment(customer_id: int) -> None:
    """Let a customer choose one of their reservations and make a payment."""
    reservations = db.fetchall(
        """
        SELECT reservation_id, event_name, start_datetime, end_datetime
        FROM reservations
        WHERE customer_id = ?
        ORDER BY start_datetime
        """,
        (customer_id,),
    )

    if not reservations:
        print("You do not have any reservations.")
        return

    choices = [
        questionary.Choice(
            title=f"{event_name} ({start_datetime} to {end_datetime})",
            value=reservation_id,
        )
        for reservation_id, event_name, start_datetime, end_datetime in reservations
    ]

    reservation_id = questionary.select(
        "Choose a reservation:",
        choices=choices,
    ).ask()

    if reservation_id is None:
        return

    verify_and_make_deposit(reservation_id)
