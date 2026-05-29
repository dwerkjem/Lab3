class RoomsCRUD:
    def __init__(self, db_path:str):
        self.db_path = db_path

    def create_room(self, room_name:str, capacity:int, day_rate_cents:int):
        print(self.db_path)