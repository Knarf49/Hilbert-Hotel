import sys
import os
from typing import Optional

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
        self.mod_n_system: Optional[Any] = None
        self.migration_history = []

    def run(self):
        while True:
            print("\n" + "=" * 50)
            print("Distributed Hilbert's Hotel Management Console")
            print("=" * 50)
            print("1. Initialize System")
            print("2. Add Guests (Single / Batch)")
            print("3. Remove Guest")
            print("4. Add / Remove Building")
            print("5. Bidirectional Search")
            print("6. List Occupied Rooms")
            print("7. Load Balance Analysis")
            print("8. Run Performance Benchmarks")
            print("9. Compare with Hash Mod N")
            print("10. Export Data to CSV")
            print("0. Exit")
            print("=" * 50)

            choice = input("Select an option (0-10): ").strip()
            if choice == "0":
                print("Exiting application. Goodbye.")
                break
            elif choice == "1":
                self.handle_init()
            elif choice == "2":
                self.handle_add_guests()
            elif choice == "3":
                self.handle_remove_guest()
            elif choice == "4":
                self.handle_building_modification()
            elif choice == "5":
                self.handle_search()
            elif choice == "6":
                self.handle_list_rooms()
            elif choice == "7":
                self.handle_load_balance()
            elif choice == "8":
                self.handle_benchmarks()
            elif choice == "9":
                self.handle_compare_mod_n()
            elif choice == "10":
                self.handle_csv_export()
            else:
                print("Invalid selection. Please choose an option from 0 to 10.")

    def handle_init(self):
        if HotelSystem is None:
            print("Error: HotelSystem module is not implemented yet.")
            return

        try:
            n = int(input("Enter initial number of buildings (N >= 1): ").strip())
            v = int(input("Enter virtual nodes per building (V >= 1): ").strip())
            channels = int(input("Enter number of channels: ").strip())
            guests_per_c = int(input("Enter guests per channel: ").strip())

            if n < 1 or v < 1 or channels < 1 or guests_per_c < 0:
                print("Invalid input parameters. All numbers must be positive.")
                return

            self.system = HotelSystem(v_nodes=v)
            for i in range(n):
                self.system.add_building(f"Node_{i}")

            for c in range(1, channels + 1):
                for s in range(1, guests_per_c + 1):
                    if hasattr(self.system, "add_single_guest"):
                        self.system.add_single_guest(c, s)
                    elif hasattr(self.system, "add_guest"):
                        self.system.add_guest(c, s)

            print(f"System successfully initialized with {n} buildings and {channels * guests_per_c} guests.")
        except ValueError:
            print("Invalid input. Please enter valid integers.")

    def handle_add_guests(self):
        if self.system is None:
            print("Please initialize the system first (Option 1).")
            return

        mode = input("Choose addition mode: (1) Single, (2) Batch: ").strip()
        try:
            if mode == "1":
                c = int(input("Channel ID (c >= 1): ").strip())
                s = int(input("Sequence ID (s >= 1): ").strip())
                if hasattr(self.system, "add_single_guest"):
                    success = self.system.add_single_guest(c, s)
                elif hasattr(self.system, "add_guest"):
                    success = self.system.add_guest(c, s)
                else:
                    success = False
                if success:
                    print(f"Guest ({c}, {s}) added successfully.")
                else:
                    print(f"Failed to add guest ({c}, {s}). Guest might already exist.")
            elif mode == "2":
                c = int(input("Channel ID (c >= 1): ").strip())
                s_start = int(input("Starting sequence ID (s_start >= 1): ").strip())
                count = int(input("Guest count: ").strip())
                if hasattr(self.system, "add_guest_batch"):
                    success = self.system.add_guest_batch(c, s_start, count)
                else:
                    success = False
                if success:
                    print(f"Batch of {count} guests added successfully.")
                else:
                    print("Batch rejected. Conflict detected with existing guests.")
            else:
                print("Invalid mode selected.")
        except ValueError:
            print("Invalid input format.")

    def handle_remove_guest(self):
        if self.system is None:
            print("Please initialize the system first.")
            return

        try:
            c = int(input("Enter Channel ID (c): ").strip())
            s = int(input("Enter Sequence ID (s): ").strip())
            if hasattr(self.system, "remove_guest"):
                success = self.system.remove_guest(c, s)
                if success:
                    print(f"Guest ({c}, {s}) removed successfully.")
                else:
                    print(f"Guest ({c}, {s}) not found.")
            else:
                print("Remove function not supported by core system yet.")
        except ValueError:
            print("Invalid numerical input.")

    def handle_building_modification(self):
        if self.system is None:
            print("Please initialize the system first.")
            return

        action = input("Choose action: (1) Add Building, (2) Remove Building: ").strip()
        b_id = input("Enter Building Node ID: ").strip()

        if action == "1":
            success, migrations, rate = self.system.add_building(b_id)
            if success:
                self.migration_history.extend(migrations)
                print(f"Building {b_id} added. Moved guests: {len(migrations)}, Migration Rate: {rate:.4f}")
            else:
                print(f"Cannot add building {b_id}. Node ID already exists.")
        elif action == "2":
            success, migrations, rate = self.system.remove_building(b_id)
            if success:
                self.migration_history.extend(migrations)
                print(f"Building {b_id} removed. Moved guests: {len(migrations)}, Migration Rate: {rate:.4f}")
            else:
                print(f"Cannot remove building {b_id}. Node does not exist or system has only 1 building.")
        else:
            print("Invalid action.")

    def handle_search(self):
        if self.system is None:
            print("Please initialize the system first.")
            return

        mode = input("Search by: (1) Guest ID (c, s), (2) Location (node_id, room_no): ").strip()
        try:
            if mode == "1":
                c = int(input("Channel ID: ").strip())
                s = int(input("Sequence ID: ").strip())
                res = None
                if hasattr(self.system, "search_by_guest"):
                    res = self.system.search_by_guest(c, s)
                elif hasattr(self.system, "index_manager"):
                    res = self.system.index_manager.search_by_guest(c, s)
                if res:
                    print(f"Found: Node ID = {res[0]}, Room No = {res[1]}")
                else:
                    print("Guest Not Found.")
            elif mode == "2":
                node_id = input("Building Node ID: ").strip()
                room_no = int(input("Room Number: ").strip())
                res = None
                if hasattr(self.system, "search_by_room"):
                    res = self.system.search_by_room(node_id, room_no)
                elif hasattr(self.system, "index_manager"):
                    res = self.system.index_manager.search_by_room(node_id, room_no)
                if res:
                    print(f"Found: Channel ID = {res[0]}, Sequence ID = {res[1]}")
                else:
                    print("Room Not Found / Unoccupied.")
            else:
                print("Invalid search mode.")
        except ValueError:
            print("Invalid input format.")

    def handle_list_rooms(self):
        if self.system is None:
            print("Please initialize the system first.")
            return

        if hasattr(self.system, "list_occupied_rooms"):
            rooms = self.system.list_occupied_rooms()
            print(f"Total Occupied Rooms: {len(rooms)}")
            for item in rooms[:50]:
                print(item)
            if len(rooms) > 50:
                print(f"... and {len(rooms) - 50} more rooms (see CSV export for complete listing).")
        else:
            print("list_occupied_rooms is not available yet.")

    def handle_load_balance(self):
        if self.system is None:
            print("Please initialize the system first.")
            return

        if hasattr(self.system, "get_load_balance_stats"):
            stats = self.system.get_load_balance_stats()
            print("-" * 40)
            print("Load Balance Statistics:")
            print(f"Max Guests per Node: {stats.get('max')}")
            print(f"Min Guests per Node: {stats.get('min')}")
            print(f"Mean Guests per Node: {stats.get('mean'):.2f}")
            print(f"Std Deviation: {stats.get('std'):.4f}")
            print(f"Coefficient of Variation (CV): {stats.get('cv')}")
            print("-" * 40)
        else:
            print("get_load_balance_stats is not implemented yet.")

    def handle_benchmarks(self):
        if ExperimentRunner is None:
            print("ExperimentRunner module is not available.")
            return

        runner = ExperimentRunner()
        exp = input("Choose benchmark to run: (A) Data Size, (B) Mod N Comparison, (C) Virtual Nodes: ").strip().upper()
        try:
            if exp == "A":
                print("Running Experiment A...")
                res = runner.run_experiment_a([1000, 5000])
                print(res)
            elif exp == "B":
                print("Running Experiment B...")
                res = runner.run_experiment_b([5, 10])
                print(res)
            elif exp == "C":
                print("Running Experiment C...")
                res = runner.run_experiment_c([1, 8])
                print(res)
            else:
                print("Invalid experiment option.")
        except Exception as e:
            print(f"Benchmark error: {e}")

    def handle_compare_mod_n(self):
        if ModNHotelSystem is None or HotelSystem is None:
            print("ModNHotelSystem or HotelSystem not available.")
            return

        try:
            n = int(input("Number of buildings (N): ").strip())
            k = int(input("Number of guests (K): ").strip())
            runner = ExperimentRunner()
            guest_list = runner.generate_guest_batch(k)

            ch_sys = HotelSystem(v_nodes=32)
            mod_sys = ModNHotelSystem()

            for i in range(n):
                ch_sys.add_building(f"Node_{i}")
                mod_sys.add_building(f"Node_{i}")

            for c, s in guest_list:
                if hasattr(ch_sys, "add_single_guest"):
                    ch_sys.add_single_guest(c, s)
                elif hasattr(ch_sys, "add_guest"):
                    ch_sys.add_guest(c, s)

            _, _, ch_rate = ch_sys.add_building("New_Node")
            before_mod = [mod_sys.get_node(f"guest:{c}:{s}") for c, s in guest_list]
            mod_sys.add_building("New_Node")
            after_mod = [mod_sys.get_node(f"guest:{c}:{s}") for c, s in guest_list]
            mod_moved = sum(1 for a, b in zip(before_mod, after_mod) if a != b)
            mod_rate = mod_moved / k if k > 0 else 0.0

            print("-" * 40)
            print(f"Comparison on Adding Building (N={n} -> N={n+1}, K={k}):")
            print(f"Consistent Hashing Migration Rate: {ch_rate:.4f}")
            print(f"Naive Mod N Migration Rate:        {mod_rate:.4f}")
            print("-" * 40)
        except ValueError:
            print("Invalid input.")

    def handle_csv_export(self):
        if CSVExporter is None:
            print("CSVExporter module is not available.")
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
            print("Exported migrations to output/migrations.csv")
        else:
            print("No migration history recorded yet.")


if __name__ == "__main__":
    cli = HotelCLI()
    cli.run()
