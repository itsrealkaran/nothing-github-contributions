"""Contribution card. A year of four-square days, then the streak and the stars."""

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
        open_svg(mode, 220, 164, f"{data['login']} contributions", mark=6, margin=14),
        label(28, 70, f"{data['last_year']:,}", colors["figure"], 28, -0.8),
        label(28, 90, "Last year", colors["muted"], 11, 0.3),
        _week(data["days"], 28, 106, 13, 5, colors),
        label(28, 148, _span(data["current"], "day"), colors["fg"], 12, 0.2),
        "</svg>",
    ])


def _compact(mode, data):
    colors = _colors(mode)
    parts = [
        _open(mode, 495, 168, data),
        *_who(data, colors, 495),
        _hline(colors, 20, 475, 76),
        *_stats(data, colors, 495, 116, 138, 92, 150),
    ]
    return "\n".join(parts + ["</svg>"])


def _regular(mode, data):
    colors = _colors(mode)
    graph = _graph(data["days"], 20, 82, 495, 53, 7, colors)
    parts = [
        _open(mode, 495, 250, data),
        *_who(data, colors, 495),
        _hline(colors, 20, 475, 70),
        graph,
        *_year_line(data, colors, 20, 164),
        *_stats(data, colors, 495, 204, 226, 182, 238),
    ]
    return "\n".join(parts + ["</svg>"])


def _wide(mode, data):
    colors = _colors(mode)
    graph = _graph(data["days"], 20, 88, 896, 53, 13, colors)
    parts = [
        _open(mode, 896, 318, data),
        *_who(data, colors, 896, total_size=28),
        _hline(colors, 20, 876, 74),
        graph,
        *_year_line(data, colors, 20, 222),
        _languages(data, colors, 876, 222),
        *_stats(data, colors, 896, 276, 298, 250, 310),
    ]
    return "\n".join(parts + ["</svg>"])


def _open(mode, width, height, data):
    mark = 0 if data.get("glyph") else 8
    return open_svg(mode, width, height, f"{data['login']} contributions", mark=mark)


def _who(data, colors, width, total_size=22):
    portrait = data.get("glyph") or []
    if portrait:
        head = [
            _portrait(portrait, 18, 14, 48, colors),
            label(78, 36, data["name"], colors["fg"], 16, 0),
            label(78, 56, f"@{data['login']}", colors["muted"], 12, 0.2),
        ]
    else:
        head = [
            label(40, 36, data["name"], colors["fg"], 16, 0),
            label(40, 56, f"@{data['login']}", colors["muted"], 12, 0.2),
        ]
    return head + [
        label(width - 20, 40, f"{data['all_time']:,}", colors["figure"], total_size, -0.6, anchor="end"),
        label(width - 20, 60, f"contributions since {data['year']}", colors["muted"], 12, 0.2, anchor="end"),
    ]


def _portrait(dots, x, y, size, colors):
    step = size / 18
    radius = {1: step * 0.28, 2: step * 0.38, 3: step * 0.46}
    fill = {1: colors["muted"], 2: colors["figure"], 3: colors["figure"]}
    parts = []
    for col, row, kind in dots:
        parts.append(
            f'<circle cx="{x + (col + 0.5) * step:.2f}" cy="{y + (row + 0.5) * step:.2f}" '
            f'r="{radius[kind]:.2f}" fill="{fill[kind]}"/>'
        )
    return "".join(parts)


def _year_line(data, colors, x, y):
    return [
        label(x, y, f"{data['last_year']:,}", colors["figure"], 13, 0),
        label(x + len(f"{data['last_year']:,}") * 8 + 8, y, "contributions in the last year", colors["muted"], 13, 0.15),
    ]


def _stats(data, colors, width, number_y, caption_y, rule_top, rule_bottom):
    columns = (
        (_span(data["longest"], "day"), "Longest streak"),
        (_span(data["current"], "day"), "Current streak"),
        (f"{data['stars']:,}", "Stars"),
    )
    span = width / 3
    parts = []
    for index in (1, 2):
        rule_x = round(span * index, 1)
        parts.append(
            f'<line x1="{rule_x}" y1="{rule_top}" x2="{rule_x}" y2="{rule_bottom}" stroke="{colors["rule"]}"/>'
        )
    for index, (number, caption) in enumerate(columns):
        x = round(span * (index + 0.5), 1)
        parts.append(label(x, number_y, number, colors["figure"], 18, -0.4, anchor="middle"))
        parts.append(label(x, caption_y, caption, colors["muted"], 12, 0.2, anchor="middle"))
    return parts


def _languages(data, colors, x, y):
    rows = data.get("languages") or []
    if not rows:
        return ""
    parts = []
    cursor = x
    for name, share in reversed(rows):
        text = f"{name} {share}%"
        parts.append(label(cursor, y, text, colors["muted"], 12, 0.15, anchor="end"))
        square = cursor - len(text) * 7.3 - 14
        parts.append(
            f'<rect x="{square:.1f}" y="{y - 10:.1f}" width="6" height="6" fill="{colors["figure"]}"/>'
        )
        cursor = square - 22
    return "".join(parts)


def _hline(colors, x1, x2, y):
    return f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{colors["rule"]}"/>'


def _span(count, word):
    unit = word if count == 1 else f"{word}s"
    return f"{count:,} {unit}"


# A day lights squares in reading order: one, the top pair, an L, then the block.
_DAY = ((0, 0), (1, 0), (0, 1), (1, 1))


def _graph(days, x, y, width, weeks, cell, colors):
    gap = (width - 40 - weeks * cell) / (weeks - 1)
    return _field(days, x, y, weeks, cell, gap, colors, horizontal=False)


def _week(days, x, y, cell, gap, colors):
    return _field(days, x, y, 1, cell, gap, colors, horizontal=True)


def _field(days, x, y, weeks, cell, gap, colors, horizontal):
    by_day = {}
    for day, count in days:
        by_day[datetime.strptime(day, "%Y-%m-%d").date()] = count
    today = datetime.now(timezone.utc).date()
    sunday = today - timedelta(days=(today.weekday() + 1) % 7)
    start = sunday - timedelta(weeks=weeks - 1)
    counted = []
    cells = []
    for week in range(weeks):
        for row in range(7):
            day = start + timedelta(days=week * 7 + row)
            if day > today:
                if not horizontal:
                    continue
                count = 0
            else:
                count = by_day.get(day, 0)
            cells.append((week, row, count))
            if count:
                counted.append(count)
    counted.sort()
    step = cell + gap
    parts = []
    for week, row, count in cells:
        origin_x = x + (row if horizontal else week) * step
        origin_y = y + (0 if horizontal else row) * step
        parts.append(_day(origin_x, origin_y, cell, _level(count, counted), colors))
    return "".join(parts)


def _level(count, counted):
    if count <= 0 or not counted:
        return 0
    if count <= counted[len(counted) // 4]:
        return 1
    if count <= counted[len(counted) // 2]:
        return 2
    if count <= counted[(3 * len(counted)) // 4]:
        return 3
    return 4


def _day(x, y, cell, rank, colors):
    sub = (cell - 1) / 2
    parts = []
    for index, (col, row) in enumerate(_DAY):
        fill = colors["figure"] if index < rank else colors["rule"]
        parts.append(
            f'<rect x="{x + col * (sub + 1):.1f}" y="{y + row * (sub + 1):.1f}" '
            f'width="{sub:.1f}" height="{sub:.1f}" fill="{fill}"/>'
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
    lines = [f"# {data['login']}", "", "The year is a field of equal squares. A day lights one more square at each step. Under it: the last year, the longest streak, the current streak, and stars.", ""]
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
