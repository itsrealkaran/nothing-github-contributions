"""Contribution card. A year grid, then the streak and the stars."""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from frame import label, open_svg
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
    return "\n".join([
        open_svg(mode, 220, 148, f"{data['login']} contributions", mark=6, margin=14),
        label(28, 78, f"{data['last_year']:,}", colors["figure"], 28, -0.8),
        label(28, 100, "Last year", colors["muted"], 11, 0.3),
        label(28, 128, _span(data["current"], "day"), colors["fg"], 12, 0.2),
        "</svg>",
    ])


def _compact(mode, data):
    colors = _colors(mode)
    parts = [
        open_svg(mode, 495, 168, f"{data['login']} contributions"),
        *_who(data, colors, 495),
        *_stats(data, colors, 495, 108, 132),
    ]
    return "\n".join(parts + ["</svg>"])


def _regular(mode, data):
    colors = _colors(mode)
    graph = _graph(data["days"], 20, 78, 53, 6, 2, colors)
    parts = [
        open_svg(mode, 495, 250, f"{data['login']} contributions"),
        *_who(data, colors, 495),
        graph,
        *_year_line(data, colors, 20, 156),
        f'<line x1="20" y1="176" x2="475" y2="176" stroke="{colors["rule"]}"/>',
        *_stats(data, colors, 495, 206, 228),
    ]
    return "\n".join(parts + ["</svg>"])


def _wide(mode, data):
    colors = _colors(mode)
    graph = _graph(data["days"], 20, 88, 53, 13, 3, colors)
    parts = [
        open_svg(mode, 896, 318, f"{data['login']} contributions"),
        *_who(data, colors, 896, total_size=28),
        graph,
        *_year_line(data, colors, 20, 224),
        f'<line x1="20" y1="248" x2="876" y2="248" stroke="{colors["rule"]}"/>',
        *_stats(data, colors, 896, 278, 300),
        _languages(data, colors, 876, 224),
    ]
    return "\n".join(parts + ["</svg>"])


def _who(data, colors, width, total_size=22):
    return [
        label(40, 36, data["name"], colors["fg"], 16, 0),
        label(40, 56, f"@{data['login']}", colors["muted"], 12, 0.2),
        label(width - 20, 40, f"{data['all_time']:,}", colors["figure"], total_size, -0.6, anchor="end"),
        label(width - 20, 60, f"contributions since {data['year']}", colors["muted"], 12, 0.2, anchor="end"),
    ]


def _year_line(data, colors, x, y):
    return [
        label(x, y, f"{data['last_year']:,}", colors["figure"], 13, 0),
        label(x + len(f"{data['last_year']:,}") * 8 + 8, y, "contributions in the last year", colors["muted"], 13, 0.15),
    ]


def _stats(data, colors, width, number_y, caption_y):
    columns = (
        (_span(data["longest"], "day"), "Longest streak"),
        (_span(data["current"], "day"), "Current streak"),
        (f"{data['stars']:,}", "Stars"),
    )
    span = width / 3
    parts = []
    for index, (number, caption) in enumerate(columns):
        x = 20 if index == 0 else span * index
        anchor = "start"
        parts.append(label(x, number_y, number, colors["figure"], 18, -0.4, anchor=anchor))
        parts.append(label(x, caption_y, caption, colors["muted"], 12, 0.2, anchor=anchor))
    return parts


def _languages(data, colors, x, y):
    rows = data.get("languages") or []
    if not rows:
        return ""
    text = "  ·  ".join(f"{name} {share}%" for name, share in rows)
    return label(x, y, text, colors["muted"], 12, 0.15, anchor="end")


def _span(count, word):
    unit = word if count == 1 else f"{word}s"
    return f"{count:,} {unit}"


def _graph(days, x, y, weeks, cell, gap, colors):
    by_day = {}
    for day, count in days:
        by_day[datetime.strptime(day, "%Y-%m-%d").date()] = count
    today = datetime.now(timezone.utc).date()
    sunday = today - timedelta(days=(today.weekday() + 1) % 7)
    start = sunday - timedelta(weeks=weeks - 1)
    cells = []
    counted = []
    for week in range(weeks):
        for row in range(7):
            day = start + timedelta(days=week * 7 + row)
            if day > today:
                continue
            count = by_day.get(day, 0)
            cells.append((week, row, count))
            if count:
                counted.append(count)
    counted.sort()

    def level(count):
        if count <= 0 or not counted:
            return 0
        if count <= counted[len(counted) // 4]:
            return 1
        if count <= counted[len(counted) // 2]:
            return 2
        if count <= counted[(3 * len(counted)) // 4]:
            return 3
        return 4

    opacity = {1: "0.35", 2: "0.55", 3: "0.78"}
    step = cell + gap
    parts = []
    for week, row, count in cells:
        rank = level(count)
        fill = colors["rule"] if rank == 0 else colors["figure"]
        extra = f' opacity="{opacity[rank]}"' if rank in opacity else ""
        parts.append(
            f'<rect x="{x + week * step}" y="{y + row * step}" width="{cell}" height="{cell}" '
            f'fill="{fill}"{extra}/>'
        )
    return "".join(parts)


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
    lines = [f"# {data['login']}", "", "The year is a grid. Under it: the last year, the longest streak, the current streak, and stars.", ""]
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
