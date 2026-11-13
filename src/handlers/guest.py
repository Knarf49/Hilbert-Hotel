import questionary
from src.handlers import print_box


def handle_add_guests(cli):
    if not cli.system:
        print_box("Please initialize system first.", title="WARNING")
        return

    mode = questionary.select("Add mode:", choices=["Single Guest", "Batch Guests", "Back"]).ask()
    if mode == "Single Guest":
        c = questionary.text("Channel ID:").ask()
        s = questionary.text("Sequence ID:").ask()
        try:
            c_val, s_val = int(c), int(s)
            ok = cli.system.add_single_guest(c_val, s_val)
            if ok:
                loc = cli.system.search_by_guest(c_val, s_val)
                if loc:
                    msg = f"Guest ({c_val}, {s_val}) added. Assigned to Building {loc[0]}, Room {loc[1]}."
                else:
                    msg = f"Guest ({c_val}, {s_val}) added."
                print_box(msg, title="ADD GUEST")
            else:
                print_box("Failed to add guest (duplicate or invalid input).", title="ADD GUEST")
        except (ValueError, TypeError):
            print_box("Invalid input.", title="ERROR")
    elif mode == "Batch Guests":
        c = questionary.text("Channel ID:").ask()
        s_start = questionary.text("Start Sequence ID:").ask()
        count = questionary.text("Count:").ask()
        try:
            c_val, s_val, count_val = int(c), int(s_start), int(count)
            ok = cli.system.add_guest_batch(c_val, s_val, count_val)
            if ok:
                print_box(f"Batch of {count_val} guests added successfully.", title="ADD GUEST BATCH")
            else:
                print_box("Batch rejected (duplicate detected or invalid input).", title="ADD GUEST BATCH")
        except (ValueError, TypeError):
            print_box("Invalid input.", title="ERROR")


def handle_remove_guest(cli):
    if not cli.system:
        print_box("Please initialize system first.", title="WARNING")
        return

    c = questionary.text("Channel ID:").ask()
    s = questionary.text("Sequence ID:").ask()
    try:
        ok = cli.system.remove_guest(int(c), int(s))
        if ok:
            print_box(f"Guest ({c}, {s}) removed successfully.", title="REMOVE GUEST")
        else:
            print_box(f"Guest ({c}, {s}) not found.", title="REMOVE GUEST")
    except (ValueError, TypeError):
        print_box("Invalid input.", title="ERROR")
