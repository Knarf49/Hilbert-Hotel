import sys
import os
from typing import Optional, Any
import questionary

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
            "1. Initialize System": self.handle_init,
            "2. Add Guests (Single / Batch)": self.handle_add_guests,
            "3. Remove Guest": self.handle_remove_guest,
            "4. Add / Remove Building": self.handle_building_modification,
            "5. Bidirectional Search": self.handle_search,
            "6. List Occupied Rooms": self.handle_list_rooms,
            "7. Load Balance Analysis": self.handle_load_balance,
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

    def handle_init(self):
        if HotelSystem is None:
            print("Error: HotelSystem module not available.")
            return

        n = questionary.text("Number of buildings (N >= 1):", default="10").ask()
        v = questionary.text("Virtual nodes per building (V >= 1):", default="32").ask()
        channels = questionary.text("Number of channels (c):", default="10").ask()
        guests = questionary.text("Guests per channel:", default="100").ask()

        try:
            n_val, v_val, c_val, g_val = int(n), int(v), int(channels), int(guests)
            if n_val < 1 or v_val < 1 or c_val < 1 or g_val < 0:
                print("Values must be positive integers.")
                return

            self.system = HotelSystem(v_nodes=v_val)
            for i in range(n_val):
                self.system.add_building(f"Node_{i}")

            for c in range(1, c_val + 1):
                for s in range(1, g_val + 1):
                    if hasattr(self.system, "add_single_guest"):
                        self.system.add_single_guest(c, s)
                    elif hasattr(self.system, "add_guest"):
                        self.system.add_guest(c, s)

            print(f"System initialized with {n_val} buildings and {c_val * g_val} guests.")
        except (ValueError, TypeError):
            print("Invalid input numbers.")

    def handle_add_guests(self):
        if not self.system:
            print("Please initialize system first.")
            return

        mode = questionary.select("Add mode:", choices=["Single Guest", "Batch Guests", "Back"]).ask()
        if mode == "Single Guest":
            c = questionary.text("Channel ID:").ask()
            s = questionary.text("Sequence ID:").ask()
            try:
                fn = getattr(self.system, "add_single_guest", getattr(self.system, "add_guest", None))
                ok = fn(int(c), int(s)) if fn else False
                print("Guest added." if ok else "Failed. Duplicate or invalid.")
            except (ValueError, TypeError):
                print("Invalid input.")
        elif mode == "Batch Guests":
            c = questionary.text("Channel ID:").ask()
            s_start = questionary.text("Start Sequence ID:").ask()
            count = questionary.text("Count:").ask()
            try:
                fn = getattr(self.system, "add_guest_batch", None)
                ok = fn(int(c), int(s_start), int(count)) if fn else False
                print("Batch added." if ok else "Batch rejected (collision detected).")
            except (ValueError, TypeError):
                print("Invalid input.")

    def handle_remove_guest(self):
        if not self.system:
            print("Please initialize system first.")
            return

        c = questionary.text("Channel ID:").ask()
        s = questionary.text("Sequence ID:").ask()
        try:
            fn = getattr(self.system, "remove_guest", None)
            ok = fn(int(c), int(s)) if fn else False
            print("Guest removed." if ok else "Guest not found.")
        except (ValueError, TypeError):
            print("Invalid input.")

    def handle_building_modification(self):
        if not self.system:
            print("Please initialize system first.")
            return

        action = questionary.select("Action:", choices=["Add Building", "Remove Building", "Back"]).ask()
        if action == "Back" or not action:
            return

        b_id = questionary.text("Building Node ID:").ask()
        if not b_id:
            return

        if action == "Add Building":
            ok, migs, rate = self.system.add_building(b_id)
            if ok:
                self.migration_history.extend(migs)
                print(f"Added {b_id}. Relocated: {len(migs)}, Rate: {rate:.4f}")
            else:
                print(f"Failed to add {b_id} (already exists).")
        else:
            ok, migs, rate = self.system.remove_building(b_id)
            if ok:
                self.migration_history.extend(migs)
                print(f"Removed {b_id}. Relocated: {len(migs)}, Rate: {rate:.4f}")
            else:
                print(f"Failed to remove {b_id} (not found or only 1 building left).")

    def handle_search(self):
        if not self.system:
            print("Please initialize system first.")
            return

        mode = questionary.select("Search by:", choices=["Guest ID (c, s)", "Room (node_id, room_no)", "Back"]).ask()
        if mode == "Guest ID (c, s)":
            c = questionary.text("Channel ID:").ask()
            s = questionary.text("Sequence ID:").ask()
            try:
                fn = getattr(self.system, "search_by_guest", None)
                if not fn and hasattr(self.system, "index_manager"):
                    fn = self.system.index_manager.search_by_guest
                res = fn(int(c), int(s)) if fn else None
                print(f"Location: Building {res[0]}, Room {res[1]}" if res else "Not Found.")
            except (ValueError, TypeError):
                print("Invalid input.")
        elif mode == "Room (node_id, room_no)":
            node_id = questionary.text("Building Node ID:").ask()
            room_no = questionary.text("Room Number:").ask()
            try:
                fn = getattr(self.system, "search_by_room", None)
                if not fn and hasattr(self.system, "index_manager"):
                    fn = self.system.index_manager.search_by_room
                res = fn(node_id, int(room_no)) if fn else None
                print(f"Guest: Channel {res[0]}, Sequence {res[1]}" if res else "Not Found.")
            except (ValueError, TypeError):
                print("Invalid input.")

    def handle_list_rooms(self):
        if not self.system:
            print("Please initialize system first.")
            return

        fn = getattr(self.system, "list_occupied_rooms", None)
        if fn:
            rooms = fn()
            print(f"Occupied Rooms ({len(rooms)} total):")
            for r in rooms[:30]:
                print(r)
            if len(rooms) > 30:
                print(f"... and {len(rooms) - 30} more.")
        else:
            print("Feature not implemented in core system.")

    def handle_load_balance(self):
        if not self.system:
            print("Please initialize system first.")
            return

        fn = getattr(self.system, "get_load_balance_stats", None)
        if fn:
            stats = fn()
            print("=" * 30)
            print(f"Max: {stats.get('max')}")
            print(f"Min: {stats.get('min')}")
            print(f"Mean: {stats.get('mean'):.2f}")
            print(f"Std: {stats.get('std'):.4f}")
            print(f"CV: {stats.get('cv')}")
            print("=" * 30)
        else:
            print("Feature not implemented.")

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
