import math
from src.hash_ring import HashRing
from src.guest import Guest
from src.indexing import GuestIndexManager
from src.hotel_node import HotelNode, MigrationRecord

class HotelSystem:
    def __init__(self, v_nodes = 32, salt =""):
        self.ring = HashRing(v_nodes =  v_nodes, salt = salt)
        self.nodes = {}
        self.index_manager = GuestIndexManager()

    def add_building(self, node_id):
        if node_id in self.nodes:
            return False, [], 0.0

        self.nodes[node_id] = HotelNode(node_id)
        self.ring.add_node(node_id)
        migrations = []
        total_guests = len(self.index_manager.guest_to_location)

        for guest_id, (old_node, room_no, guest) in list(self.index_manager.guest_to_location.items()):
            target_node = self.ring.get_node(guest.guest_key)
            
            if target_node == node_id:
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
                        room_no=room_no
                    )
                )
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
                        room_no=room_no
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
                    room_no=room_no
                )
            )

        rate = len(migrations) / total_guests if total_guests > 0 else 0.0
        return True, migrations, rate

    def get_load_balance_stats(self):
        sorted_node_ids = sorted(self.nodes.keys())
        counts = [self.nodes[nid].guest_count for nid in sorted_node_ids]
        k = sum(counts)
        n = len(sorted_node_ids)

        if n == 0 or k == 0:
            return {
                "counts": counts,
                "total_guests": k,
                "max": 0,
                "min": 0,
                "mean": 0.0,
                "std": 0.0,
                "cv": "N/A"
            }

        mean = k / n
        variance = sum((x - mean) ** 2 for x in counts) / n
        std = math.sqrt(variance)
        cv = std / mean if mean > 0 else "N/A"

        return {
            "counts": counts,
            "total_guests": k,
            "max": max(counts),
            "min": min(counts),
            "mean": mean,
            "std": std,
            "cv": cv
        }

    def list_occupied_rooms(self):
        result = {}
        for node_id in sorted(self.nodes.keys()):
            node = self.nodes[node_id]
            sorted_guests = sorted(node.guests.values(), key = lambda g: g.room_no)
            result[node_id] = [
                {
                    "room_no": g.room_no,
                    "guest_id": (g.channel_id, g.sequence_id),
                    "name": getattr(g, "name", "")
                }
                for g in sorted_guests
            ]
        return result