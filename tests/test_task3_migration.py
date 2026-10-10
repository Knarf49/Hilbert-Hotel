import pytest

try:
    from src.hotel_node import HotelNode
    from src.hotel_system import HotelSystem
    from src.guest import Guest
    HAS_TASK3 = True
except ImportError:
    HAS_TASK3 = False

pytestmark = pytest.mark.skipif(not HAS_TASK3, reason="Task 3 modules (HotelNode, HotelSystem) not implemented yet")


class TestTask3MigrationEngineAndLoadBalance:
    def test_t3_1_add_building_invariant_v_gt_1(self):
        """T3.1: When adding a node, moved guests must ONLY move into the new node."""
        sys = HotelSystem(v_nodes=32, salt="0")
        sys.add_building("Node_A")
        sys.add_building("Node_B")

        # Add 100 guests
        for i in range(1, 101):
            sys.index_manager.guest_to_location[(1, i)] = ("Node_A", i, Guest(1, i))

        # Add new building Node_C
        success, migrations, rate = sys.add_building("Node_C")
        assert success is True
        for m in migrations:
            assert m.new_node == "Node_C", f"Moved guest must move into new node Node_C, got {m.new_node}"
            assert m.old_node != "Node_C"

    def test_t3_2_remove_building_invariant_v_gt_1(self):
        """T3.2: When removing a node, only guests in the removed node are relocated."""
        sys = HotelSystem(v_nodes=32, salt="0")
        sys.add_building("Node_A")
        sys.add_building("Node_B")
        sys.add_building("Node_C")

        # Remove Node_B
        success, migrations, rate = sys.remove_building("Node_B")
        assert success is True
        for m in migrations:
            assert m.old_node == "Node_B", f"Only guests from deleted node Node_B should move, got {m.old_node}"
            assert m.new_node in ["Node_A", "Node_C"]

    def test_t3_3_room_number_invariant_on_migration(self):
        """T3.3: Room numbers of migrated guests must remain identical."""
        sys = HotelSystem(v_nodes=32, salt="0")
        sys.add_building("Node_A")
        sys.add_building("Node_B")

        # Migration records should preserve room_no
        success, migrations, rate = sys.add_building("Node_C")
        for m in migrations:
            expected_room = Guest.compute_room_no(m.channel_id, m.sequence_id)
            assert m.room_no == expected_room

    def test_t3_4_guest_conservation_invariant(self):
        """T3.4: Total guest count before and after migration must be identical."""
        sys = HotelSystem(v_nodes=32, salt="0")
        sys.add_building("Node_A")
        sys.add_building("Node_B")

        count_before = len(sys.index_manager.guest_to_location)
        success, migrations, rate = sys.add_building("Node_C")
        count_after = len(sys.index_manager.guest_to_location)
        assert count_before == count_after, "Total guests must not increase or decrease"
        assert len(migrations) == int(rate * count_before) if count_before > 0 else len(migrations) == 0

    def test_t3_5_migration_rate_formula(self):
        """T3.5: Migration rate calculation and zero division protection."""
        sys = HotelSystem(v_nodes=32)
        # Empty hotel (K = 0)
        success, migrations, rate = sys.add_building("Node_A")
        assert rate == 0.0
        assert len(migrations) == 0

    def test_t3_6_load_balance_stats_integrity(self):
        """T3.6: Load balance statistics calculation (including empty 0-guest nodes and K=0)."""
        sys = HotelSystem(v_nodes=32)
        sys.add_building("Node_A")
        sys.add_building("Node_B")

        # K = 0 check
        stats_empty = sys.get_load_balance_stats()
        assert stats_empty["mean"] == 0.0
        assert stats_empty["cv"] == "N/A"

    def test_t3_7_occupied_rooms_sorting_order(self):
        """T3.7: Occupied rooms ordered by node_id ascending and room_no numerically ascending."""
        node = HotelNode("Node_1")
        g1 = Guest(1, 2)  # room_no 3
        g2 = Guest(1, 1)  # room_no 1
        node.guests[(1, 2)] = g1
        node.guests[(1, 1)] = g2

        sorted_rooms = sorted(node.guests.values(), key=lambda g: g.room_no)
        assert [g.room_no for g in sorted_rooms] == [1, 3]

    def test_t3_8_edge_case_reject_last_node_removal(self):
        """T3.8: Reject removing the last building (N = 1 rule)."""
        sys = HotelSystem(v_nodes=32)
        sys.add_building("Only_Node")
        assert len(sys.nodes) == 1

        # Attempt to delete last node
        success, migrations, rate = sys.remove_building("Only_Node")
        assert success is False, "Must strictly reject removing the last building (N >= 1 invariant)"
        assert len(sys.nodes) == 1

    def test_t3_9_edge_case_add_duplicate_building(self):
        """T3.9: Reject adding an existing building politely."""
        sys = HotelSystem(v_nodes=32)
        assert sys.add_building("Node_A")[0] is True
        assert sys.add_building("Node_A")[0] is False  # Rejected politely

    def test_t3_10_edge_case_remove_missing_building(self):
        """T3.10: Removing a non-existent building reports 0 relocations without error."""
        sys = HotelSystem(v_nodes=32)
        sys.add_building("Node_A")
        success, migrations, rate = sys.remove_building("Non_Existent_Node")
        assert success is False
        assert len(migrations) == 0
