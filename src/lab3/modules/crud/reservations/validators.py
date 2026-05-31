import datetime

from lab3.modules.crud.database import Database

db = Database()


def _is_reserved_date_in_range(room_id: str, start_date: str, end_date: str):
    reserved_dates = db.fetchall(
        """
        SELECT start_datetime, end_datetime
        FROM reservations
        WHERE room_id = ?
          AND status = 'approved'
          AND start_datetime <= ?
          AND end_datetime >= ?
    """,
        (int(room_id), end_date, start_date),
    )  # This woks only because it is YY-MM-DD and
    # therefore there in the right order and can be compared like this.

    if not reserved_dates:
        return False

    return reserved_dates


def validate_datetime(room_id):
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
            return f"The start date {parts[0]} must be before {parts[1]}"

        if (end - start).days > 30:
            return (
                "Reservations cannot be longer than 30 days without special approval."
            )

        reserved_dates = _is_reserved_date_in_range(room_id, parts[0], parts[1])

        if reserved_dates:
            return f"That room is already reserved during: {reserved_dates}"

        return True

    return validator
