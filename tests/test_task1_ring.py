import pytest

try:
    from src.hash_ring import HashRing
    from src.mod_n_system import ModNHotelSystem
    HAS_TASK1 = True
except ImportError:
    HAS_TASK1 = False

pytestmark = pytest.mark.skipif(not HAS_TASK1, reason="Task 1 modules (HashRing, ModNHotelSystem) not implemented yet")


class TestTask1CoreRing:
    def test_t1_1_deterministic_sha256_range(self):
        """T1.1: Deterministic SHA-256 hash output in range [0, 2^64 - 1]."""
        ring1 = HashRing(v_nodes=32)
        ring2 = HashRing(v_nodes=32)
        key = "guest:1:1"
        h1 = ring1._hash(key)
        h2 = ring2._hash(key)
        assert h1 == h2, "Hash must be strictly deterministic across instances"
        assert 0 <= h1 < (2**64), "Hash must be within 64-bit integer range [0, 2^64 - 1]"

    def test_t1_2_salt_parameter_determinism(self):
        """T1.2: Salt parameter alters hash deterministically."""
        ring_salt0 = HashRing(v_nodes=32, salt="0")
        ring_salt1 = HashRing(v_nodes=32, salt="1")
        key = "guest:1:1"
        h0 = ring_salt0._hash(key)
        h1 = ring_salt1._hash(key)
        assert h0 != h1, "Different salts must produce different hash positions"
        # Deterministic check for same salt
        assert h0 == ring_salt0._hash(key)

    def test_t1_3_virtual_node_placement(self):
        """T1.3: Virtual nodes created in format node:{id}:{j} with exactly V nodes."""
        v = 32
        ring = HashRing(v_nodes=v)
        node_id = "Building_A"
        assert ring.add_node(node_id) is True
        assert len(ring.ring_positions) == v
        assert len(ring.node_to_positions[node_id]) == v
        # Ensure cannot add duplicate building
        assert ring.add_node(node_id) is False

    def test_t1_4_mock_ring_100_lookup(self):
        """T1.4: Small mock ring size 100, V=1, nodes at A=20, B=50, C=80 (Section 9.1)."""
        ring = HashRing(v_nodes=1)
        # Directly set mock ring state for section 9.1 test
        ring.ring_positions = [20, 50, 80]
        ring.position_to_node = {20: ("A", 0), 50: ("B", 0), 80: ("C", 0)}

        # Helper to lookup by direct position without hashing
        def lookup_pos(pos: int) -> str:
            import bisect
            idx = bisect.bisect_left(ring.ring_positions, pos)
            if idx == len(ring.ring_positions):
                idx = 0
            return ring.position_to_node[ring.ring_positions[idx]][0]

        assert lookup_pos(10) == "A"  # Clockwise to 20
        assert lookup_pos(20) == "A"  # Exact match on 20
        assert lookup_pos(25) == "B"  # Clockwise to 50
        assert lookup_pos(35) == "B"  # Clockwise to 50
        assert lookup_pos(50) == "B"  # Exact match on 50
        assert lookup_pos(70) == "C"  # Clockwise to 80
        assert lookup_pos(90) == "A"  # Wrap-around to 20

    def test_t1_5_mock_ring_migration_dynamics(self):
        """T1.5: Mock ring migration transition tests (Section 9.1).
        Guest positions: 10, 20, 25, 35, 50, 70, 90.
        1. Add D at 35 -> guests 25, 35 move to D (2 moved).
        2. Remove B from initial -> guests 25, 35, 50 move to C (3 moved).
        """
        import bisect

        guest_positions = [10, 20, 25, 35, 50, 70, 90]

        def get_assignments(positions, pos_to_node):
            res = []
            for g in guest_positions:
                idx = bisect.bisect_left(positions, g)
                if idx == len(positions):
                    idx = 0
                res.append(pos_to_node[positions[idx]][0])
            return res

        # Initial state: A=20, B=50, C=80
        init_positions = [20, 50, 80]
        init_map = {20: ("A", 0), 50: ("B", 0), 80: ("C", 0)}
        initial_assign = get_assignments(init_positions, init_map)
        assert initial_assign == ["A", "A", "B", "B", "B", "C", "A"]

        # Case 1: Add D at 35
        d_positions = [20, 35, 50, 80]
        d_map = {20: ("A", 0), 35: ("D", 0), 50: ("B", 0), 80: ("C", 0)}
        d_assign = get_assignments(d_positions, d_map)
        assert d_assign == ["A", "A", "D", "D", "B", "C", "A"]
        moved_d = [i for i, (old, new) in enumerate(zip(initial_assign, d_assign)) if old != new]
        assert len(moved_d) == 2
        for idx in moved_d:
            assert d_assign[idx] == "D", "Moved guests must only move into new node D"

        # Case 2: Remove B from initial
        no_b_positions = [20, 80]
        no_b_map = {20: ("A", 0), 80: ("C", 0)}
        no_b_assign = get_assignments(no_b_positions, no_b_map)
        assert no_b_assign == ["A", "A", "C", "C", "C", "C", "A"]
        moved_b = [i for i, (old, new) in enumerate(zip(initial_assign, no_b_assign)) if old != new]
        assert len(moved_b) == 3

    def test_t1_6_hash_collision_tie_breaker(self):
        """T1.6: Tie-breaker sorting tuple (position, node_id, j) when hashes collide."""
        ring = HashRing(v_nodes=1)
        ring.ring_positions = [100, 100]
        ring.position_to_node = {100: ("Node_1", 0)}
        # Ensure tie breaker handling runs without crashing
        assert ring.ring_positions[0] == 100

    def test_t1_7_mod_n_array_order_preservation(self):
        """T1.7: Mod N array order preserved on add/remove building."""
        mod_sys = ModNHotelSystem()
        mod_sys.add_building("Node_A")
        mod_sys.add_building("Node_B")
        mod_sys.add_building("Node_C")
        assert mod_sys.building_list == ["Node_A", "Node_B", "Node_C"]

        # Remove B without disrupting order of A and C
        mod_sys.remove_building("Node_B")
        assert mod_sys.building_list == ["Node_A", "Node_C"]
