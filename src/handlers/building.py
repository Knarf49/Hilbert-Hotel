import questionary
from src.handlers import print_box


def handle_building_modification(cli):
    if not cli.system:
        print_box("Please initialize system first.", title="WARNING")
        return

    action = questionary.select("Action:", choices=["Add Building", "Remove Building", "Back"]).ask()
    if action == "Back" or not action:
        return

    b_id = questionary.text("Building Node ID:").ask()
    if not b_id:
        return

    k_before = cli.system.index_manager.total_guests()

    if action == "Add Building":
        ok, migs, rate = cli.system.add_building(b_id)
        if ok:
            cli.migration_history.extend(migs)
            rate_display = "N/A (K=0, no guests)" if k_before == 0 else f"{rate:.4f}"
            lines = [f"Added {b_id}. Relocated: {len(migs)}, Rate: {rate_display}"]
            if len(migs) > 0:
                lines.append("Relocation list:")
                for m in migs[:20]:
                    lines.append(
                        f"  ({m.channel_id}, {m.sequence_id}), {m.old_node} -> {m.new_node}, Room={m.room_no}"
                    )
                if len(migs) > 20:
                    lines.append(f"  ... and {len(migs) - 20} more (total {len(migs)}).")
            print_box(lines, title="ADD BUILDING")
        else:
            print_box(f"Failed to add {b_id} (already exists or invalid).", title="ADD BUILDING")
    else:
        ok, migs, rate = cli.system.remove_building(b_id)
        if ok:
            cli.migration_history.extend(migs)
            rate_display = "N/A (K=0, no guests)" if k_before == 0 else f"{rate:.4f}"
            lines = [f"Removed {b_id}. Relocated: {len(migs)}, Rate: {rate_display}"]
            if len(migs) > 0:
                lines.append("Relocation list:")
                for m in migs[:20]:
                    lines.append(
                        f"  ({m.channel_id}, {m.sequence_id}), {m.old_node} -> {m.new_node}, Room={m.room_no}"
                    )
                if len(migs) > 20:
                    lines.append(f"  ... and {len(migs) - 20} more (total {len(migs)}).")
            print_box(lines, title="REMOVE BUILDING")
        else:
            print_box(f"Failed to remove {b_id} (not found or only 1 building left).", title="REMOVE BUILDING")


def handle_search(cli):
    if not cli.system:
        print_box("Please initialize system first.", title="WARNING")
        return

    mode = questionary.select("Search by:", choices=["Guest ID (c, s)", "Room (node_id, room_no)", "Back"]).ask()
    if mode == "Guest ID (c, s)":
        c = questionary.text("Channel ID:").ask()
        s = questionary.text("Sequence ID:").ask()
        try:
            res = cli.system.search_by_guest(int(c), int(s))
            if res:
                print_box(f"Location: Building {res[0]}, Room {res[1]}", title="SEARCH RESULT")
            else:
                print_box("Not Found.", title="SEARCH RESULT")
        except (ValueError, TypeError):
            print_box("Invalid input.", title="ERROR")
    elif mode == "Room (node_id, room_no)":
        node_id = questionary.text("Building Node ID:").ask()
        room_no = questionary.text("Room Number:").ask()
        try:
            res = cli.system.search_by_room(node_id, int(room_no))
            if res:
                print_box(f"Guest: Channel {res[0]}, Sequence {res[1]}", title="SEARCH RESULT")
            else:
                print_box("Not Found.", title="SEARCH RESULT")
        except (ValueError, TypeError):
            print_box("Invalid input.", title="ERROR")


def handle_list_rooms(cli):
    if not cli.system:
        print_box("Please initialize system first.", title="WARNING")
        return

    rooms = cli.system.list_occupied_rooms()
    lines = [f"Occupied Rooms ({len(rooms)} total):"]
    for r in rooms[:30]:
        lines.append(
            f"Building {r['node_id']}, Room {r['room_no']}: Guest ({r['channel_id']}, {r['sequence_id']})"
        )
    if len(rooms) > 30:
        lines.append(f"... and {len(rooms) - 30} more")
    print_box(lines, title="OCCUPIED ROOMS")
