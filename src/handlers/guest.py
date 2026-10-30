import questionary


def handle_add_guests(cli):
    if not cli.system:
        print("Please initialize system first.")
        return

    mode = questionary.select("Add mode:", choices=["Single Guest", "Batch Guests", "Back"]).ask()
    if mode == "Single Guest":
        c = questionary.text("Channel ID:").ask()
        s = questionary.text("Sequence ID:").ask()
        try:
            fn = getattr(cli.system, "add_single_guest", getattr(cli.system, "add_guest", None))
            ok = fn(int(c), int(s)) if fn else False
            print("Guest added." if ok else "Failed. Duplicate or invalid.")
        except (ValueError, TypeError):
            print("Invalid input.")
    elif mode == "Batch Guests":
        c = questionary.text("Channel ID:").ask()
        s_start = questionary.text("Start Sequence ID:").ask()
        count = questionary.text("Count:").ask()
        try:
            fn = getattr(cli.system, "add_guest_batch", None)
            ok = fn(int(c), int(s_start), int(count)) if fn else False
            print("Batch added." if ok else "Batch rejected (collision detected).")
        except (ValueError, TypeError):
            print("Invalid input.")


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
