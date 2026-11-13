import os
import time
import tracemalloc
import statistics
from typing import List, Tuple, Dict, Any, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.export import CSVExporter

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

    @staticmethod
    def _summarize(values: List[float]) -> Dict[str, float]:
        if not values:
            return {"median": 0.0, "mean": 0.0, "min": 0.0, "max": 0.0}
        return {
            "median": float(statistics.median(values)),
            "mean": float(statistics.mean(values)),
            "min": float(min(values)),
            "max": float(max(values)),
        }

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
            guest_list = self.generate_guest_batch(k)
            search_subset = guest_list[:1000] if len(guest_list) >= 1000 else guest_list

            ring_build_times = []
            assign_times = []
            search_1000_times = []
            search_per_query_times = []
            sort_times = []
            current_mems = []
            peak_mems = []
            rounds_timing = []

            for salt in self.salts:
                t_ring_0 = time.perf_counter()
                system = HotelSystem(v_nodes=32, salt=salt)
                for i in range(10):
                    system.add_building(f"Node_{i}")
                ring_build_time = time.perf_counter() - t_ring_0
                ring_build_times.append(ring_build_time)

                t_assign_0 = time.perf_counter()
                for c, s in guest_list:
                    if not system.add_single_guest(c, s):
                        raise RuntimeError(f"Failed to add guest ({c}, {s})")
                assign_time = time.perf_counter() - t_assign_0
                assign_times.append(assign_time)

                t_search_0 = time.perf_counter()
                for c, s in search_subset:
                    system.search_by_guest(c, s)
                search_time = time.perf_counter() - t_search_0
                per_query_time = search_time / len(search_subset) if search_subset else 0.0
                search_1000_times.append(search_time)
                search_per_query_times.append(per_query_time)

                t_sort_0 = time.perf_counter()
                system.list_occupied_rooms()
                sort_time = time.perf_counter() - t_sort_0
                sort_times.append(sort_time)

                rounds_timing.append(
                    {
                        "salt": salt,
                        "ring_build_time": ring_build_time,
                        "assignment_time": assign_time,
                        "search_1000_time": search_time,
                        "search_per_query_time": per_query_time,
                        "sort_time": sort_time,
                    }
                )

            for idx, salt in enumerate(self.salts):
                tracemalloc.start()
                system_mem = HotelSystem(v_nodes=32, salt=salt)
                for i in range(10):
                    system_mem.add_building(f"Node_{i}")
                for c, s in guest_list:
                    system_mem.add_single_guest(c, s)
                current, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()

                current_mib = current / (1024 * 1024)
                peak_mib = peak / (1024 * 1024)
                current_mems.append(current_mib)
                peak_mems.append(peak_mib)
                rounds_timing[idx]["current_mem_mib"] = current_mib
                rounds_timing[idx]["peak_mem_mib"] = peak_mib

            ring_stats = self._summarize(ring_build_times)
            assign_stats = self._summarize(assign_times)
            search_stats = self._summarize(search_1000_times)
            per_query_stats = self._summarize(search_per_query_times)
            sort_stats = self._summarize(sort_times)
            curr_mem_stats = self._summarize(current_mems)
            peak_mem_stats = self._summarize(peak_mems)

            results[k] = {
                "ring_build_time_median": ring_stats["median"],
                "ring_build_time_mean": ring_stats["mean"],
                "ring_build_time_min": ring_stats["min"],
                "ring_build_time_max": ring_stats["max"],
                "assignment_time_median": assign_stats["median"],
                "assignment_time_mean": assign_stats["mean"],
                "assignment_time_min": assign_stats["min"],
                "assignment_time_max": assign_stats["max"],
                "search_1000_time_median": search_stats["median"],
                "search_1000_time_mean": search_stats["mean"],
                "search_1000_time_min": search_stats["min"],
                "search_1000_time_max": search_stats["max"],
                "search_per_query_time_median": per_query_stats["median"],
                "search_per_query_time_mean": per_query_stats["mean"],
                "search_per_query_time_min": per_query_stats["min"],
                "search_per_query_time_max": per_query_stats["max"],
                "sort_time_median": sort_stats["median"],
                "sort_time_mean": sort_stats["mean"],
                "sort_time_min": sort_stats["min"],
                "sort_time_max": sort_stats["max"],
                "current_mem_mib_median": curr_mem_stats["median"],
                "current_mem_mib_mean": curr_mem_stats["mean"],
                "current_mem_mib_min": curr_mem_stats["min"],
                "current_mem_mib_max": curr_mem_stats["max"],
                "peak_mem_mib_median": peak_mem_stats["median"],
                "peak_mem_mib_mean": peak_mem_stats["mean"],
                "peak_mem_mib_min": peak_mem_stats["min"],
                "peak_mem_mib_max": peak_mem_stats["max"],
                "rounds": rounds_timing,
            }

        return results

    def run_experiment_b(
        self, n_values: Optional[List[int]] = None, k: int = 10000, v: int = 32
    ) -> Dict[int, Dict[str, Any]]:
        if HotelSystem is None or ModNHotelSystem is None:
            raise RuntimeError("HotelSystem or ModNHotelSystem is not available")

        if n_values is None:
            n_values = [5, 10, 20]

        results = {}
        guest_list = self.generate_guest_batch(k)
        guest_keys = [f"guest:{c}:{s}" for c, s in guest_list]

        for n in n_values:
            ch_add_rates, ch_rem_rates = [], []
            mod_add_rates, mod_rem_rates = [], []
            ch_add_moved_list, ch_rem_moved_list = [], []
            mod_add_moved_list, mod_rem_moved_list = [], []
            ch_add_times, ch_rem_times = [], []
            mod_add_times, mod_rem_times = [], []
            rounds = []

            for salt in self.salts:
                ch_add_sys = HotelSystem(v_nodes=v, salt=salt)
                mod_add_sys = ModNHotelSystem(salt=salt)
                for i in range(n):
                    b_id = f"Node_{i}"
                    ch_add_sys.add_building(b_id)
                    mod_add_sys.add_building(b_id)
                for c, s in guest_list:
                    if not ch_add_sys.add_single_guest(c, s):
                        raise RuntimeError(f"Failed to add guest ({c}, {s})")

                t0 = time.perf_counter()
                _, ch_add_migs, ch_add_rate = ch_add_sys.add_building(f"Node_{n}")
                ch_add_time = time.perf_counter() - t0
                ch_add_moved = len(ch_add_migs)

                mod_init_assign = [mod_add_sys.get_node(gk) for gk in guest_keys]
                t1 = time.perf_counter()
                mod_add_sys.add_building(f"Node_{n}")
                mod_after_add = [mod_add_sys.get_node(gk) for gk in guest_keys]
                mod_add_time = time.perf_counter() - t1
                mod_add_moved = sum(1 for a, b in zip(mod_init_assign, mod_after_add) if a != b)
                mod_add_rate = mod_add_moved / k if k > 0 else 0.0

                ch_rem_sys = HotelSystem(v_nodes=v, salt=salt)
                mod_rem_sys = ModNHotelSystem(salt=salt)
                for i in range(n):
                    b_id = f"Node_{i}"
                    ch_rem_sys.add_building(b_id)
                    mod_rem_sys.add_building(b_id)
                for c, s in guest_list:
                    if not ch_rem_sys.add_single_guest(c, s):
                        raise RuntimeError(f"Failed to add guest ({c}, {s})")

                t2 = time.perf_counter()
                _, ch_rem_migs, ch_rem_rate = ch_rem_sys.remove_building("Node_0")
                ch_rem_time = time.perf_counter() - t2
                ch_rem_moved = len(ch_rem_migs)

                mod_rem_init = [mod_rem_sys.get_node(gk) for gk in guest_keys]
                t3 = time.perf_counter()
                mod_rem_sys.remove_building("Node_0")
                mod_after_rem = [mod_rem_sys.get_node(gk) for gk in guest_keys]
                mod_rem_time = time.perf_counter() - t3
                mod_rem_moved = sum(1 for a, b in zip(mod_rem_init, mod_after_rem) if a != b)
                mod_rem_rate = mod_rem_moved / k if k > 0 else 0.0

                ch_add_rates.append(ch_add_rate)
                ch_rem_rates.append(ch_rem_rate)
                mod_add_rates.append(mod_add_rate)
                mod_rem_rates.append(mod_rem_rate)

                ch_add_moved_list.append(ch_add_moved)
                ch_rem_moved_list.append(ch_rem_moved)
                mod_add_moved_list.append(mod_add_moved)
                mod_rem_moved_list.append(mod_rem_moved)

                ch_add_times.append(ch_add_time)
                ch_rem_times.append(ch_rem_time)
                mod_add_times.append(mod_add_time)
                mod_rem_times.append(mod_rem_time)

                rounds.append(
                    {
                        "salt": salt,
                        "ch_add_moved": ch_add_moved,
                        "ch_add_rate": ch_add_rate,
                        "ch_add_time": ch_add_time,
                        "ch_rem_moved": ch_rem_moved,
                        "ch_rem_rate": ch_rem_rate,
                        "ch_rem_time": ch_rem_time,
                        "mod_add_moved": mod_add_moved,
                        "mod_add_rate": mod_add_rate,
                        "mod_add_time": mod_add_time,
                        "mod_rem_moved": mod_rem_moved,
                        "mod_rem_rate": mod_rem_rate,
                        "mod_rem_time": mod_rem_time,
                    }
                )

            ch_add_r = self._summarize(ch_add_rates)
            ch_rem_r = self._summarize(ch_rem_rates)
            mod_add_r = self._summarize(mod_add_rates)
            mod_rem_r = self._summarize(mod_rem_rates)

            ch_add_m = self._summarize(ch_add_moved_list)
            ch_rem_m = self._summarize(ch_rem_moved_list)
            mod_add_m = self._summarize(mod_add_moved_list)
            mod_rem_m = self._summarize(mod_rem_moved_list)

            ch_add_t = self._summarize(ch_add_times)
            ch_rem_t = self._summarize(ch_rem_times)
            mod_add_t = self._summarize(mod_add_times)
            mod_rem_t = self._summarize(mod_rem_times)

            results[n] = {
                "ch_add_rate_median": ch_add_r["median"],
                "ch_add_rate_mean": ch_add_r["mean"],
                "ch_add_rate_min": ch_add_r["min"],
                "ch_add_rate_max": ch_add_r["max"],
                "ch_rem_rate_median": ch_rem_r["median"],
                "ch_rem_rate_mean": ch_rem_r["mean"],
                "ch_rem_rate_min": ch_rem_r["min"],
                "ch_rem_rate_max": ch_rem_r["max"],
                "mod_add_rate_median": mod_add_r["median"],
                "mod_add_rate_mean": mod_add_r["mean"],
                "mod_add_rate_min": mod_add_r["min"],
                "mod_add_rate_max": mod_add_r["max"],
                "mod_rem_rate_median": mod_rem_r["median"],
                "mod_rem_rate_mean": mod_rem_r["mean"],
                "mod_rem_rate_min": mod_rem_r["min"],
                "mod_rem_rate_max": mod_rem_r["max"],
                "ch_add_moved_median": int(ch_add_m["median"]),
                "ch_rem_moved_median": int(ch_rem_m["median"]),
                "mod_add_moved_median": int(mod_add_m["median"]),
                "mod_rem_moved_median": int(mod_rem_m["median"]),
                "ch_add_time_median": ch_add_t["median"],
                "ch_rem_time_median": ch_rem_t["median"],
                "mod_add_time_median": mod_add_t["median"],
                "mod_rem_time_median": mod_rem_t["median"],
                "rounds": rounds,
            }

        return results

    def run_experiment_c(
        self, v_values: Optional[List[int]] = None, n: int = 10, k: int = 10000
    ) -> Dict[int, Dict[str, Any]]:
        if HotelSystem is None:
            raise RuntimeError("HotelSystem is not available")

        if v_values is None:
            v_values = [1, 8, 32]

        results = {}
        guest_list = self.generate_guest_batch(k)

        for v in v_values:
            cvs = []
            add_rates = []
            rem_rates = []
            add_moved_list = []
            rem_moved_list = []
            current_mems = []
            peak_mems = []
            rounds = []

            for salt in self.salts:
                system = HotelSystem(v_nodes=v, salt=salt)
                for i in range(n):
                    system.add_building(f"Node_{i}")
                for c, s in guest_list:
                    if not system.add_single_guest(c, s):
                        raise RuntimeError(f"Failed to add guest ({c}, {s})")

                stats = system.get_load_balance_stats()
                cv_val = stats["cv"] if isinstance(stats["cv"], (int, float)) else 0.0
                cvs.append(cv_val)

                _, add_migs, add_rate = system.add_building(f"Node_{n}")
                add_rates.append(add_rate)
                add_moved_list.append(len(add_migs))

                system_rem = HotelSystem(v_nodes=v, salt=salt)
                for i in range(n):
                    system_rem.add_building(f"Node_{i}")
                for c, s in guest_list:
                    system_rem.add_single_guest(c, s)
                _, rem_migs, rem_rate = system_rem.remove_building("Node_0")
                rem_rates.append(rem_rate)
                rem_moved_list.append(len(rem_migs))

                rounds.append(
                    {
                        "salt": salt,
                        "cv": cv_val,
                        "min_guests": stats["min"],
                        "max_guests": stats["max"],
                        "mean_guests": stats["mean"],
                        "std_guests": stats["std"],
                        "per_building": stats["per_building"],
                        "add_moved": len(add_migs),
                        "add_rate": add_rate,
                        "rem_moved": len(rem_migs),
                        "rem_rate": rem_rate,
                    }
                )

            for idx, salt in enumerate(self.salts):
                tracemalloc.start()
                system_mem = HotelSystem(v_nodes=v, salt=salt)
                for i in range(n):
                    system_mem.add_building(f"Node_{i}")
                for c, s in guest_list:
                    system_mem.add_single_guest(c, s)
                current, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()

                curr_mib = current / (1024 * 1024)
                peak_mib = peak / (1024 * 1024)
                current_mems.append(curr_mib)
                peak_mems.append(peak_mib)
                rounds[idx]["current_mem_mib"] = curr_mib
                rounds[idx]["peak_mem_mib"] = peak_mib

            cv_stats = self._summarize(cvs)
            curr_mem_stats = self._summarize(current_mems)
            peak_mem_stats = self._summarize(peak_mems)
            add_rate_stats = self._summarize(add_rates)
            rem_rate_stats = self._summarize(rem_rates)
            add_moved_stats = self._summarize(add_moved_list)
            rem_moved_stats = self._summarize(rem_moved_list)

            results[v] = {
                "cv_median": cv_stats["median"],
                "cv_mean": cv_stats["mean"],
                "cv_min": cv_stats["min"],
                "cv_max": cv_stats["max"],
                "current_mem_mib_median": curr_mem_stats["median"],
                "current_mem_mib_mean": curr_mem_stats["mean"],
                "current_mem_mib_min": curr_mem_stats["min"],
                "current_mem_mib_max": curr_mem_stats["max"],
                "peak_mem_mib_median": peak_mem_stats["median"],
                "peak_mem_mib_mean": peak_mem_stats["mean"],
                "peak_mem_mib_min": peak_mem_stats["min"],
                "peak_mem_mib_max": peak_mem_stats["max"],
                "add_rate_median": add_rate_stats["median"],
                "rem_rate_median": rem_rate_stats["median"],
                "add_moved_median": int(add_moved_stats["median"]),
                "rem_moved_median": int(rem_moved_stats["median"]),
                "per_building_counts": rounds[0]["per_building"] if rounds else {},
                "rounds": rounds,
            }

        return results

    def plot_graph_a(
        self,
        k_values: List[int],
        times: Optional[List[float]] = None,
        output_path: str = "output/graph_a.png",
        exp_results: Optional[Dict[int, Dict[str, Any]]] = None,
    ) -> None:
        plt.figure(figsize=(9, 5.5))
        if exp_results:
            ks = sorted(exp_results.keys())
            x_labels = [f"{k:,}" for k in ks]

            assign_means = [exp_results[k]["assignment_time_mean"] for k in ks]
            assign_err_low = [exp_results[k]["assignment_time_mean"] - exp_results[k]["assignment_time_min"] for k in ks]
            assign_err_high = [exp_results[k]["assignment_time_max"] - exp_results[k]["assignment_time_mean"] for k in ks]

            sort_means = [exp_results[k]["sort_time_mean"] for k in ks]
            sort_err_low = [exp_results[k]["sort_time_mean"] - exp_results[k]["sort_time_min"] for k in ks]
            sort_err_high = [exp_results[k]["sort_time_max"] - exp_results[k]["sort_time_mean"] for k in ks]

            ring_means = [exp_results[k]["ring_build_time_mean"] for k in ks]

            plt.errorbar(
                x_labels,
                assign_means,
                yerr=[assign_err_low, assign_err_high],
                marker="o",
                capsize=5,
                color="tab:blue",
                label="Guest Assignment Time (mean ± min/max)",
            )
            plt.errorbar(
                x_labels,
                sort_means,
                yerr=[sort_err_low, sort_err_high],
                marker="s",
                capsize=5,
                color="tab:orange",
                label="Room Sort Time (mean ± min/max)",
            )
            plt.plot(
                x_labels,
                ring_means,
                marker="^",
                linestyle="--",
                color="tab:green",
                label="Ring Build Time (mean)",
            )
        else:
            plt.plot([str(k) for k in k_values], times or [], marker="o", color="tab:blue", label="Execution Time")

        plt.title(f"Experiment A: Execution Time vs Guests K (N=10, V=32, salts={self.salts})")
        plt.xlabel("Number of Guests (K)")
        plt.ylabel("Execution Time (seconds)")
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.legend()
        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        plt.close()

    def plot_graph_b(
        self,
        ch_rates: Optional[List[float]] = None,
        mod_rates: Optional[List[float]] = None,
        n_labels: Optional[List[str]] = None,
        output_path: str = "output/graph_b.png",
        exp_results: Optional[Dict[int, Dict[str, Any]]] = None,
    ) -> None:
        plt.figure(figsize=(9, 5.5))
        if exp_results:
            ns = sorted(exp_results.keys())
            labels = [str(n) for n in ns]

            ch_add_mean = [exp_results[n]["ch_add_rate_mean"] for n in ns]
            ch_add_low = [exp_results[n]["ch_add_rate_mean"] - exp_results[n]["ch_add_rate_min"] for n in ns]
            ch_add_high = [exp_results[n]["ch_add_rate_max"] - exp_results[n]["ch_add_rate_mean"] for n in ns]

            ch_rem_mean = [exp_results[n]["ch_rem_rate_mean"] for n in ns]
            ch_rem_low = [exp_results[n]["ch_rem_rate_mean"] - exp_results[n]["ch_rem_rate_min"] for n in ns]
            ch_rem_high = [exp_results[n]["ch_rem_rate_max"] - exp_results[n]["ch_rem_rate_mean"] for n in ns]

            mod_add_mean = [exp_results[n]["mod_add_rate_mean"] for n in ns]
            mod_rem_mean = [exp_results[n]["mod_rem_rate_mean"] for n in ns]

            plt.errorbar(
                labels,
                ch_add_mean,
                yerr=[ch_add_low, ch_add_high],
                marker="o",
                capsize=5,
                color="tab:blue",
                label="Consistent Hashing - Add 1 Building (mean ± min/max)",
            )
            plt.errorbar(
                labels,
                ch_rem_mean,
                yerr=[ch_rem_low, ch_rem_high],
                marker="^",
                linestyle="--",
                capsize=5,
                color="tab:cyan",
                label="Consistent Hashing - Remove 1 Building (mean ± min/max)",
            )
            plt.plot(
                labels,
                mod_add_mean,
                marker="s",
                color="tab:red",
                label="Hash Mod N - Add 1 Building (mean)",
            )
            plt.plot(
                labels,
                mod_rem_mean,
                marker="D",
                linestyle="--",
                color="tab:orange",
                label="Hash Mod N - Remove 1 Building (mean)",
            )
        else:
            plt.plot(n_labels or [], ch_rates or [], marker="o", label="Consistent Hashing", color="tab:blue")
            plt.plot(n_labels or [], mod_rates or [], marker="s", label="Hash Mod N", color="tab:red")

        plt.title(f"Experiment B: Migration Rate vs Buildings N (K=10,000, V=32, salts={self.salts})")
        plt.xlabel("Initial Number of Buildings (N)")
        plt.ylabel("Migration Rate (Moved Guests / K)")
        plt.ylim(0, 1.05)
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.legend(fontsize=8.5)
        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        plt.close()

    def plot_graph_c(
        self,
        v_labels: Optional[List[str]] = None,
        cv_values: Optional[List[float]] = None,
        mem_values: Optional[List[float]] = None,
        output_path: str = "output/graph_c.png",
        exp_results: Optional[Dict[int, Dict[str, Any]]] = None,
    ) -> None:
        fig, ax1 = plt.subplots(figsize=(9, 5.5))

        if exp_results:
            vs = sorted(exp_results.keys())
            labels = [str(v) for v in vs]

            cv_mean = [exp_results[v]["cv_mean"] for v in vs]
            cv_low = [exp_results[v]["cv_mean"] - exp_results[v]["cv_min"] for v in vs]
            cv_high = [exp_results[v]["cv_max"] - exp_results[v]["cv_mean"] for v in vs]

            mem_mean = [exp_results[v]["peak_mem_mib_mean"] for v in vs]
            mem_low = [exp_results[v]["peak_mem_mib_mean"] - exp_results[v]["peak_mem_mib_min"] for v in vs]
            mem_high = [exp_results[v]["peak_mem_mib_max"] - exp_results[v]["peak_mem_mib_mean"] for v in vs]
        else:
            labels = v_labels or []
            cv_mean = cv_values or []
            mem_mean = mem_values or []
            cv_low = cv_high = mem_low = mem_high = None

        c_cv = "tab:blue"
        ax1.set_xlabel("Virtual Nodes per Building (V)")
        ax1.set_ylabel("Coefficient of Variation (CV = std / mean)", color=c_cv)
        if exp_results:
            line1 = ax1.errorbar(
                labels,
                cv_mean,
                yerr=[cv_low, cv_high],
                marker="o",
                capsize=5,
                color=c_cv,
                label="Load Balance CV (mean ± min/max)",
            )
        else:
            line1 = ax1.plot(labels, cv_mean, marker="o", color=c_cv, label="CV (Load Balance)")
        ax1.tick_params(axis="y", labelcolor=c_cv)
        ax1.grid(True, linestyle="--", alpha=0.5)

        ax2 = ax1.twinx()
        c_mem = "tab:red"
        ax2.set_ylabel("Peak Traced Memory (MiB, tracemalloc)", color=c_mem)
        if exp_results:
            line2 = ax2.errorbar(
                labels,
                mem_mean,
                yerr=[mem_low, mem_high],
                marker="s",
                linestyle="--",
                capsize=5,
                color=c_mem,
                label="Peak Memory MiB (mean ± min/max)",
            )
        else:
            line2 = ax2.plot(labels, mem_mean, marker="s", color=c_mem, linestyle="--", label="Peak Memory (MiB)")
        ax2.tick_params(axis="y", labelcolor=c_mem)

        h1, l1 = ax1.get_legend_handles_labels()
        h2, l2 = ax2.get_legend_handles_labels()
        ax1.legend(h1 + h2, l1 + l2, loc="upper center")

        plt.title(f"Experiment C: Effect of Virtual Nodes V on CV & Memory (N=10, K=10,000, salts={self.salts})")
        fig.tight_layout()
        plt.savefig(output_path, dpi=300)
        plt.close()

    def run_all_and_export(self, output_dir: str = "output") -> Dict[str, Any]:
        os.makedirs(output_dir, exist_ok=True)

        exp_a = self.run_experiment_a([1000, 10000, 100000])
        exp_b = self.run_experiment_b([5, 10, 20], k=10000, v=32)
        exp_c = self.run_experiment_c([1, 8, 32], n=10, k=10000)

        rows_a = []
        for k, data in sorted(exp_a.items()):
            for r in data["rounds"]:
                rows_a.append(
                    {
                        "N": 10,
                        "V": 32,
                        "K": k,
                        "salt": r["salt"],
                        "ring_build_time_s": round(r["ring_build_time"], 6),
                        "assignment_time_s": round(r["assignment_time"], 6),
                        "search_1000_time_s": round(r["search_1000_time"], 6),
                        "search_per_query_time_s": round(r["search_per_query_time"], 9),
                        "sort_time_s": round(r["sort_time"], 6),
                        "current_mem_mib": round(r["current_mem_mib"], 6),
                        "peak_mem_mib": round(r["peak_mem_mib"], 6),
                        "assignment_time_median_s": round(data["assignment_time_median"], 6),
                        "peak_mem_mib_median": round(data["peak_mem_mib_median"], 6),
                    }
                )
        CSVExporter.export_experiment_results(os.path.join(output_dir, "experiment_a.csv"), rows_a)

        rows_b = []
        for n, data in sorted(exp_b.items()):
            for r in data["rounds"]:
                rows_b.append(
                    {
                        "N": n,
                        "V": 32,
                        "K": 10000,
                        "salt": r["salt"],
                        "ch_add_moved": r["ch_add_moved"],
                        "ch_add_rate": round(r["ch_add_rate"], 6),
                        "ch_add_time_s": round(r["ch_add_time"], 6),
                        "ch_rem_moved": r["ch_rem_moved"],
                        "ch_rem_rate": round(r["ch_rem_rate"], 6),
                        "ch_rem_time_s": round(r["ch_rem_time"], 6),
                        "mod_add_moved": r["mod_add_moved"],
                        "mod_add_rate": round(r["mod_add_rate"], 6),
                        "mod_add_time_s": round(r["mod_add_time"], 6),
                        "mod_rem_moved": r["mod_rem_moved"],
                        "mod_rem_rate": round(r["mod_rem_rate"], 6),
                        "mod_rem_time_s": round(r["mod_rem_time"], 6),
                    }
                )
        CSVExporter.export_experiment_results(os.path.join(output_dir, "experiment_b.csv"), rows_b)

        rows_c = []
        for v, data in sorted(exp_c.items()):
            for r in data["rounds"]:
                rows_c.append(
                    {
                        "N": 10,
                        "V": v,
                        "K": 10000,
                        "salt": r["salt"],
                        "min_guests": r["min_guests"],
                        "max_guests": r["max_guests"],
                        "mean_guests": round(r["mean_guests"], 4),
                        "std_guests": round(r["std_guests"], 4),
                        "cv": round(r["cv"], 6),
                        "current_mem_mib": round(r["current_mem_mib"], 6),
                        "peak_mem_mib": round(r["peak_mem_mib"], 6),
                        "add_moved": r["add_moved"],
                        "add_rate": round(r["add_rate"], 6),
                        "rem_moved": r["rem_moved"],
                        "rem_rate": round(r["rem_rate"], 6),
                        "per_building": str(r["per_building"]),
                    }
                )
        CSVExporter.export_experiment_results(os.path.join(output_dir, "experiment_c.csv"), rows_c)

        sample_sys = HotelSystem(v_nodes=32, salt="0")
        for i in range(10):
            sample_sys.add_building(f"Node_{i}")
        for c, s in self.generate_guest_batch(1000):
            sample_sys.add_single_guest(c, s)

        guests_rows = [
            {
                "channel_id": row["channel_id"],
                "sequence_id": row["sequence_id"],
                "node_id": row["node_id"],
                "room_no": row["room_no"],
            }
            for row in sample_sys.list_occupied_rooms()
        ]
        CSVExporter.export_guests(os.path.join(output_dir, "guests.csv"), guests_rows)

        _, add_migs, _ = sample_sys.add_building("Node_10")
        _, rem_migs, _ = sample_sys.remove_building("Node_0")
        all_migs = add_migs + rem_migs
        mig_rows = [
            {
                "channel_id": m.channel_id,
                "sequence_id": m.sequence_id,
                "old_node": m.old_node,
                "new_node": m.new_node,
                "room_no": m.room_no,
            }
            for m in all_migs
        ]
        CSVExporter.export_migrations(os.path.join(output_dir, "migrations.csv"), mig_rows)

        self.plot_graph_a(
            sorted(exp_a.keys()),
            output_path=os.path.join(output_dir, "graph_a.png"),
            exp_results=exp_a,
        )
        self.plot_graph_b(
            output_path=os.path.join(output_dir, "graph_b.png"),
            exp_results=exp_b,
        )
        self.plot_graph_c(
            output_path=os.path.join(output_dir, "graph_c.png"),
            exp_results=exp_c,
        )

        return {"exp_a": exp_a, "exp_b": exp_b, "exp_c": exp_c}


if __name__ == "__main__":
    runner = ExperimentRunner()
    summary = runner.run_all_and_export("output")
    print("Exported all CSVs and graphs to output/")
    print("Exp A (medians):", {k: (v["assignment_time_median"], v["peak_mem_mib_median"]) for k, v in summary["exp_a"].items()})
    print("Exp B (medians):", {n: (v["ch_add_rate_median"], v["mod_add_rate_median"]) for n, v in summary["exp_b"].items()})
    print("Exp C (medians):", {v: (val["cv_median"], val["peak_mem_mib_median"]) for v, val in summary["exp_c"].items()})
