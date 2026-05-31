"""
Name: Derek R. Neilson
Description: Reservation pricing calculations and cost breakdown utilities.
"""

from datetime import datetime, timedelta

import holidays

from lab3.modules.crud.database import Database

db = Database()

# Percentage-based pricing adjustments.
WEEEKEND_SURCHARGE = 0.10
HOLIDAY_SURCHARGE = 0.15
WEEKEND_HOLIDAY_SURCHARGE = 0.05
DEPOSIT_PERCENT = 0.25


def reservation_days(start_datetime: str, end_datetime: str) -> int:
    """Return the inclusive number of days covered by a reservation.

    Args:
        start_datetime (str): Reservation start date and time as a string `"YY-MM-DD"`.
        end_datetime (str): Reservation end date and time as a string `"YY-MM-DD"`.

    Returns:
        int: Number of calendar days included in the reservation.
    """
    start_date = datetime.strptime(
        start_datetime.split()[0],
        "%y-%m-%d",
    ).date()

    end_date = datetime.strptime(
        end_datetime.split()[0],
        "%y-%m-%d",
    ).date()

    return (end_date - start_date).days + 1


# Monetary values are stored in cents to avoid floating-point rounding errors.
def calculate_room_total(
    start_datetime: str,
    end_datetime: str,
    day_rate_cents: int,
) -> tuple[int, int]:
    """Calculate the room total and surcharge total for a reservation.

    Args:
        start_datetime (str): Reservation start date and time as a string.
        end_datetime (str): Reservation end date and time as a string.
        day_rate_cents (int): Base room cost per day, stored in cents.

    Returns:
        tuple[int, int]: Total room cost in cents and total surcharge amount in cents.
    """
    start_date = datetime.strptime(
        start_datetime.split()[0],
        "%y-%m-%d",
    ).date()

    end_date = datetime.strptime(
        end_datetime.split()[0],
        "%y-%m-%d",
    ).date()

    us_holidays = holidays.US()

    total = 0
    surcharge_total = 0

    current = start_date

    # Check each calendar day so weekend and holiday surcharges can be applied daily.
    while current <= end_date:
        daily_cost = day_rate_cents
        surcharge = 0

        is_weekend = current.weekday() >= 5
        is_holiday = current in us_holidays

        # Apply each surcharge separately; weekend holidays receive all applicable surcharges.
        if is_weekend:
            surcharge += int(day_rate_cents * WEEEKEND_SURCHARGE)

        if is_holiday:
            surcharge += int(day_rate_cents * HOLIDAY_SURCHARGE)

        if is_weekend and is_holiday:
            surcharge += int(day_rate_cents * WEEKEND_HOLIDAY_SURCHARGE)

        total += daily_cost + surcharge
        surcharge_total += surcharge

        current += timedelta(days=1)

    return total, surcharge_total


def calculate_pricing(
    room_name: str,
    room_cost_cents: int,
    attendees: int,
    start_datetime: str,
    end_datetime: str,
    services: list[tuple],
    reservation_id: int | None = None,
) -> dict:
    """Calculate the full pricing breakdown for a reservation.

    Args:
        room_name (str): Name of the reserved room.
        room_cost_cents (int): Base room cost per day, stored in cents.
        attendees (int): Number of people attending the event.
        start_datetime (str): Reservation start date and time as a string.
        end_datetime (str): Reservation end date and time as a string.
        services (list[tuple]): Optional services as name, cost, and charge type tuples.
        reservation_id (int | None, optional): Reservation ID, if one already exists.

    Returns:
        dict: Pricing breakdown including room total, service total, deposit, and final total.
    """

    days = reservation_days(start_datetime, end_datetime)

    room_total_cents, surcharge_total_cents = calculate_room_total(
        start_datetime,
        end_datetime,
        room_cost_cents,
    )

    service_total_cents = 0
    service_breakdown = []

    # Service totals depend on how each service is charged.
    for name, cost_cents, charge_by in services:
        if charge_by == "one time":
            total = cost_cents
        elif charge_by == "daily":
            total = cost_cents * days
        elif charge_by == "attendees":
            total = cost_cents * attendees
        elif charge_by == "daily attendees":
            total = cost_cents * attendees * days
        else:
            total = 0

        service_total_cents += total

        service_breakdown.append(
            {
                "name": name,
                "charge_by": charge_by,
                "cost_cents": cost_cents,
                "total_cents": total,
            }
        )

    total_cents = room_total_cents + service_total_cents
    deposit_cents = int(round(total_cents * DEPOSIT_PERCENT))

    return {
        "reservation_id": reservation_id,
        "room_name": room_name,
        "attendees": attendees,
        "days": days,
        "room_total_cents": room_total_cents,
        "surcharge_total_cents": surcharge_total_cents,
        "services": service_breakdown,
        "service_total_cents": service_total_cents,
        "total_cents": total_cents,
        "deposit_cents": deposit_cents,
    }


def get_reservation_pricing(reservation_id: int) -> dict | None:
    """Fetch reservation data and return its pricing breakdown.

    Args:
        reservation_id (int): Reservation to calculate pricing for.

    Returns:
        dict | None: Pricing breakdown for the reservation, or None if the
        reservation does not exist.
    """
    # Fetch reservation and room data needed for the base room price.
    reservation = db.fetchone(
        """
        SELECT
            r.reservation_id,
            r.attendees,
            r.start_datetime,
            r.end_datetime,
            rooms.name,
            rooms.day_rate_cents
        FROM reservations r
        JOIN rooms ON rooms.room_id = r.room_id
        WHERE r.reservation_id = ?
        """,
        (reservation_id,),
    )

    if not reservation:
        print("Reservation not found.")
        return None

    (
        reservation_id,
        attendees,
        start_datetime,
        end_datetime,
        room_name,
        room_cost_cents,
    ) = reservation

    # Fetch optional services attached to this reservation.
    services = db.fetchall(
        """
        SELECT
            s.name,
            s.cost_cents,
            s.charge_by
        FROM reservation_services rs
        JOIN services s ON s.service_id = rs.service_id
        WHERE rs.reservation_id = ?
        """,
        (reservation_id,),
    )

    return calculate_pricing(
        room_name=room_name,
        room_cost_cents=room_cost_cents,
        attendees=attendees,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        services=services,
        reservation_id=reservation_id,
    )
