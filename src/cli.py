import sys
import os
from typing import Optional, Any
import questionary

from src.handlers.system import (
    handle_init,
    handle_search,
    handle_list_rooms,
    handle_load_balance,
)
from src.handlers.guest import handle_add_guests
from src.handlers.building import (
    handle_remove_guest,
    handle_building_modification,
)

try:
    from src.hotel_system import HotelSystem
except ImportError:
    HotelSystem = None

try:
    from src.mod_n_system import ModNHotelSystem
except ImportError:
    ModNHotelSystem = None

try:
    from src.experiments import ExperimentRunner
except ImportError:
    ExperimentRunner = None

try:
    from src.export import CSVExporter
except ImportError:
    CSVExporter = None


class HotelCLI:
    def __init__(self):
        self.system: Optional[Any] = None
        self.migration_history = []

    def run(self):
        menu = {
            "1. Initialize System": lambda: handle_init(self),
            "2. Add Guests (Single / Batch)": lambda: handle_add_guests(self),
            "3. Remove Guest": lambda: handle_remove_guest(self),
            "4. Add / Remove Building": lambda: handle_building_modification(self),
            "5. Bidirectional Search": lambda: handle_search(self),
            "6. List Occupied Rooms": lambda: handle_list_rooms(self),
            "7. Load Balance Analysis": lambda: handle_load_balance(self),
            "8. Run Performance Benchmarks": self.handle_benchmarks,
            "9. Compare with Hash Mod N": self.handle_compare_mod_n,
            "10. Export Data to CSV": self.handle_csv_export,
            "Exit": None,
        }

        while True:
            choice = questionary.select(
                "Distributed Hilbert's Hotel Console:",
                choices=list(menu.keys()),
            ).ask()

            if not choice or choice == "Exit":
                print("Exiting application.")
                break

            action = menu.get(choice)
            if action:
                action()

    def handle_benchmarks(self):
        if not ExperimentRunner:
            print("ExperimentRunner not available.")
            return

        exp = questionary.select("Choose Benchmark:", choices=["Exp A: Data Size", "Exp B: Mod N Comparison", "Exp C: Virtual Nodes", "Back"]).ask()
        runner = ExperimentRunner()
        if exp == "Exp A: Data Size":
            print(runner.run_experiment_a([1000, 5000]))
        elif exp == "Exp B: Mod N Comparison":
            print(runner.run_experiment_b([5, 10]))
        elif exp == "Exp C: Virtual Nodes":
            print(runner.run_experiment_c([1, 8]))

    def handle_compare_mod_n(self):
        if not ModNHotelSystem or not HotelSystem or not ExperimentRunner:
            print("Required modules not ready.")
            return

        n_str = questionary.text("Building count (N):", default="10").ask()
        k_str = questionary.text("Guest count (K):", default="1000").ask()
        try:
            n, k = int(n_str), int(k_str)
            runner = ExperimentRunner()
            guest_list = runner.generate_guest_batch(k)
            ch_sys = HotelSystem(v_nodes=32)
            mod_sys = ModNHotelSystem()

            for i in range(n):
                ch_sys.add_building(f"Node_{i}")
                mod_sys.add_building(f"Node_{i}")

            for c, s in guest_list:
                fn = getattr(ch_sys, "add_single_guest", getattr(ch_sys, "add_guest", None))
                if fn:
                    fn(c, s)

            _, _, ch_rate = ch_sys.add_building("New_Node")
            b_mod = [mod_sys.get_node(f"guest:{c}:{s}") for c, s in guest_list]
            mod_sys.add_building("New_Node")
            a_mod = [mod_sys.get_node(f"guest:{c}:{s}") for c, s in guest_list]
            mod_rate = sum(1 for x, y in zip(b_mod, a_mod) if x != y) / k if k > 0 else 0.0

            print(f"Consistent Hashing Rate: {ch_rate:.4f}")
            print(f"Hash Mod N Rate:         {mod_rate:.4f}")
        except (ValueError, TypeError):
            print("Invalid input.")

    def handle_csv_export(self):
        if not CSVExporter:
            print("CSVExporter not available.")
            return

        os.makedirs("output", exist_ok=True)
        if self.migration_history:
            mig_data = [
                {
                    "channel_id": getattr(m, "channel_id", ""),
                    "sequence_id": getattr(m, "sequence_id", ""),
                    "old_node": getattr(m, "old_node", ""),
                    "new_node": getattr(m, "new_node", ""),
                    "room_no": getattr(m, "room_no", ""),
                }
                for m in self.migration_history
            ]
            CSVExporter.export_migrations("output/migrations.csv", mig_data)
            print("Exported to output/migrations.csv")
        else:
            print("No migrations recorded yet.")


if __name__ == "__main__":
    HotelCLI().run()
