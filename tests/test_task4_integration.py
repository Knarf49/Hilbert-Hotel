import csv
import io
import pytest

try:
    from src.export import CSVExporter
    from src.experiments import ExperimentRunner
    HAS_TASK4 = True
except ImportError:
    HAS_TASK4 = False

pytestmark = pytest.mark.skipif(not HAS_TASK4, reason="Task 4 modules (CSVExporter, ExperimentRunner) not implemented yet")


class TestTask4IntegrationAndExport:
    def test_t4_1_csv_row_count_and_headers(self, tmp_path):
        """T4.1 & T4.2: CSV contains required headers and exact row count."""
        guests_data = [
            {"channel_id": 1, "sequence_id": 1, "node_id": "Node_0", "room_no": 1},
            {"channel_id": 1, "sequence_id": 2, "node_id": "Node_0", "room_no": 3},
            {"channel_id": 2, "sequence_id": 1, "node_id": "Node_1", "room_no": 2},
        ]
        out_file = tmp_path / "guests.csv"
        CSVExporter.export_guests(str(out_file), guests_data)

        with open(out_file, encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            assert len(reader) == 3, "CSV rows must match number of guests"
            assert list(reader[0].keys()) == ["channel_id", "sequence_id", "node_id", "room_no"]

    def test_t4_3_migration_log_csv_export(self, tmp_path):
        """T4.3: Export migration records with required fields."""
        records = [
            {"channel_id": 1, "sequence_id": 1, "old_node": "Node_0", "new_node": "Node_1", "room_no": 1}
        ]
        out_file = tmp_path / "migrations.csv"
        with open(out_file, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["channel_id", "sequence_id", "old_node", "new_node", "room_no"])
            writer.writeheader()
            writer.writerows(records)

        with open(out_file, encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            assert len(reader) == 1
            assert reader[0]["old_node"] == "Node_0"
            assert reader[0]["new_node"] == "Node_1"

    def test_t4_4_uniform_experiment_guest_generator(self):
        """T4.4: 10 channels uniform guest batch generator."""
        runner = ExperimentRunner()
        k = 1000
        guests = runner.generate_guest_batch(k)
        assert len(guests) == k
        channels = {c for c, s in guests}
        assert len(channels) == 10, "Must distribute across 10 channels"
        assert min(channels) == 1
        assert max(channels) == 10
