import math
from dataclasses import dataclass

@dataclass
class MigrationRecord:
    channel_id: int
    sequence_id: int
    old_node: str
    new_node: str
    room_no: int

    def __repr__(self) -> str:
        return f"MigrationRecord(Guest=({self.channel_id}, {self.sequence_id}), Move: '{self.old_node}' -> '{self.new_node}', Room: {self.room_no})"
class HotelNode:
    def __init__(self, node_id):
        self.node_id = node_id
        self.guests = {}

    def add_guest(self, guest):
        self.guests[guest.guest_id] = guest

    def remove_guest(self, guest_id):
        return self.guests.pop(guest_id, None)

    @property
    def guest_count(self):
        return len(self.guests)