"""
Name: Derek R. Neilson
Description: Payment and pricing display helpers for reservations.
"""

from lab3.modules.crud.database import Database
from lab3.modules.crud.pricing.calculations import calculate_pricing
from datetime import datetime

db = Database()

# Percentage-based pricing adjustments.
WEEEKEND_SURCHARGE = 0.10
HOLIDAY_SURCHARGE = 0.15
WEEKEND_HOLIDAY_SURCHARGE = 0.05
DEPOSIT_PERCENT = 0.25


def get_paid_total_cents(reservation_id: int) -> int:
    """Return the total paid amount for a reservation in cents."""
    row = db.fetchone(
        """
        SELECT COALESCE(SUM(amount_cents), 0)
        FROM payments
        WHERE reservation_id = ?
          AND status = 'paid'
        """,
        (reservation_id,),
    )

    return row[0] if row else 0


def has_paid_deposit(reservation_id: int) -> bool:
    """Return whether the reservation has a paid deposit recorded."""

    row = db.fetchone(
        """
        SELECT 1
        FROM payments
        WHERE reservation_id = ?
          AND payment_type = 'deposit'
          AND status = 'paid'
        LIMIT 1
        """,
        (reservation_id,),
    )

    return row is not None


def reservation_days(start_datetime: str, end_datetime: str) -> int:
    """Return the inclusive number of days covered by a reservation."""
    start = start_datetime.split()[0]
    end = end_datetime.split()[0]

    start_date = datetime.strptime(start, "%y-%m-%d").date()
    end_date = datetime.strptime(end, "%y-%m-%d").date()

    return (end_date - start_date).days + 1


def print_price_breakdown(pricing: dict) -> None:
    """Print a formatted pricing breakdown for a reservation."""
    print("\nPrice Breakdown")
    print("----------------")
    print(f"Room: {pricing['room_name']}")
    print(f"Days: {pricing['days']}")
    print(f"Attendees: {pricing['attendees']}")
    print(f"Room total: ${pricing['room_total_cents'] / 100:.2f}")
    print(f"Weekend/Holiday surcharges: ${pricing['surcharge_total_cents'] / 100:.2f}")

    print("\nOptional Services:")
    if not pricing["services"]:
        print("No optional services selected.")
    else:
        for service in pricing["services"]:
            print(
                f"- {service['name']} "
                f"({service['charge_by']}): "
                f"${service['total_cents'] / 100:.2f}"
            )

    print(f"\nService total: ${pricing['service_total_cents'] / 100:.2f}")
    print(f"Grand total: ${pricing['total_cents'] / 100:.2f}")
    print(f"Required deposit: ${pricing['deposit_cents'] / 100:.2f}")


def preview_reservation_pricing(
    room_id: int,
    attendees: int,
    start_datetime: str,
    end_datetime: str,
    service_ids: list[int],
) -> dict | None:
    """Calculate pricing for a reservation before it is saved.

    Returns None if the selected room does not exist.
    """
    room = db.fetchone(
        """
        SELECT
            name,
            day_rate_cents
        FROM rooms
        WHERE room_id = ?
        """,
        (room_id,),
    )

    if not room:
        return None

    room_name, room_cost_cents = room

    services = []

    if service_ids:
        placeholders = ",".join("?" for _ in service_ids)

        services = db.fetchall(
            f"""
            SELECT
                name,
                cost_cents,
                charge_by
            FROM services
            WHERE service_id IN ({placeholders})
            """,
            service_ids,
        )

    return calculate_pricing(
        room_name=room_name,
        room_cost_cents=room_cost_cents,
        attendees=attendees,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        services=services,
    )
