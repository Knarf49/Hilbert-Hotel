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
        assert sys.add_guest_batch(1, 1, 100) is True

        success, migrations, rate = sys.add_building("Node_C")
        assert success is True
        assert len(migrations) > 0
        assert len({(m.channel_id, m.sequence_id) for m in migrations}) == len(migrations)
        for m in migrations:
            assert m.new_node == "Node_C", f"Moved guest must move into new node Node_C, got {m.new_node}"
            assert m.old_node != "Node_C"

    def test_t3_2_remove_building_invariant_v_gt_1(self):
        """T3.2: When removing a node, only guests in the removed node are relocated."""
        sys = HotelSystem(v_nodes=32, salt="0")
        sys.add_building("Node_A")
        sys.add_building("Node_B")
        sys.add_building("Node_C")
        assert sys.add_guest_batch(1, 1, 100) is True

        success, migrations, rate = sys.remove_building("Node_B")
        assert success is True
        assert len(migrations) > 0
        assert len({(m.channel_id, m.sequence_id) for m in migrations}) == len(migrations)
        for m in migrations:
            assert m.old_node == "Node_B", f"Only guests from deleted node Node_B should move, got {m.old_node}"
            assert m.new_node in ["Node_A", "Node_C"]

    def test_t3_3_room_number_invariant_on_migration(self):
        """T3.3: Room numbers of migrated guests must remain identical."""
        sys = HotelSystem(v_nodes=32, salt="0")
        sys.add_building("Node_A")
        sys.add_building("Node_B")
        assert sys.add_guest_batch(1, 1, 100) is True

        success, migrations, rate = sys.add_building("Node_C")
        assert success is True
        assert len(migrations) > 0
        assert len({(m.channel_id, m.sequence_id) for m in migrations}) == len(migrations)
        for m in migrations:
            expected_room = Guest.compute_room_no(m.channel_id, m.sequence_id)
            assert m.room_no == expected_room

    def test_t3_4_guest_conservation_invariant(self):
        """T3.4: Total guest count before and after migration must be identical."""
        sys = HotelSystem(v_nodes=32, salt="0")
        sys.add_building("Node_A")
        sys.add_building("Node_B")
        assert sys.add_guest_batch(1, 1, 100) is True

        count_before = len(sys.index_manager.guest_to_location)
        assert count_before == 100
        success, migrations, rate = sys.add_building("Node_C")
        count_after = len(sys.index_manager.guest_to_location)
        assert count_before == count_after, "Total guests must not increase or decrease"
        assert len(migrations) > 0
        assert len({(m.channel_id, m.sequence_id) for m in migrations}) == len(migrations)
        assert len(migrations) == round(rate * count_before)

    def test_t3_5_migration_rate_formula(self):
        """T3.5: Migration rate calculation and zero division protection."""
        sys = HotelSystem(v_nodes=32)
        success, migrations, rate = sys.add_building("Node_A")
        assert rate == 0.0
        assert len(migrations) == 0

    def test_t3_6_load_balance_stats_integrity(self):
        """T3.6: Load balance statistics calculation (including empty 0-guest nodes and K=0)."""
        sys = HotelSystem(v_nodes=32)
        sys.add_building("Node_A")
        sys.add_building("Node_B")

        stats_empty = sys.get_load_balance_stats()
        assert stats_empty["mean"] == 0.0
        assert stats_empty["cv"] == "N/A"
        assert stats_empty["total_guests"] == 0
        assert stats_empty["per_building"] == {"Node_A": 0, "Node_B": 0}

        sys.add_single_guest(1, 1)
        stats_single = sys.get_load_balance_stats()
        assert stats_single["total_guests"] == 1
        assert stats_single["min"] == 0
        assert stats_single["max"] == 1
        assert 0 in stats_single["per_building"].values()
        assert "per_building" in stats_single

        sys.add_building("Node_Empty")
        stats_with_empty = sys.get_load_balance_stats()
        assert "Node_Empty" in stats_with_empty["per_building"]
        assert isinstance(stats_with_empty["per_building"]["Node_Empty"], int)
        assert stats_with_empty["mean"] > 0.0
        assert isinstance(stats_with_empty["cv"], float)

        assert sys.add_guest_batch(2, 1, 50) is True
        stats_k = sys.get_load_balance_stats()
        assert stats_k["total_guests"] == 51
        assert len(stats_k["per_building"]) == 3
        assert isinstance(stats_k["cv"], float)

    def test_t3_7_occupied_rooms_sorting_order(self):
        """T3.7: Occupied rooms ordered by node_id ascending and room_no numerically ascending."""
        sys = HotelSystem(v_nodes=32, salt="0")
        sys.add_building("Node_B")
        sys.add_building("Node_A")
        sys.add_building("Node_C")
        assert sys.add_guest_batch(1, 1, 30) is True
        assert sys.add_guest_batch(2, 1, 30) is True

        rooms = sys.list_occupied_rooms()
        assert len(rooms) == 60
        for i in range(len(rooms) - 1):
            curr_r = rooms[i]
            next_r = rooms[i + 1]
            if curr_r["node_id"] == next_r["node_id"]:
                assert curr_r["room_no"] <= next_r["room_no"]
            else:
                assert curr_r["node_id"] < next_r["node_id"]

    def test_t3_8_edge_case_reject_last_node_removal(self):
        """T3.8: Reject removing the last building (N = 1 rule)."""
        sys = HotelSystem(v_nodes=32)
        sys.add_building("Only_Node")
        assert len(sys.nodes) == 1

        success, migrations, rate = sys.remove_building("Only_Node")
        assert success is False, "Must strictly reject removing the last building (N >= 1 invariant)"
        assert len(sys.nodes) == 1

    def test_t3_9_edge_case_add_duplicate_building(self):
        """T3.9: Reject adding an existing building politely."""
        sys = HotelSystem(v_nodes=32)
        assert sys.add_building("Node_A")[0] is True
        assert sys.add_building("Node_A")[0] is False

    def test_t3_10_edge_case_remove_missing_building(self):
        """T3.10: Removing a non-existent building reports 0 relocations without error."""
        sys = HotelSystem(v_nodes=32)
        sys.add_building("Node_A")
        success, migrations, rate = sys.remove_building("Non_Existent_Node")
        assert success is False
        assert len(migrations) == 0
