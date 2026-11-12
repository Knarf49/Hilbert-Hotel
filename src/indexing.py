from src.guest import Guest


class GuestIndexManager:
    def __init__(self):
        # ค้นจากแขก: (c, s) -> (node_id, room_no, ตัวแขก)
        self.guest_to_location = {}
        # ค้นจากห้อง: (node_id, room_no) -> (c, s)
        self.location_to_guest = {}

    def search_by_guest(self, c, s):
        record = self.guest_to_location.get((c, s))
        if record:
            return record[0], record[1]
        return None

    def search_by_room(self, node_id, room_no):
        return self.location_to_guest.get((node_id, room_no))

    def add_guest(self, guest, node_id):
        guest_id = guest.guest_id
        if guest_id in self.guest_to_location:
            return False
        self.guest_to_location[guest_id] = (node_id, guest.room_no, guest)
        self.location_to_guest[(node_id, guest.room_no)] = guest_id
        return True

    def remove_guest(self, c, s):
        record = self.guest_to_location.get((c, s))
        if record is None:
            return None
        node_id, room_no, guest = record
        del self.guest_to_location[(c, s)]
        del self.location_to_guest[(node_id, room_no)]
        return record

    def validate_batch(self, channel_id, s_start, count):
        new_guests = []
        for s in range(s_start, s_start + count):
            if (channel_id, s) in self.guest_to_location:
                return None
            new_guests.append(Guest(channel_id, s))
        return new_guests

    def total_guests(self):
        return len(self.guest_to_location)