import os
import questionary
from src.handlers import print_box

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
        print_box("Error: HotelSystem module not available.", title="ERROR")
        return

    n = questionary.text("Number of buildings (N >= 1):", default="10").ask()
    v = questionary.text("Virtual nodes per building (V >= 1):", default="32").ask()
    channels = questionary.text("Number of channels (c):", default="10").ask()
    guests = questionary.text("Guests per channel:", default="100").ask()

    try:
        n_val, v_val, c_val, g_val = int(n), int(v), int(channels), int(guests)
        if n_val < 1 or v_val < 1 or c_val < 1 or g_val < 0:
            print_box("Values must be positive integers.", title="ERROR")
            return

        cli.system = HotelSystem(v_nodes=v_val)
        cli.migration_history = []

        for i in range(n_val):
            cli.system.add_building(f"Node_{i}")

        if g_val > 0:
            for c in range(1, c_val + 1):
                cli.system.add_guest_batch(c, 1, g_val)

        total_guests = cli.system.index_manager.total_guests()
        print_box(
            f"System initialized with {n_val} buildings and {total_guests} total guests.",
            title="INITIALIZE SYSTEM",
        )
    except (ValueError, TypeError):
        print_box("Invalid input numbers.", title="ERROR")


def handle_load_balance(cli):
    if not cli.system:
        print_box("Please initialize system first.", title="WARNING")
        return

    stats = cli.system.get_load_balance_stats()
    per_building = stats.get("per_building", {})
    lines = ["Guest count per building:"]
    for node_id, count in per_building.items():
        lines.append(f"  {node_id}: {count}")
    lines.append("-" * 35)
    lines.append(f"Total Guests: {stats.get('total_guests', 0)}")
    lines.append(f"Max: {stats.get('max')}")
    lines.append(f"Min: {stats.get('min')}")
    mean = stats.get("mean")
    lines.append(f"Mean: {mean:.2f}" if isinstance(mean, (int, float)) else f"Mean: {mean}")
    std = stats.get("std")
    lines.append(f"Std: {std:.4f}" if isinstance(std, (int, float)) else f"Std: {std}")
    cv = stats.get("cv")
    lines.append(f"CV: {cv:.4f}" if isinstance(cv, (int, float)) else f"CV: {cv}")
    print_box(lines, title="LOAD BALANCE")


def handle_benchmarks(cli):
    if not ExperimentRunner:
        print_box("ExperimentRunner not available.", title="ERROR")
        return

    exp = questionary.select(
        "Choose Benchmark:",
        choices=[
            "Exp A: Data Size",
            "Exp B: Mod N Comparison",
            "Exp C: Virtual Nodes",
            "Run All & Export CSVs + Graphs",
            "Back",
        ],
    ).ask()
    if not exp or exp == "Back":
        return

    runner = ExperimentRunner()
    if exp == "Exp A: Data Size":
        res = runner.run_experiment_a([1000, 10000, 100000])
        lines = ["Experiment A Medians (N=10, V=32, 3 salts):"]
        for k, d in sorted(res.items()):
            lines.append(
                f"  K={k:,}: ring={d['ring_build_time_median']:.5f}s, "
                f"assign={d['assignment_time_median']:.4f}s, "
                f"sort={d['sort_time_median']:.4f}s, "
                f"peak={d['peak_mem_mib_median']:.2f} MiB"
            )
        print_box(lines, title="BENCHMARK - EXP A")
    elif exp == "Exp B: Mod N Comparison":
        res = runner.run_experiment_b([5, 10, 20])
        lines = ["Experiment B Medians (K=10,000, V=32, 3 salts):"]
        for n, d in sorted(res.items()):
            lines.append(
                f"  N={n}: Add CH={d['ch_add_rate_median']:.4f} vs ModN={d['mod_add_rate_median']:.4f} | "
                f"Rem CH={d['ch_rem_rate_median']:.4f} vs ModN={d['mod_rem_rate_median']:.4f}"
            )
        print_box(lines, title="BENCHMARK - EXP B")
    elif exp == "Exp C: Virtual Nodes":
        res = runner.run_experiment_c([1, 8, 32])
        lines = ["Experiment C Medians (N=10, K=10,000, 3 salts):"]
        for v, d in sorted(res.items()):
            lines.append(
                f"  V={v}: CV={d['cv_median']:.4f}, "
                f"peak={d['peak_mem_mib_median']:.2f} MiB, "
                f"add_rate={d['add_rate_median']:.4f}"
            )
        print_box(lines, title="BENCHMARK - EXP C")
    elif exp == "Run All & Export CSVs + Graphs":
        runner.run_all_and_export("output")
        print_box(
            [
                "Benchmarks completed. Exported files to output/:",
                "  - experiment_a.csv, experiment_b.csv, experiment_c.csv",
                "  - guests.csv, migrations.csv",
                "  - graph_a.png, graph_b.png, graph_c.png",
            ],
            title="BENCHMARK EXPORT",
        )


