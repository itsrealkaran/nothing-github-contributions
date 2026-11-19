"""Contribution card for any GitHub username."""

import sys
from pathlib import Path

from frame import dots, label, open_svg
from github_user import contributions
from nothing import MODES, SCALE, SIZES, theme

ROOT = Path(__file__).resolve().parent


def render(mode, size, data):
    scale = SCALE[size]
    colors = theme(mode)
    width = int(640 * scale)
    height = int(260 * scale)

    def n(value):
        return round(value * scale, 1)

    name, _ = dots("CONTRIBUTIONS", n(46), n(22), colors["fg"], scale=2.1 * scale)
    parts = [
        open_svg(mode, width, height, f"{data['login']} contributions"),
        name,
        label(n(28), n(168), f"{data['last_year']:,}", colors["figure"], n(42), -0.8),
        label(n(330), n(168), f"{data['all_time']:,}", colors["figure"], n(42), -0.8),
        label(n(28), n(196), "Last 12 months", colors["muted"], n(13), 0.6),
        label(n(330), n(196), f"Since {data['since']}", colors["muted"], n(13), 0.6),
        f'<line x1="{n(28)}" y1="{n(216)}" x2="{width - n(28)}" y2="{n(216)}" stroke="{colors["rule"]}"/>',
        label(n(28), n(240), f"@{data['login']} · {data['stars']} {data['stars_label']}", colors["fg"], n(13), 0.2),
        "</svg>",
    ]
    return "\n".join(parts)


def main():
    login = sys.argv[1] if len(sys.argv) > 1 else "itsrealkaran"
    data = contributions(login)
    out = ROOT / "dist" / data["login"]
    out.mkdir(parents=True, exist_ok=True)
    lines = [f"# {data['login']}", "", "Username, mode, and size.", ""]
    for mode in MODES:
        lines += [f"## {mode}", ""]
        for size in SIZES:
            filename = f"{mode}-{size}.svg"
            (out / filename).write_text(render(mode, size, data))
            lines += [f"### {size}", "", f"![{mode} {size}](dist/{data['login']}/{filename})", ""]
            print(data["login"], mode, size)
    (ROOT / "DUMMY.md").write_text("\n".join(lines))


if __name__ == "__main__":
    main()
