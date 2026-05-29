import questionary
from lab3.modules.crud.database import Database

db = Database()


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
            get_room_id(room_names, user_name)


def get_room_id(room_names, user_name):
    room_name = questionary.select(
        f"Hello {user_name} please select a room for your first reservation", room_names
    ).ask()
    return room_name
