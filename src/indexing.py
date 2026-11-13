from src.guest import Guest


class GuestIndexManager:
    def __init__(self):
        self.guest_to_location = {}
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
        location = (node_id, guest.room_no)
        if guest_id in self.guest_to_location or location in self.location_to_guest:
            return False
        self.guest_to_location[guest_id] = (node_id, guest.room_no, guest)
        self.location_to_guest[location] = guest_id
        return True

    def remove_guest(self, c, s):
        record = self.guest_to_location.get((c, s))
        if record is None:
            return None
        node_id, room_no, guest = record
        del self.guest_to_location[(c, s)]
        self.location_to_guest.pop((node_id, room_no), None)
        return record

    def validate_batch(self, channel_id, s_start, count):
        if (
            not isinstance(channel_id, int)
            or isinstance(channel_id, bool)
            or not isinstance(s_start, int)
            or isinstance(s_start, bool)
            or not isinstance(count, int)
            or isinstance(count, bool)
        ):
            return None
        if channel_id < 1 or s_start < 1 or count < 0:
            return None
        if count == 0:
            return []

        new_guests = []
        for s in range(s_start, s_start + count):
            if (channel_id, s) in self.guest_to_location:
                return None
            new_guests.append(Guest(channel_id, s))
        return new_guests

    def total_guests(self):
        return len(self.guest_to_location)
