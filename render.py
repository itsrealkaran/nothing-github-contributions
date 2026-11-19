"""Contribution card. Five Nothing modes."""

import json
from pathlib import Path

from frame import dots, label, open_svg
from nothing import MODES, theme

ROOT = Path(__file__).resolve().parent


def render(mode, data):
    colors = theme(mode)
    name, _ = dots("CONTRIBUTIONS", 46, 22, colors["fg"], scale=2.1)
    width, height = 640, 250
    parts = [
        open_svg(mode, width, height, "Contributions, public and private"),
        name,
        label(28, 168, f'{data["last_year"]:,}', colors["figure"], 42, -0.8),
        label(330, 168, f'{data["all_time"]:,}', colors["figure"], 42, -0.8),
        label(28, 196, "Last 12 months", colors["muted"], 13, 0.6),
        label(330, 196, "Since Oct 2022", colors["muted"], 13, 0.6),
        f'<line x1="28" y1="214" x2="612" y2="214" stroke="{colors["rule"]}"/>',
        label(28, 236, f'{data["stars"]} stars on owned repos', colors["fg"], 13, 0.2),
        "</svg>",
    ]
    return "\n".join(parts)


def main():
    data = json.loads((ROOT / "sample.json").read_text())
    out = ROOT / "dist"
    out.mkdir(exist_ok=True)
    for mode in MODES:
        (out / f"{mode}.svg").write_text(render(mode, data))
        print(mode)


if __name__ == "__main__":
    main()
