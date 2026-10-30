import questionary


def handle_remove_guest(cli):
    if not cli.system:
        print("Please initialize system first.")
        return

    c = questionary.text("Channel ID:").ask()
    s = questionary.text("Sequence ID:").ask()
    try:
        fn = getattr(cli.system, "remove_guest", None)
        ok = fn(int(c), int(s)) if fn else False
        print("Guest removed." if ok else "Guest not found.")
    except (ValueError, TypeError):
        print("Invalid input.")


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
