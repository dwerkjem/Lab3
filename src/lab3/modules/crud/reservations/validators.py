"""
Name: Derek R. Neilson
Description: Date validation helpers for reservation scheduling.
"""

import datetime
from typing import Any, Callable, Literal

from lab3.modules.crud.database import Database

db = Database()


def _parse_db_date(value: str) -> datetime.date:
    """
    Parse a database date value into a ``datetime.date``.

    Supports the following formats:
    - YY-MM-DD (e.g. ``26-9-8`` or ``26-09-08``)
    - YYYY-MM-DD (e.g. ``2026-09-08``)
    - Datetime strings where the date is the first token
      (e.g. ``2026-09-08 14:30:00``)

    Args:
        value: Date value retrieved from the database.

    Raises:
        ValueError: If the value cannot be parsed as a supported date format.

    Returns:
        The parsed date.
    """
    value = str(value).split()[0]

    for fmt in ("%y-%m-%d", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(value, fmt).date()
        except ValueError:
            pass

    raise ValueError(f"Invalid date in database: {value}")


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

    requested_start = _parse_db_date(start_date)
    requested_end = _parse_db_date(end_date)

    reservations = db.fetchall(
        """
        SELECT start_datetime, end_datetime
        FROM reservations
        WHERE room_id = ?
          AND status = 'approved'
        """,
        (int(room_id),),
    )

    overlapping = []

    for reservation in reservations:
        reserved_start = _parse_db_date(reservation[0])
        reserved_end = _parse_db_date(reservation[1])

        if reserved_start <= requested_end and reserved_end >= requested_start:
            overlapping.append(reservation)

    if not overlapping:
        return False

    return overlapping


def validate_datetime(room_id: str) -> Callable[[str], str | Literal[True]]:
    """Return a validator for reservation date or date range."""

    def validator(dates: str):
        parts = dates.split()
        today = datetime.date.today()

        if len(parts) not in (1, 2):
            return "Enter 1 or 2 dates using format `YY-MM-DD` or `YY-MM-DD YY-MM-DD`."

        parsed_dates = []

        for date in parts:
            try:
                parsed_date = datetime.datetime.strptime(date, "%y-%m-%d").date()
                parsed_dates.append(parsed_date)
            except ValueError:
                return f"{date} is invalid, use this format `YY-MM-DD`."

            if parsed_date < today:
                return f"{date} is in the past. Please enter today or a future date."

        if len(parsed_dates) == 1:
            start = end = parsed_dates[0]
        else:
            start, end = parsed_dates

            if start > end:
                return f"The start date {parts[0]} must be before {parts[1]}."

            if (end - start).days > 30:
                return "Reservations cannot be longer than 30 days without special approval."

        reserved_dates = _is_reserved_date_in_range(
            room_id,
            start.strftime("%y-%m-%d"),
            end.strftime("%y-%m-%d"),
        )

        if reserved_dates:
            return f"That room is already reserved during: {reserved_dates}"

        return True

    return validator
