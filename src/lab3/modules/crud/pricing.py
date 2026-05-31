import questionary
from datetime import datetime, timedelta
import holidays

from lab3.modules.crud.database import Database

db = Database()


WEEEKEND_SURCHARGE = 0.10
HOLIDAY_SURCHARGE = 0.15
WEEKEND_HOLIDAY_SURCHARGE = 0.05
DEPOSIT_PERCENT = 0.25


def get_paid_total_cents(reservation_id: int) -> int:
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


def make_payment(reservation_id: int, amount_cents: int, payment_type: str):
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


def _reservation_days(start_datetime: str, end_datetime: str) -> int:
    start = start_datetime.split()[0]
    end = end_datetime.split()[0]

    from datetime import datetime

    start_date = datetime.strptime(start, "%Y-%m-%d").date()
    end_date = datetime.strptime(end, "%Y-%m-%d").date()

    return (end_date - start_date).days + 1


def _calculate_pricing(
    room_name: str,
    room_cost_cents: int,
    attendees: int,
    start_datetime: str,
    end_datetime: str,
    services: list[tuple],
    reservation_id: int | None = None,
) -> dict:
    days = _reservation_days(start_datetime, end_datetime)

    room_total_cents, surcharge_total_cents = calculate_room_total(
        start_datetime,
        end_datetime,
        room_cost_cents,
    )

    service_total_cents = 0
    service_breakdown = []

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

    return _calculate_pricing(
        room_name=room_name,
        room_cost_cents=room_cost_cents,
        attendees=attendees,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        services=services,
        reservation_id=reservation_id,
    )


def print_price_breakdown(pricing: dict):
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


def verify_and_make_deposit(reservation_id: int) -> bool:
    pricing = get_reservation_pricing(reservation_id)

    if pricing is None:
        return False

    print_price_breakdown(pricing)

    paid_total_cents = get_paid_total_cents(reservation_id)
    remaining_cents = pricing["total_cents"] - paid_total_cents

    print(f"\nAlready paid: ${paid_total_cents / 100:.2f}")
    print(f"Remaining balance: ${remaining_cents / 100:.2f}")

    if remaining_cents <= 0:
        print("This reservation is already fully paid.")
        return True

    deposit_paid = has_paid_deposit(reservation_id)

    if not deposit_paid:
        confirmed = questionary.confirm(
            "Do you verify this reservation and agree to make the required deposit?"
        ).ask()

        if not confirmed:
            print("Reservation was not verified. Deposit was not made.")
            return False

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

        print(f"Deposit paid: ${deposit_cents / 100:.2f}")
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
                else f"Enter an amount greater than $0.00 and no more than ${remaining_cents / 100:.2f}."
            ),
        ).ask()

        if amount is None:
            return False

        payment_cents = int(round(float(amount) * 100))

    make_payment(
        reservation_id,
        payment_cents,
        "balance",
    )

    print(f"Payment made: ${payment_cents / 100:.2f}")

    new_remaining_cents = remaining_cents - payment_cents
    print(f"Remaining balance: ${new_remaining_cents / 100:.2f}")

    return True


def make_or_view_payment(customer_id: int):
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


def calculate_room_total(
    start_datetime: str,
    end_datetime: str,
    day_rate_cents: int,
) -> tuple[int, int]:
    start_date = datetime.strptime(
        start_datetime.split()[0],
        "%Y-%m-%d",
    ).date()

    end_date = datetime.strptime(
        end_datetime.split()[0],
        "%Y-%m-%d",
    ).date()

    us_holidays = holidays.US()

    total = 0
    surcharge_total = 0

    current = start_date

    while current <= end_date:
        daily_cost = day_rate_cents
        surcharge = 0

        is_weekend = current.weekday() >= 5
        is_holiday = current in us_holidays

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


def preview_reservation_pricing(
    room_id: int,
    attendees: int,
    start_datetime: str,
    end_datetime: str,
    service_ids: list[int],
) -> dict | None:
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

    return _calculate_pricing(
        room_name=room_name,
        room_cost_cents=room_cost_cents,
        attendees=attendees,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        services=services,
    )
