"""Contribution card. Compact and regular stay numeric. Wide adds a glyph year."""

import sys
from pathlib import Path

from frame import dots, label, open_svg, week_glyphs
from github_user import contributions
from nothing import MODES, SIZES, theme

ROOT = Path(__file__).resolve().parent


def render(mode, size, data):
    if size == "mini":
        return _mini(mode, data)
    if size == "compact":
        return _compact(mode, data)
    if size == "wide":
        return _wide(mode, data)
    return _regular(mode, data)


def _colors(mode):
    return theme(mode)


def _mini(mode, data):
    colors = _colors(mode)
    name, _ = dots("CONTRIBUTIONS", 28, 12, colors["fg"], scale=1.15)
    return "\n".join([
        open_svg(mode, 220, 148, f"{data['login']} contributions", mark=6, margin=14),
        name,
        label(16, 108, f"{data['last_year']:,}", colors["figure"], 28, -0.8),
        label(16, 130, "12 months", colors["muted"], 11, 0.3),
        "</svg>",
    ])


def _compact(mode, data):
    colors = _colors(mode)
    name, _ = dots("CONTRIBUTIONS", 40, 16, colors["fg"], scale=1.8)
    return "\n".join([
        open_svg(mode, 495, 132, f"{data['login']} contributions"),
        name,
        label(20, 108, f"{data['last_year']:,}", colors["figure"], 36, -1),
        label(280, 86, "Last 12 months", colors["muted"], 13, 0.4),
        label(280, 108, f"@{data['login']}", colors["fg"], 14, 0.2),
        "</svg>",
    ])


def _regular(mode, data):
    colors = _colors(mode)
    name, _ = dots("CONTRIBUTIONS", 40, 16, colors["fg"], scale=1.8)
    return "\n".join([
        open_svg(mode, 495, 195, f"{data['login']} contributions"),
        name,
        label(20, 118, f"{data['last_year']:,}", colors["figure"], 32, -0.8),
        label(250, 118, f"{data['all_time']:,}", colors["figure"], 32, -0.8),
        label(20, 142, "Last 12 months", colors["muted"], 12, 0.4),
        label(250, 142, f"Since {data['since']}", colors["muted"], 12, 0.4),
        f'<line x1="20" y1="158" x2="475" y2="158" stroke="{colors["rule"]}"/>',
        label(20, 180, f"@{data['login']} · {data['stars']} {data['stars_label']}", colors["fg"], 12, 0.2),
        "</svg>",
    ])


def _wide(mode, data):
    colors = _colors(mode)
    name, _ = dots("CONTRIBUTIONS", 40, 16, colors["fg"], scale=1.8)
    glyphs = week_glyphs(data["days"], 32, 310, 72, 12, 3, colors["figure"], colors["rule"])
    return "\n".join([
        open_svg(mode, 896, 240, f"{data['login']} contributions"),
        name,
        label(20, 120, f"{data['last_year']:,}", colors["figure"], 40, -1),
        label(20, 148, "Last 12 months", colors["muted"], 13, 0.4),
        label(20, 200, f"{data['all_time']:,} since {data['since']}", colors["fg"], 14, 0.2),
        glyphs,
        label(310, 214, "Last 32 weeks", colors["muted"], 12, 0.4),
        "</svg>",
    ])


def _variant(card, login, mode, size, filename):
    url = f"https://github.com/itsrealkaran/{card}?username={login}&theme={mode}&size={size}"
    return [
        f"**{card}** · {mode} · {size}",
        "",
        f"`{url}`",
        "",
        f"![{card} {mode} {size}](dist/{login}/{filename})",
        "",
    ]


def main():
    login = sys.argv[1] if len(sys.argv) > 1 else "itsrealkaran"
    data = contributions(login)
    out = ROOT / "dist" / data["login"]
    out.mkdir(parents=True, exist_ok=True)
    lines = [f"# {data['login']}", "", "Mini is the short rectangle. Compact and regular are number widgets. Wide is the glyph widget.", ""]
    for mode in MODES:
        lines += [f"## {mode}", ""]
        for size in SIZES:
            filename = f"{mode}-{size}.svg"
            (out / filename).write_text(render(mode, size, data))
            lines += _variant("contributions", data["login"], mode, size, filename)
            print(data["login"], mode, size)
    (ROOT / "DUMMY.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
