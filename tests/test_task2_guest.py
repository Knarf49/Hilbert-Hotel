import pytest

try:
    from src.guest import Guest
    from src.indexing import GuestIndexManager
    HAS_TASK2 = True
except ImportError:
    HAS_TASK2 = False

pytestmark = pytest.mark.skipif(not HAS_TASK2, reason="Task 2 modules (Guest, GuestIndexManager) not implemented yet")


class TestTask2GuestEntityAndIndex:
    def test_t2_1_cantor_pairing_standard_table(self):
        """T2.1: Cantor pairing standard table checks:
        (1, 1) -> 1, (2, 1) -> 2, (1, 2) -> 3, (3, 1) -> 4, (2, 2) -> 5
        """
        cases = [
            (1, 1, 1),
            (2, 1, 2),
            (1, 2, 3),
            (3, 1, 4),
            (2, 2, 5),
        ]
        for c, s, expected_room in cases:
            g = Guest(c, s)
            assert g.room_no == expected_room, f"Guest({c}, {s}) room must be {expected_room}, got {g.room_no}"
            assert isinstance(g.room_no, int), "Room number must be an integer (never float)"

    def test_t2_2_no_last_room_plus_one_invariant(self):
        """T2.2: Room numbers must be invariant to system guest state (no last_room + 1)."""
        g1 = Guest(1, 1)
        g2 = Guest(1, 2)
        assert g1.room_no == 1
        assert g2.room_no == 3
        g3 = Guest(2, 1)
        assert g1.room_no == 1
        assert g2.room_no == 3
        assert g3.room_no == 2

    def test_t2_3_arbitrary_large_id_safety(self):
        """T2.3: Large c and s values compute accurately without overflow."""
        g = Guest(channel_id=1000, sequence_id=50000)
        assert g.room_no > 0
        assert isinstance(g.room_no, int)

    def test_t2_4_bidirectional_index_o1(self):
        """T2.4: Bidirectional lookups (c, s) <-> (node, room) return consistent records."""
        manager = GuestIndexManager()
        g1 = Guest(1, 1)
        assert manager.add_guest(g1, "Node_A") is True

        res_forward = manager.search_by_guest(1, 1)
        assert res_forward == ("Node_A", g1.room_no)

        res_reverse = manager.search_by_room("Node_A", g1.room_no)
        assert res_reverse == (1, 1)

    def test_t2_5_atomic_batch_validation_and_rollback(self):
        """T2.5: Batch addition with duplicate guest rejects entire batch atomically."""
        manager = GuestIndexManager()
        g_existing = Guest(1, 3)
        assert manager.add_guest(g_existing, "Node_A") is True

        batch = manager.validate_batch(channel_id=1, s_start=1, count=5)
        assert batch is None, "Batch containing existing guest must return None (atomically rejected)"
        assert (1, 1) not in manager.guest_to_location
        assert (1, 2) not in manager.guest_to_location

        assert manager.validate_batch(channel_id=1, s_start=1, count=0) == []
        assert manager.validate_batch(channel_id=1, s_start=1, count=-1) is None
        assert manager.validate_batch(channel_id=0, s_start=1, count=5) is None
        with pytest.raises(ValueError):
            Guest(True, 1)
        with pytest.raises(ValueError):
            Guest.compute_room_no(0, 1)

    def test_t2_6_edge_case_duplicate_guest_rejection(self):
        """T2.6: Individual duplicate guest addition rejection."""
        manager = GuestIndexManager()
        g1 = Guest(2, 1)
        assert manager.add_guest(g1, "Node_A") is True
        assert manager.add_guest(g1, "Node_A") is False
        assert manager.add_guest(Guest(2, 1), "Node_B") is False
        assert (2, 1) in manager.guest_to_location

    def test_t2_7_edge_case_non_existent_search(self):
        """T2.7: Search non-existent guest or non-existent room returns None politely (no crash)."""
        manager = GuestIndexManager()
        assert manager.search_by_guest(999, 999) is None
        assert manager.search_by_room("Missing_Node", 99999) is None

    def test_t2_8_edge_case_remove_non_existent_guest(self):
        """T2.8: Removing non-existent guest does not cause KeyError or change counts."""
        manager = GuestIndexManager()
        assert manager.remove_guest(99, 99) is None
        assert (99, 99) not in manager.guest_to_location
        assert manager.total_guests() == 0

    def test_t2_9_clean_guest_removal(self):
        """T2.9: Removing a guest cleans both index directions completely."""
        manager = GuestIndexManager()
        g = Guest(1, 1)
        assert manager.add_guest(g, "Node_A") is True

        removed = manager.remove_guest(1, 1)
        assert removed is not None
        assert manager.search_by_guest(1, 1) is None
        assert manager.search_by_room("Node_A", g.room_no) is None
        assert manager.total_guests() == 0
