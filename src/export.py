import csv
from typing import List, Dict, Any, Optional


class CSVExporter:
    @staticmethod
    def export_guests(filepath: str, guests_data: List[Dict[str, Any]]) -> None:
        fieldnames = ["channel_id", "sequence_id", "node_id", "room_no"]
        with open(filepath, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in guests_data:
                filtered_row = {k: row.get(k, "") for k in fieldnames}
                writer.writerow(filtered_row)

    @staticmethod
    def export_migrations(filepath: str, migrations_data: List[Dict[str, Any]]) -> None:
        fieldnames = ["channel_id", "sequence_id", "old_node", "new_node", "room_no"]
        with open(filepath, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in migrations_data:
                filtered_row = {k: row.get(k, "") for k in fieldnames}
                writer.writerow(filtered_row)

    @staticmethod
    def export_experiment_results(filepath: str, results_data: List[Dict[str, Any]], fieldnames: Optional[List[str]] = None) -> None:
        if not results_data:
            with open(filepath, mode="w", newline="", encoding="utf-8") as f:
                pass
            return

        if not fieldnames:
            fieldnames = list(results_data[0].keys())

        with open(filepath, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in results_data:
                writer.writerow(row)
