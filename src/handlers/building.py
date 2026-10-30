import questionary


def handle_building_modification(cli):
    if not cli.system:
        print("Please initialize system first.")
        return

    action = questionary.select("Action:", choices=["Add Building", "Remove Building", "Back"]).ask()
    if action == "Back" or not action:
        return

    b_id = questionary.text("Building Node ID:").ask()
    if not b_id:
        return

    if action == "Add Building":
        ok, migs, rate = cli.system.add_building(b_id)
        if ok:
            cli.migration_history.extend(migs)
            print(f"Added {b_id}. Relocated: {len(migs)}, Rate: {rate:.4f}")
        else:
            print(f"Failed to add {b_id} (already exists).")
    else:
        ok, migs, rate = cli.system.remove_building(b_id)
        if ok:
            cli.migration_history.extend(migs)
            print(f"Removed {b_id}. Relocated: {len(migs)}, Rate: {rate:.4f}")
        else:
            print(f"Failed to remove {b_id} (not found or only 1 building left).")


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