def handle_compare_mod_n(cli):
    if not ModNHotelSystem or not HotelSystem or not ExperimentRunner:
        print_box("Required modules not ready.", title="ERROR")
        return

    n_str = questionary.text("Building count (N >= 2):", default="10").ask()
    k_str = questionary.text("Guest count (K >= 0):", default="1000").ask()
    try:
        n, k = int(n_str), int(k_str)
        if n < 2 or k < 0:
            print_box("Validation failed: N must be >= 2 and K must be >= 0.", title="ERROR")
            return

        runner = ExperimentRunner()
        guest_list = runner.generate_guest_batch(k) if k > 0 else []

        ch_add_sys = HotelSystem(v_nodes=32)
        mod_add_sys = ModNHotelSystem()
        for i in range(n):
            b_id = f"Node_{i}"
            ch_add_sys.add_building(b_id)
            mod_add_sys.add_building(b_id)

        for c, s in guest_list:
            ch_add_sys.add_single_guest(c, s)

        mod_init_assign = [mod_add_sys.get_node(f"guest:{c}:{s}") for c, s in guest_list]
        _, ch_add_migs, ch_add_rate = ch_add_sys.add_building(f"Node_{n}")
        mod_add_sys.add_building(f"Node_{n}")
        mod_after_add = [mod_add_sys.get_node(f"guest:{c}:{s}") for c, s in guest_list]

        ch_add_moved = len(ch_add_migs)
        mod_add_moved = sum(1 for a, b in zip(mod_init_assign, mod_after_add) if a != b)
        mod_add_rate = mod_add_moved / k if k > 0 else 0.0

        ch_rem_sys = HotelSystem(v_nodes=32)
        mod_rem_sys = ModNHotelSystem()
        for i in range(n):
            b_id = f"Node_{i}"
            ch_rem_sys.add_building(b_id)
            mod_rem_sys.add_building(b_id)

        for c, s in guest_list:
            ch_rem_sys.add_single_guest(c, s)

        mod_rem_init = [mod_rem_sys.get_node(f"guest:{c}:{s}") for c, s in guest_list]
        _, ch_rem_migs, ch_rem_rate = ch_rem_sys.remove_building("Node_0")
        mod_rem_sys.remove_building("Node_0")
        mod_rem_after = [mod_rem_sys.get_node(f"guest:{c}:{s}") for c, s in guest_list]

        ch_rem_moved = len(ch_rem_migs)
        mod_rem_moved = sum(1 for a, b in zip(mod_rem_init, mod_rem_after) if a != b)
        mod_rem_rate = mod_rem_moved / k if k > 0 else 0.0

        lines = [f"Add 1 Building ({n} -> {n + 1}):"]
        if k > 0:
            lines.append(f"  Consistent Hashing: Moved = {ch_add_moved}, Rate = {ch_add_rate:.4f}")
            lines.append(f"  Hash Mod N:         Moved = {mod_add_moved}, Rate = {mod_add_rate:.4f}")
        else:
            lines.append("  Consistent Hashing: Moved = 0, Rate = N/A (K=0, no guests)")
            lines.append("  Hash Mod N:         Moved = 0, Rate = N/A (K=0, no guests)")

        lines.append(f"Remove 1 Building ({n} -> {n - 1}):")
        if k > 0:
            lines.append(f"  Consistent Hashing: Moved = {ch_rem_moved}, Rate = {ch_rem_rate:.4f}")
            lines.append(f"  Hash Mod N:         Moved = {mod_rem_moved}, Rate = {mod_rem_rate:.4f}")
        else:
            lines.append("  Consistent Hashing: Moved = 0, Rate = N/A (K=0, no guests)")
            lines.append("  Hash Mod N:         Moved = 0, Rate = N/A (K=0, no guests)")

        print_box(lines, title="CH VS HASH MOD N")
    except (ValueError, TypeError):
        print_box("Invalid input.", title="ERROR")


def handle_csv_export(cli):
    if not CSVExporter:
        print_box("CSVExporter not available.", title="ERROR")
        return

    os.makedirs("output", exist_ok=True)
    lines = []

    if cli.system:
        rooms = cli.system.list_occupied_rooms()
        CSVExporter.export_guests("output/guests.csv", rooms)
        lines.append(f"Exported {len(rooms)} guests to output/guests.csv")
    else:
        lines.append("System not initialized. Skipped guests export.")

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
        lines.append(f"Exported {len(mig_data)} migration records to output/migrations.csv")
    else:
        lines.append("No migration history recorded. Skipped migrations export.")

    print_box(lines, title="CSV EXPORT")
