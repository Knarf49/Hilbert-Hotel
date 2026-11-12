import hashlib

class ModNHotelSystem:
    def __init__(self, salt: str = ""):
        self.salt = salt
        self.building_list: list[str] = []

    def _hash(self, key: str) -> int:
        """แปลง Key + Salt เป็นเลข 64-bit Unsigned Integer ด้วย SHA-256"""
        data = f"{key}{self.salt}".encode("utf-8")
        digest = hashlib.sha256(data).hexdigest()
        return int(digest, 16) & 0xFFFFFFFFFFFFFFFF

    def add_building(self, node_id: str) -> bool:
        if node_id in self.building_list:
            return False
        self.building_list.append(node_id)
        return True

    def remove_building(self, node_id: str) -> bool:
        if node_id not in self.building_list:
            return False
        self.building_list.remove(node_id)
        return True

    def assign(self, guest_key: str) -> str | None:
        if not self.building_list:
            return None
        idx = self._hash(guest_key) % len(self.building_list)
        return self.building_list[idx]