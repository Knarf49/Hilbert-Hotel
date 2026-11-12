import os
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


def handle_init(cli):
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

        cli.system = HotelSystem(v_nodes=v_val)
        for i in range(n_val):
            cli.system.add_building(f"Node_{i}")

        for c in range(1, c_val + 1):
            for s in range(1, g_val + 1):
                if hasattr(cli.system, "add_single_guest"):
                    cli.system.add_single_guest(c, s)
                elif hasattr(cli.system, "add_guest"):
                    cli.system.add_guest(c, s)

        print(f"System initialized with {n_val} buildings and {c_val * g_val} guests.")
    except (ValueError, TypeError):
        print("Invalid input numbers.")


def handle_load_balance(cli):
    if not cli.system:
        print("Please initialize system first.")
        return

    fn = getattr(cli.system, "get_load_balance_stats", None)
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


def handle_benchmarks(cli):
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


def handle_compare_mod_n(cli):
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


def handle_csv_export(cli):
    if not CSVExporter:
        print("CSVExporter not available.")
        return

    os.makedirs("output", exist_ok=True)
    if cli.migration_history:
        mig_data = [
            {
                "channel_id": getattr(m, "channel_id", ""),
                "sequence_id": getattr(m, "sequence_id", ""),
                "old_node": getattr(m, "old_node", ""),
                "new_node": getattr(m, "new_node", ""),
                "room_no": getattr(m, "room_no", ""),
            }
            for m in cli.migration_history
        ]
        CSVExporter.export_migrations("output/migrations.csv", mig_data)
        print("Exported to output/migrations.csv")
    else:
        print("No migrations recorded yet.")
