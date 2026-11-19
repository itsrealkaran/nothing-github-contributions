"""Contribution card. A year grid, then the streak and the stars."""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from frame import dots, label, open_svg
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
    """Glyph and the last year, then the recent weeks at a size you can read."""
    colors = _colors(mode)
    portrait = data.get("glyph") or []
    parts = [
        open_svg(
            mode, 220, 184, f"{data['login']} contributions",
            mark=0 if portrait else 6, margin=14,
        ),
    ]
    if portrait:
        count, _ = _figure(f"{data['last_year']:,}", 70, 22, colors["figure"], 2.6)
        parts.append(_portrait(portrait, 14, 14, 46, colors))
        parts.append(count)
        parts.append(label(70, 62, "Last year", colors["muted"], 11, 0.3))
    else:
        count, _ = _figure(f"{data['last_year']:,}", 28, 24, colors["figure"], 3)
        parts.append(count)
        parts.append(label(28, 68, "Last year", colors["muted"], 11, 0.3))
    parts.append(_graph(data["days"], 16, 80, 53, 8, 2, colors, show=19))
    parts.extend(_count(data["current"], "day", 16, 156, colors, 1.5, "Current"))
    parts.append("</svg>")
    return "\n".join(parts)


def _compact(mode, data):
    colors = _colors(mode)
    parts = [
        _open(mode, 495, 168, data),
        *_who(data, colors, 495),
        *_stats(data, colors, 495, 108, 132),
    ]
    return "\n".join(parts + ["</svg>"])


def _regular(mode, data):
    colors = _colors(mode)
    graph = _graph(data["days"], 20, 78, 53, 6, 2, colors)
    parts = [
        _open(mode, 495, 250, data),
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
        _open(mode, 896, 318, data),
        *_who(data, colors, 896, total_size=28),
        graph,
        *_year_line(data, colors, 20, 224),
        f'<line x1="20" y1="248" x2="876" y2="248" stroke="{colors["rule"]}"/>',
        *_stats(data, colors, 896, 278, 300),
        _languages(data, colors, 876, 224),
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
    scale = 3.4 if total_size >= 26 else 2.8
    return head + [
        _figure_end(f"{data['all_time']:,}", width - 20, 16, colors["figure"], scale),
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
    scale = 1.55
    top = y - _figure_height(scale) + 2
    drawn, visual = _figure(f"{data['last_year']:,}", x, top, colors["figure"], scale)
    return [
        drawn,
        label(x + visual + 8, y, "contributions in the last year", colors["muted"], 13, 0.15),
    ]


def _stats(data, colors, width, number_y, caption_y):
    scale = 2.2
    top = number_y - _figure_height(scale) + 2
    columns = (
        (data["longest"], "day", "Longest streak"),
        (data["current"], "day", "Current streak"),
        (data["stars"], "", "Stars"),
    )
    span = width / 3
    parts = []
    for index, (count, unit, caption) in enumerate(columns):
        x = 20 if index == 0 else span * index
        drawn, visual = _figure(f"{count:,}", x, top, colors["figure"], scale)
        parts.append(drawn)
        if unit:
            word = unit if count == 1 else f"{unit}s"
            parts.append(label(x + visual + 6, _unit_line(top, scale, 14), word, colors["figure"], 14, 0.1))
        parts.append(label(x, caption_y, caption, colors["muted"], 12, 0.2))
    return parts


def _languages(data, colors, x, y):
    rows = data.get("languages") or []
    if not rows:
        return ""
    text = "  ·  ".join(f"{name} {share}%" for name, share in rows)
    return label(x, y, text, colors["muted"], 12, 0.15, anchor="end")


def _figure_height(scale):
    return 6 * (scale + 1.1) + scale


def _unit_line(top, scale, size):
    """Baseline that sits a unit on the same line as a dot-grid figure."""
    return top + _figure_height(scale) / 2 + size * 0.32


def _figure(text, x, y, fill, scale):
    drawn, width = dots(text, x, y, fill, scale=scale)
    return drawn, width - (scale + 1.1)


def _figure_end(text, right, y, fill, scale):
    _drawn, visual = _figure(text, 0, y, fill, scale)
    drawn, _visual = _figure(text, right - visual, y, fill, scale)
    return drawn


def _count(count, unit, x, y, colors, scale, caption):
    """A dot-grid count, its unit, and a muted caption on one line."""
    drawn, visual = _figure(f"{count:,}", x, y, colors["figure"], scale)
    word = unit if count == 1 else f"{unit}s"
    baseline = _unit_line(y, scale, 13)
    word_x = x + visual + 6
    return [
        drawn,
        label(word_x, baseline, word, colors["figure"], 13, 0.1),
        label(word_x + len(word) * 8 + 10, baseline, caption, colors["muted"], 13, 0.15),
    ]


# A day lights squares in reading order: one, the top pair, an L, then the block.
def _graph(days, x, y, weeks, cell, gap, colors, show=None):
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
    shown = weeks if show is None else show
    origin = weeks - shown
    parts = []
    for week, row, count in cells:
        if week < origin:
            continue
        rank = level(count)
        fill = colors["rule"] if rank == 0 else colors["figure"]
        extra = f' opacity="{opacity[rank]}"' if rank in opacity else ""
        parts.append(
            f'<rect x="{x + (week - origin) * step}" y="{y + row * step}" width="{cell}" height="{cell}" '
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
