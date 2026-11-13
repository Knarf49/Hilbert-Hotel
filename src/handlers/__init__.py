from typing import Iterable, Union


def print_box(content: Union[str, Iterable[str]], title: str = "OUTPUT") -> None:
    """Render output lines inside a bordered Unicode box frame."""
    if isinstance(content, str):
        raw_lines = content.splitlines()
    else:
        raw_lines = []
        for item in content:
            split = str(item).splitlines()
            raw_lines.extend(split if split else [""])

    if not raw_lines:
        raw_lines = [""]

    header_label = f"─ [ {title} ] "
    max_line_len = max(len(line) for line in raw_lines)
    inner_width = max(54, max_line_len + 2, len(header_label) + 2)

    top_border = "┌" + header_label + "─" * (inner_width - len(header_label)) + "┐"
    bottom_border = "└" + "─" * inner_width + "┘"

    print(top_border)
    for line in raw_lines:
        print(f"│ {line.ljust(inner_width - 2)} │")
    print(bottom_border)
