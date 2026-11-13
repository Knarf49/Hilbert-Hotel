import hashlib
from bisect import bisect_left


class HashRing:
    def __init__(self, v_nodes: int = 32, salt: str = ""):
        if not isinstance(v_nodes, int) or isinstance(v_nodes, bool) or v_nodes < 1:
            raise ValueError("v_nodes must be a positive integer")
        self.v_nodes = v_nodes
        self.salt = salt
        self.ring: list[tuple[int, str, int]] = []
        self.position_to_node: dict[int, str] = {}
        self.node_to_positions: dict[str, list[int]] = {}

    def _sync_position_to_node(self) -> None:
        self.position_to_node = {}
        for pos, node_id, _ in reversed(self.ring):
            self.position_to_node[pos] = node_id

    @property
    def ring_positions(self) -> list[int]:
        """Return list of all sorted ring positions."""
        return [entry[0] for entry in self.ring]

    @ring_positions.setter
    def ring_positions(self, positions: list[int]) -> None:
        """Allow mock positions on the ring while keeping sorted order."""
        self.ring = sorted((pos, "mock_node", idx) for idx, pos in enumerate(positions))
        self._sync_position_to_node()

    def set_mock_ring(self, entries: list[tuple[int, str, int]]) -> None:
        """Set explicit ring entries (position, node_id, j) for deterministic testing."""
        self.ring = sorted(entries)
        self.node_to_positions = {}
        for pos, node_id, _ in self.ring:
            self.node_to_positions.setdefault(node_id, []).append(pos)
        self._sync_position_to_node()

    def _hash(self, key: str) -> int:
        """Convert Key + Salt to 64-bit unsigned integer using SHA-256."""
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
            added_positions.append(pos)
            self.ring.append((pos, node_id, j))

        self.node_to_positions[node_id] = added_positions
        self.ring.sort()
        self._sync_position_to_node()
        return True

    def remove_node(self, node_id: str) -> bool:
        if node_id not in self.node_to_positions:
            return False

        self.node_to_positions.pop(node_id)
        self.ring = [entry for entry in self.ring if entry[1] != node_id]
        self._sync_position_to_node()
        return True

    def get_node_at_pos(self, guest_pos: int) -> str | None:
        if not self.ring:
            return None

        idx = bisect_left(self.ring, (guest_pos, "", 0))
        if idx == len(self.ring):
            idx = 0

        return self.ring[idx][1]

    def get_node(self, guest_key: str) -> str | None:
        if not self.ring:
            return None

        guest_pos = self._hash(guest_key)
        return self.get_node_at_pos(guest_pos)
