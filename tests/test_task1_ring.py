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
        assert h0 == ring_salt0._hash(key)

    def test_t1_3_virtual_node_placement(self):
        """T1.3: Virtual nodes created in format node:{id}:{j} with exactly V nodes."""
        v = 32
        ring = HashRing(v_nodes=v)
        node_id = "Building_A"
        assert ring.add_node(node_id) is True
        assert len(ring.ring_positions) == v
        assert len(ring.node_to_positions[node_id]) == v
        assert ring.add_node(node_id) is False

    def test_t1_4_mock_ring_100_lookup(self):
        """T1.4: Small mock ring size 100, V=1, nodes at A=20, B=50, C=80 (Section 9.1)."""
        ring = HashRing(v_nodes=1)
        ring.set_mock_ring([(20, "A", 0), (50, "B", 0), (80, "C", 0)])
        assert ring.get_node_at_pos(10) == "A"
        assert ring.get_node_at_pos(20) == "A"
        assert ring.get_node_at_pos(25) == "B"
        assert ring.get_node_at_pos(35) == "B"
        assert ring.get_node_at_pos(50) == "B"
        assert ring.get_node_at_pos(70) == "C"
        assert ring.get_node_at_pos(90) == "A"

    def test_t1_5_mock_ring_migration_dynamics(self):
        """T1.5: Mock ring migration transition tests (Section 9.1)."""
        guest_positions = [10, 20, 25, 35, 50, 70, 90]

        ring = HashRing(v_nodes=1)
        ring.set_mock_ring([(20, "A", 0), (50, "B", 0), (80, "C", 0)])
        initial_assign = [ring.get_node_at_pos(pos) for pos in guest_positions]
        assert initial_assign == ["A", "A", "B", "B", "B", "C", "A"]

        ring_d = HashRing(v_nodes=1)
        ring_d.set_mock_ring([(20, "A", 0), (35, "D", 0), (50, "B", 0), (80, "C", 0)])
        d_assign = [ring_d.get_node_at_pos(pos) for pos in guest_positions]
        assert d_assign == ["A", "A", "D", "D", "B", "C", "A"]

        moved_d = [(old, new) for old, new in zip(initial_assign, d_assign) if old != new]
        assert len(moved_d) == 2
        for _, new in moved_d:
            assert new == "D", "Moved guests must only move into new node D"

        ring_no_b = HashRing(v_nodes=1)
        ring_no_b.set_mock_ring([(20, "A", 0), (80, "C", 0)])
        no_b_assign = [ring_no_b.get_node_at_pos(pos) for pos in guest_positions]
        assert no_b_assign == ["A", "A", "C", "C", "C", "C", "A"]

        moved_b = [(old, new) for old, new in zip(initial_assign, no_b_assign) if old != new]
        assert len(moved_b) == 3
        for _, new in moved_b:
            assert new == "C"

    def test_t1_6_hash_collision_tie_breaker(self):
        """T1.6: Tie-breaker sorting tuple (position, node_id, j) when hashes collide."""
        ring = HashRing(v_nodes=1)
        ring.set_mock_ring([(100, "Node_B", 0), (100, "Node_A", 0)])
        assert ring.get_node_at_pos(100) == "Node_A"

    def test_t1_7_mod_n_array_order_preservation(self):
        """T1.7: Mod N array order preserved on add/remove building."""
        mod_sys = ModNHotelSystem()
        mod_sys.add_building("Node_A")
        mod_sys.add_building("Node_B")
        mod_sys.add_building("Node_C")
        assert mod_sys.building_list == ["Node_A", "Node_B", "Node_C"]

        assigned_node = mod_sys.get_node("guest:1:1")
        assert assigned_node in ["Node_A", "Node_B", "Node_C"]

        assert mod_sys.remove_building("Node_B") is True
        assert mod_sys.building_list == ["Node_A", "Node_C"]

        assert mod_sys.remove_building("Node_C") is True
        assert mod_sys.building_list == ["Node_A"]

        assert mod_sys.remove_building("Node_A") is False
        assert mod_sys.building_list == ["Node_A"]
