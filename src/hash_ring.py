import hashlib
from bisect import bisect_left

class HashRing:
    def __init__(self, v_nodes: int = 10, salt: str = ""):
        self.v_nodes = v_nodes
        self.salt = salt
        self.ring: list[tuple[int, str, int]] = []  # เก็บ (position, node_id, j)
        self.position_to_node: dict[int, str] = {}
        self.node_to_positions: dict[str, list[int]] = {}

    @property
    def ring_positions(self) -> list[int]:
        """คืนค่าลิสต์ของพิกัดทั้งหมดบนวงแหวน"""
        return [entry[0] for entry in self.ring]
    
    @ring_positions.setter
    def ring_positions(self, positions: list[int]):
        """อนุญาตให้ชุดทดสอบ Mock พิกัดบนวงแหวนได้โดยตรง
        โดยสร้าง Dummy node_id และ j เพื่อให้สอดคล้องกับโครงสร้าง tuple ของ self.ring
        """
        # สร้าง Tuple สมมติ (pos, "mock_node", 0) ให้ตรงกับ Data Type ที่ self.ring ต้องการ
        self.ring = [(pos, "mock_node", 0) for pos in positions]
        
        # จัดการข้อมูลใน position_to_node เพื่อให้การค้นหา (get_node) ไม่พัง
        self.position_to_node = {pos: "mock_node" for pos in positions}

    def _hash(self, key: str) -> int:
        """แปลง Key + Salt เป็นเลข 64-bit Unsigned Integer ด้วย SHA-256"""
        data = f"{key}{self.salt}".encode("utf-8")
        digest = hashlib.sha256(data).hexdigest()
        return int(digest, 16) & 0xFFFFFFFFFFFFFFFF

    def add_node(self, node_id: str) -> bool:
        if node_id in self.node_to_positions:
            return False

        added_positions = []
        for j in range(self.v_nodes):
            vnode_key = f"node:{node_id}:{j}"
            pos = self._hash(vnode_key)

            self.position_to_node[pos] = node_id
            added_positions.append(pos)
            self.ring.append((pos, node_id, j))

        self.node_to_positions[node_id] = added_positions
        self.ring.sort()
        return True

    def remove_node(self, node_id: str) -> bool:
        if node_id not in self.node_to_positions:
            return False

        removed_positions = self.node_to_positions.pop(node_id)
        for pos in removed_positions:
            if pos in self.position_to_node:
                del self.position_to_node[pos]

        self.ring = [entry for entry in self.ring if entry[1] != node_id]
        return True

    def get_node(self, guest_key: str) -> str | None:
        if not self.ring:
            return None

        guest_pos = self._hash(guest_key)
        idx = bisect_left(self.ring, (guest_pos, "", 0))

        if idx == len(self.ring):
            idx = 0  # Clockwise Wrap-around

        return self.ring[idx][1]