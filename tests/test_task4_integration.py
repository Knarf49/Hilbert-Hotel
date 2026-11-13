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
        CSVExporter.export_migrations(str(out_file), records)

        with open(out_file, encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            assert len(reader) == 1
            assert reader[0]["old_node"] == "Node_0"
            assert reader[0]["new_node"] == "Node_1"
            assert reader[0]["channel_id"] == "1"
            assert reader[0]["sequence_id"] == "1"
            assert reader[0]["room_no"] == "1"

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

    def test_t4_5_experiment_runner_smoke(self):
        """T4.5: ExperimentRunner smoke tests across experiments A, B, and C."""
        runner = ExperimentRunner()
        res_a = runner.run_experiment_a([100])
        assert 100 in res_a
        assert "assignment_time_median" in res_a[100]
        assert "current_mem_mib_median" in res_a[100]
        assert res_a[100]["assignment_time_median"] > 0
        assert res_a[100]["current_mem_mib_median"] > 0

        res_b = runner.run_experiment_b([5], k=100, v=8)
        assert 5 in res_b
        assert "ch_add_rate_median" in res_b[5]
        assert res_b[5]["ch_add_rate_median"] > 0

        res_c = runner.run_experiment_c([1, 8], n=5, k=100)
        assert 1 in res_c
        assert 8 in res_c
        assert "cv_median" in res_c[1]
        assert "cv_median" in res_c[8]
        assert res_c[8]["cv_median"] > 0
