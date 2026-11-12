import time
import tracemalloc
import statistics
from typing import List, Tuple, Dict, Any, Optional
import matplotlib.pyplot as plt

try:
    from src.hotel_system import HotelSystem
except ImportError:
    HotelSystem = None

try:
    from src.mod_n_system import ModNHotelSystem
except ImportError:
    ModNHotelSystem = None


class ExperimentRunner:
    def __init__(self, salts: Optional[List[str]] = None):
        self.salts = salts if salts is not None else ["0", "1", "2"]

    def generate_guest_batch(self, k: int) -> List[Tuple[int, int]]:
        guests = []
        c_count = 10
        base_per_channel = k // c_count
        remainder = k % c_count
        for c in range(1, c_count + 1):
            count = base_per_channel + (1 if c <= remainder else 0)
            for s in range(1, count + 1):
                guests.append((c, s))
        return guests

    def run_experiment_a(self, k_values: Optional[List[int]] = None) -> Dict[int, Dict[str, Any]]:
        if HotelSystem is None:
            raise RuntimeError("HotelSystem is not available")

        if k_values is None:
            k_values = [1000, 10000, 100000]

        results = {}
        for k in k_values:
            assign_times = []
            search_times = []
            sort_times = []
            peak_mems = []

            for salt in self.salts:
                system = HotelSystem(v_nodes=32, salt=salt)
                for i in range(10):
                    system.add_building(f"Node_{i}")
                guest_list = self.generate_guest_batch(k)

                t0 = time.perf_counter()
                for c, s in guest_list:
                    if hasattr(system, "add_single_guest"):
                        system.add_single_guest(c, s)
                    elif hasattr(system, "add_guest"):
                        system.add_guest(c, s)
                assign_times.append(time.perf_counter() - t0)

                search_subset = guest_list[:1000] if len(guest_list) >= 1000 else guest_list
                t1 = time.perf_counter()
                for c, s in search_subset:
                    if hasattr(system, "search_by_guest"):
                        system.search_by_guest(c, s)
                    elif hasattr(system, "index_manager"):
                        system.index_manager.search_by_guest(c, s)
                search_times.append(time.perf_counter() - t1)

                t2 = time.perf_counter()
                if hasattr(system, "list_occupied_rooms"):
                    system.list_occupied_rooms()
                sort_times.append(time.perf_counter() - t2)

            for salt in self.salts:
                tracemalloc.start()
                system_mem = HotelSystem(v_nodes=32, salt=salt)
                for i in range(10):
                    system_mem.add_building(f"Node_{i}")
                guest_list = self.generate_guest_batch(k)
                for c, s in guest_list:
                    if hasattr(system_mem, "add_single_guest"):
                        system_mem.add_single_guest(c, s)
                    elif hasattr(system_mem, "add_guest"):
                        system_mem.add_guest(c, s)
                _, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                peak_mems.append(peak / (1024 * 1024))

            results[k] = {
                "assignment_time_median": statistics.median(assign_times) if assign_times else 0.0,
                "search_1000_time_median": statistics.median(search_times) if search_times else 0.0,
                "sort_time_median": statistics.median(sort_times) if sort_times else 0.0,
                "peak_mem_mib_median": statistics.median(peak_mems) if peak_mems else 0.0,
            }

        return results

    def run_experiment_b(self, n_values: Optional[List[int]] = None, k: int = 10000, v: int = 32) -> Dict[int, Dict[str, Any]]:
        if HotelSystem is None or ModNHotelSystem is None:
            raise RuntimeError("HotelSystem or ModNHotelSystem is not available")

        if n_values is None:
            n_values = [5, 10, 20]

        results = {}
        guest_list = self.generate_guest_batch(k)

        for n in n_values:
            ch_add_rates = []
            ch_rem_rates = []
            mod_add_rates = []
            mod_rem_rates = []

            for salt in self.salts:
                ch_sys = HotelSystem(v_nodes=v, salt=salt)
                mod_sys = ModNHotelSystem(salt=salt)

                for i in range(n):
                    b_id = f"Node_{i}"
                    ch_sys.add_building(b_id)
                    mod_sys.add_building(b_id)

                for c, s in guest_list:
                    if hasattr(ch_sys, "add_single_guest"):
                        ch_sys.add_single_guest(c, s)
                    elif hasattr(ch_sys, "add_guest"):
                        ch_sys.add_guest(c, s)

                _, _, add_rate = ch_sys.add_building("New_Node")
                ch_add_rates.append(add_rate)

                _, _, rem_rate = ch_sys.remove_building("Node_0")
                ch_rem_rates.append(rem_rate)

                mod_init_assignments = [mod_sys.get_node(f"guest:{c}:{s}") for c, s in guest_list]
                mod_sys.add_building("New_Node")
                mod_after_add = [mod_sys.get_node(f"guest:{c}:{s}") for c, s in guest_list]
                mod_add_moved = sum(1 for a, b in zip(mod_init_assignments, mod_after_add) if a != b)
                mod_add_rates.append(mod_add_moved / k if k > 0 else 0.0)

                mod_sys.remove_building("Node_0")
                mod_after_rem = [mod_sys.get_node(f"guest:{c}:{s}") for c, s in guest_list]
                mod_rem_moved = sum(1 for a, b in zip(mod_after_add, mod_after_rem) if a != b)
                mod_rem_rates.append(mod_rem_moved / k if k > 0 else 0.0)

            results[n] = {
                "ch_add_rate_median": statistics.median(ch_add_rates) if ch_add_rates else 0.0,
                "ch_rem_rate_median": statistics.median(ch_rem_rates) if ch_rem_rates else 0.0,
                "mod_add_rate_median": statistics.median(mod_add_rates) if mod_add_rates else 0.0,
                "mod_rem_rate_median": statistics.median(mod_rem_rates) if mod_rem_rates else 0.0,
            }

        return results

    def run_experiment_c(self, v_values: Optional[List[int]] = None, n: int = 10, k: int = 10000) -> Dict[int, Dict[str, Any]]:
        if HotelSystem is None:
            raise RuntimeError("HotelSystem is not available")

        if v_values is None:
            v_values = [1, 8, 32]

        results = {}
        guest_list = self.generate_guest_batch(k)

        for v in v_values:
            cvs = []
            mems = []

            for salt in self.salts:
                system = HotelSystem(v_nodes=v, salt=salt)
                for i in range(n):
                    system.add_building(f"Node_{i}")
                for c, s in guest_list:
                    if hasattr(system, "add_single_guest"):
                        system.add_single_guest(c, s)
                    elif hasattr(system, "add_guest"):
                        system.add_guest(c, s)

                stats = system.get_load_balance_stats()
                cv_val = stats["cv"] if isinstance(stats["cv"], (int, float)) else 0.0
                cvs.append(cv_val)

            for salt in self.salts:
                tracemalloc.start()
                system_mem = HotelSystem(v_nodes=v, salt=salt)
                for i in range(n):
                    system_mem.add_building(f"Node_{i}")
                for c, s in guest_list:
                    if hasattr(system_mem, "add_single_guest"):
                        system_mem.add_single_guest(c, s)
                    elif hasattr(system_mem, "add_guest"):
                        system_mem.add_guest(c, s)
                _, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                mems.append(peak / (1024 * 1024))

            results[v] = {
                "cv_median": statistics.median(cvs) if cvs else 0.0,
                "peak_mem_mib_median": statistics.median(mems) if mems else 0.0,
            }

        return results

    def plot_graph_a(self, k_values: List[int], times: List[float], output_path: str) -> None:
        plt.figure(figsize=(8, 5))
        plt.plot(k_values, times, marker="o", color="blue", label="Execution Time")
        plt.title("Execution Time vs K (Data Size)")
        plt.xlabel("Number of Guests (K)")
        plt.ylabel("Execution Time (seconds)")
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.legend()
        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        plt.close()

    def plot_graph_b(self, ch_rates: List[float], mod_rates: List[float], n_labels: List[str], output_path: str) -> None:
        plt.figure(figsize=(8, 5))
        plt.plot(n_labels, ch_rates, marker="o", label="Consistent Hashing", color="blue")
        plt.plot(n_labels, mod_rates, marker="s", label="Hash Mod N", color="red")
        plt.title("Migration Rate vs Number of Buildings (N)")
        plt.xlabel("Number of Buildings (N)")
        plt.ylabel("Migration Rate")
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.legend()
        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        plt.close()

    def plot_graph_c(self, v_labels: List[str], cv_values: List[float], mem_values: List[float], output_path: str) -> None:
        fig, ax1 = plt.subplots(figsize=(8, 5))

        color = "tab:blue"
        ax1.set_xlabel("Virtual Nodes (V)")
        ax1.set_ylabel("Coefficient of Variation (CV)", color=color)
        ax1.plot(v_labels, cv_values, marker="o", color=color, label="CV (Load Balance)")
        ax1.tick_params(axis="y", labelcolor=color)

        ax2 = ax1.twinx()
        color = "tab:red"
        ax2.set_ylabel("Peak Memory (MiB)", color=color)
        ax2.plot(v_labels, mem_values, marker="s", color=color, linestyle="--", label="Memory Footprint")
        ax2.tick_params(axis="y", labelcolor=color)

        plt.title("Effect of Virtual Nodes (V) on Balance and Memory")
        fig.tight_layout()
        plt.savefig(output_path, dpi=300)
        plt.close()
