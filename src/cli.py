from typing import Optional, Any
import questionary

from src.handlers.system import (
    handle_init,
    handle_load_balance,
    handle_benchmarks,
    handle_compare_mod_n,
    handle_csv_export,
)
from src.handlers.guest import (
    handle_add_guests,
    handle_remove_guest,
)
from src.handlers.building import (
    handle_building_modification,
    handle_search,
    handle_list_rooms,
)


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
            "8. Run Performance Benchmarks": lambda: handle_benchmarks(self),
            "9. Compare with Hash Mod N": lambda: handle_compare_mod_n(self),
            "10. Export Data to CSV": lambda: handle_csv_export(self),
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


if __name__ == "__main__":
    HotelCLI().run()
