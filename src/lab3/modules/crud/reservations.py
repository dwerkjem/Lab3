import questionary
from lab3.modules.crud.database import Database
from lab3.modules.crud.rooms import get_room_by_name
from lab3.modules.crud.main import CRUD
import datetime

db = Database()

crud = CRUD(db)


def edit_reservations(name_dict: dict):
    db.cursor.execute(f"SELECT room_id, name FROM rooms")
    room_list = db.cursor.fetchall()
    room_names = ["Quit"] + [name for _, name in room_list]

    user_id = name_dict["id"]
    user_name = name_dict["value"]

    db.cursor.execute(f"SELECT {user_id}, event_name FROM reservations")
    reservation_list = db.cursor.fetchall()
    reservation_names = [name for _, name in reservation_list]

    if reservation_list == []:
        # make new reservation
        if room_names != []:
            event_name = _set_event_name()
            room = _get_room(room_names, user_name)
            room_id = room["id"]
            start_date = _set_date()
            attendees_count = _get_attendees_count()


def validate_datetime(date: str):
    try:
        datetime.strptime(date, "%Y-%m-%d")
        return True
    except ValueError:
        return "Use this format `YYYY-MM-DD`."


def _get_room(room_names: list[str], user_name: str) -> dict[str, str | int] | None:
    room_name = questionary.select(
        f"Hello {user_name} please select a room for your first reservation", room_names
    ).ask()
    return get_room_by_name(room_name)


def _get_attendees_count() -> str:
    attendees_count = questionary.text(
        "How many people will be attending?", "30", crud.integer_validator
    ).ask()
    return attendees_count


def _set_event_name():
    event_name = questionary.text("What is your event called").ask()
    return event_name


def _set_date() -> str | None:
    date = questionary.text("What day would the event start")
