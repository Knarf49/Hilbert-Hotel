import questionary

try:
    from src.hotel_system import HotelSystem
except ImportError:
    HotelSystem = None


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


def handle_search(cli):
    if not cli.system:
        print("Please initialize system first.")
        return

    mode = questionary.select("Search by:", choices=["Guest ID (c, s)", "Room (node_id, room_no)", "Back"]).ask()
    if mode == "Guest ID (c, s)":
        c = questionary.text("Channel ID:").ask()
        s = questionary.text("Sequence ID:").ask()
        try:
            fn = getattr(cli.system, "search_by_guest", None)
            if not fn and hasattr(cli.system, "index_manager"):
                fn = cli.system.index_manager.search_by_guest
            res = fn(int(c), int(s)) if fn else None
            print(f"Location: Building {res[0]}, Room {res[1]}" if res else "Not Found.")
        except (ValueError, TypeError):
            print("Invalid input.")
    elif mode == "Room (node_id, room_no)":
        node_id = questionary.text("Building Node ID:").ask()
        room_no = questionary.text("Room Number:").ask()
        try:
            fn = getattr(cli.system, "search_by_room", None)
            if not fn and hasattr(cli.system, "index_manager"):
                fn = cli.system.index_manager.search_by_room
            res = fn(node_id, int(room_no)) if fn else None
            print(f"Guest: Channel {res[0]}, Sequence {res[1]}" if res else "Not Found.")
        except (ValueError, TypeError):
            print("Invalid input.")


def handle_list_rooms(cli):
    if not cli.system:
        print("Please initialize system first.")
        return

    fn = getattr(cli.system, "list_occupied_rooms", None)
    if fn:
        rooms = fn()
        print(f"Occupied Rooms ({len(rooms)} total):")
        for r in rooms[:30]:
            print(r)
        if len(rooms) > 30:
            print(f"... and {len(rooms) - 30} more.")
    else:
        print("Feature not implemented in core system.")


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
