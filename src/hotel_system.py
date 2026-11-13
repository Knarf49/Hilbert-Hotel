import math
from src.hash_ring import HashRing
from src.guest import Guest
from src.indexing import GuestIndexManager
from src.hotel_node import HotelNode, MigrationRecord


class HotelSystem:
    def __init__(self, v_nodes: int = 32, salt: str = ""):
        self.ring = HashRing(v_nodes=v_nodes, salt=salt)
        self.nodes = {}
        self.index_manager = GuestIndexManager()

    def add_single_guest(self, channel_id: int, sequence_id: int) -> bool:
        if not self.nodes:
            return False
        try:
            guest = Guest(channel_id, sequence_id)
        except (ValueError, TypeError):
            return False

        if guest.guest_id in self.index_manager.guest_to_location:
            return False

        target_node = self.ring.get_node(guest.guest_key)
        if target_node is None or target_node not in self.nodes:
            return False

        if not self.index_manager.add_guest(guest, target_node):
            return False

        self.nodes[target_node].add_guest(guest)
        return True

    add_guest = add_single_guest

    def add_guest_batch(self, channel_id: int, s_start: int, count: int) -> bool:
        if not self.nodes:
            return False

        batch = self.index_manager.validate_batch(channel_id, s_start, count)
        if batch is None:
            return False

        for guest in batch:
            target_node = self.ring.get_node(guest.guest_key)
            if target_node is None or target_node not in self.nodes:
                return False
            self.index_manager.add_guest(guest, target_node)
            self.nodes[target_node].add_guest(guest)

        return True

    def remove_guest(self, channel_id: int, sequence_id: int) -> bool:
        record = self.index_manager.remove_guest(channel_id, sequence_id)
        if record is None:
            return False

        node_id, _, _ = record
        if node_id in self.nodes:
            self.nodes[node_id].remove_guest((channel_id, sequence_id))
        return True

    def search_by_guest(self, channel_id: int, sequence_id: int) -> tuple[str, int] | None:
        return self.index_manager.search_by_guest(channel_id, sequence_id)

    def search_by_room(self, node_id: str, room_no: int) -> tuple[int, int] | None:
        return self.index_manager.search_by_room(node_id, room_no)

    def add_building(self, node_id):
        if not isinstance(node_id, str) or not node_id.strip() or node_id in self.nodes:
            return False, [], 0.0

        self.nodes[node_id] = HotelNode(node_id)
        self.ring.add_node(node_id)
        migrations = []
        total_guests = len(self.index_manager.guest_to_location)

        for guest_id, (old_node, room_no, guest) in list(self.index_manager.guest_to_location.items()):
            target_node = self.ring.get_node(guest.guest_key)

            if target_node == node_id:
                if old_node in self.nodes:
                    self.nodes[old_node].remove_guest(guest_id)
                self.nodes[target_node].add_guest(guest)

                self.index_manager.guest_to_location[guest_id] = (target_node, room_no, guest)
                self.index_manager.location_to_guest.pop((old_node, room_no), None)
                self.index_manager.location_to_guest[(target_node, room_no)] = guest_id

                migrations.append(
                    MigrationRecord(
                        channel_id=guest.channel_id,
                        sequence_id=guest.sequence_id,
                        old_node=old_node,
                        new_node=target_node,
                        room_no=room_no,
                    )
                )

        rate = len(migrations) / total_guests if total_guests > 0 else 0.0
        return True, migrations, rate

    def remove_building(self, node_id):
        if node_id not in self.nodes:
            return False, [], 0.0

        if len(self.nodes) <= 1:
            return False, [], 0.0

        self.ring.remove_node(node_id)
        departing_node = self.nodes.pop(node_id)

        migrations = []
        total_guests = len(self.index_manager.guest_to_location)

        for guest_id, guest in list(departing_node.guests.items()):
            new_node = self.ring.get_node(guest.guest_key)
            room_no = guest.room_no

            self.nodes[new_node].add_guest(guest)

            self.index_manager.guest_to_location[guest_id] = (new_node, room_no, guest)
            self.index_manager.location_to_guest.pop((node_id, room_no), None)
            self.index_manager.location_to_guest[(new_node, room_no)] = guest_id

            migrations.append(
                MigrationRecord(
                    channel_id=guest.channel_id,
                    sequence_id=guest.sequence_id,
                    old_node=node_id,
                    new_node=new_node,
                    room_no=room_no,
                )
            )

        rate = len(migrations) / total_guests if total_guests > 0 else 0.0
        return True, migrations, rate

    def get_load_balance_stats(self):
        sorted_node_ids = sorted(self.nodes.keys())
        per_building = {nid: self.nodes[nid].guest_count for nid in sorted_node_ids}
        counts = list(per_building.values())
        k = sum(counts)
        n = len(sorted_node_ids)

        if n == 0 or k == 0:
            return {
                "per_building": per_building,
                "counts": counts,
                "total_guests": k,
                "max": 0,
                "min": 0,
                "mean": 0.0,
                "std": 0.0,
                "cv": "N/A",
            }

        mean = k / n
        variance = sum((x - mean) ** 2 for x in counts) / n
        std = math.sqrt(variance)
        cv = std / mean if mean > 0 else "N/A"

        return {
            "per_building": per_building,
            "counts": counts,
            "total_guests": k,
            "max": max(counts),
            "min": min(counts),
            "mean": mean,
            "std": std,
            "cv": cv,
        }

    def list_occupied_rooms(self):
        rooms = []
        for node_id in sorted(self.nodes.keys()):
            node = self.nodes[node_id]
            sorted_guests = sorted(node.guests.values(), key=lambda g: g.room_no)
            for g in sorted_guests:
                rooms.append(
                    {
                        "node_id": node_id,
                        "room_no": g.room_no,
                        "channel_id": g.channel_id,
                        "sequence_id": g.sequence_id,
                        "guest_id": (g.channel_id, g.sequence_id),
                    }
                )
        return rooms
