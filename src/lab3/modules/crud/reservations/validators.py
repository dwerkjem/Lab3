"""
Name: Derek R. Neilson
Description: Date validation helpers for reservation scheduling.
"""

import datetime
from typing import Any, Callable, Literal

from lab3.modules.crud.database import Database

db = Database()


def _is_reserved_date_in_range(
    room_id: str, start_date: str, end_date: str
) -> list[Any] | Literal[False]:
    """Return approved reservations that overlap the requested date range.

    Args:
        room_id (str): Room ID to check.
        start_date (str): Requested start date in YY-MM-DD format.
        end_date (str): Requested end date in YY-MM-DD format.

    Returns:
        list[Any] | Literal[False]: Matching approved reservations, or False if there
        are no overlapping reservations.
    """

    reserved_dates = db.fetchall(
        """
        SELECT start_datetime, end_datetime
        FROM reservations
        WHERE room_id = ?
          AND status = 'approved'
          -- YY-MM-DD date strings can be compared lexicographically because the
          -- largest time unit appears first.
          AND start_datetime <= ?
          AND end_datetime >= ?
    """,
        (int(room_id), end_date, start_date),
    )

    if not reserved_dates:
        return False

    return reserved_dates


def validate_datetime(room_id: str) -> Callable[[str], str | Literal[True]]:
    """Return a validator for reservation date ranges.

    The validator checks format, prevents past dates, enforces start-before-end,
    limits normal reservations to 30 days, and rejects ranges that overlap an
    approved reservation for the selected room.

    Args:
        room_id (str): Room ID to check for approved reservation conflicts.

    Returns:
        Callable[[str], str | Literal[True]]: Validator function for date input.
    """

    def validator(dates: str):
        parts = dates.split()
        today = datetime.date.today()

        if len(parts) != 2:
            return "Enter exactly 2 dates using format `YY-MM-DD YY-MM-DD`."

        parsed_dates = []

        for date in parts:
            try:
                parsed_date = datetime.datetime.strptime(date, "%y-%m-%d").date()
                parsed_dates.append(parsed_date)
            except ValueError:
                return f"{date} is invalid, use this format `YY-MM-DD`."

            if parsed_date < today:
                return f"{date} is in the past. Please enter today or a future date."

        start, end = parsed_dates

        if start > end:
            return f"The start date {parts[0]} must be before {parts[1]}."

        if (end - start).days > 30:
            return (
                "Reservations cannot be longer than 30 days without special approval."
            )

        reserved_dates = _is_reserved_date_in_range(room_id, parts[0], parts[1])

        if reserved_dates:
            return f"That room is already reserved during: {reserved_dates}"

        return True

    return validator
