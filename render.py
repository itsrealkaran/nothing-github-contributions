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
    """Portrait and name, the last year, then the recent weeks."""
    colors = _colors(mode)
    portrait = data.get("glyph") or []
    parts = [
        open_svg(
            mode, 220, 182, f"{data['login']} contributions",
            mark=0 if portrait else 6, margin=14,
        ),
    ]
    name_x = 60 if portrait else 28
    if portrait:
        parts.append(_portrait(portrait, 14, 12, 40, colors, mode))
    parts.append(label(name_x, 28, data["name"], colors["fg"], 13, 0))
    parts.append(label(name_x, 46, f"@{data['login']}", colors["muted"], 11, 0.2))
    scale = 2.2
    top = 62
    drawn, visual = _figure(f"{data['last_year']:,}", 16, top, colors["figure"], scale)
    parts.append(drawn)
    parts.append(label(
        16 + visual + 8, top + _figure_height(scale) - 2,
        "Last year", colors["muted"], 11, 0.2,
    ))
    if mode.endswith("-r"):
        parts.append(f'<rect x="200" y="14" width="6" height="6" fill="{colors["mark"]}"/>')
    parts.append(_graph(data["days"], 16, 98, 53, 8, 2, colors, show=19, accent=_accent(mode, colors)))
    parts.append("</svg>")
    return "\n".join(parts)


def _compact(mode, data):
    colors = _colors(mode)
    parts = [
        _open(mode, 495, 168, data),
        *_who(data, colors, 495, mode),
        *([_rule(20, 475, 76, colors, mode)] if mode.endswith("-r") else []),
        *_stats(data, colors, 495, 108, 132),
    ]
    return "\n".join(parts + ["</svg>"])


def _regular(mode, data):
    colors = _colors(mode)
    graph = _graph(data["days"], 20, 78, 53, 6, 2, colors, accent=_accent(mode, colors))
    parts = [
        _open(mode, 495, 250, data),
        *_who(data, colors, 495, mode),
        graph,
        *_year_line(data, colors, 20, 156),
        _rule(20, 475, 176, colors, mode),
        *_stats(data, colors, 495, 206, 228),
    ]
    return "\n".join(parts + ["</svg>"])


def _wide(mode, data):
    colors = _colors(mode)
    graph = _graph(data["days"], 20, 88, 53, 13, 3, colors, accent=_accent(mode, colors))
    parts = [
        _open(mode, 896, 318, data),
        *_who(data, colors, 896, mode, total_size=28),
        graph,
        *_year_line(data, colors, 20, 224),
        _rule(20, 876, 248, colors, mode),
        *_stats(data, colors, 896, 278, 300),
        _languages(data, colors, 876, 224),
    ]
    return "\n".join(parts + ["</svg>"])


def _accent(mode, colors):
    """N-Red on the latest day of an -r card. Kept off the portrait."""
    return colors["mark"] if mode.endswith("-r") else None


def _rule(x1, x2, y, colors, mode):
    stroke = colors["mark"] if mode.endswith("-r") else colors["rule"]
    return f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{stroke}"/>'


def _open(mode, width, height, data):
    mark = 0 if data.get("glyph") else 8
    return open_svg(mode, width, height, f"{data['login']} contributions", mark=mark)


def _who(data, colors, width, mode, total_size=22):
    portrait = data.get("glyph") or []
    if portrait:
        head = [
            _portrait(portrait, 18, 14, 48, colors, mode),
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


def _portrait(dots, x, y, size, colors, mode):
    """The original glyph, clipped to a circle. The face uses the figure colour."""
    step = size / 18
    radius = {1: step * 0.28, 2: step * 0.38, 3: step * 0.46}
    contour = colors["figure"] if mode in ("red", "blue", "yellow") else colors["muted"]
    fill = {1: contour, 2: colors["figure"], 3: colors["figure"]}
    cx0 = x + size / 2
    cy0 = y + size / 2
    parts = [
        f'<clipPath id="pfp"><circle cx="{cx0:.2f}" cy="{cy0:.2f}" r="{size / 2:.2f}"/></clipPath>',
        '<g clip-path="url(#pfp)">',
    ]
    for col, row, kind in dots:
        parts.append(
            f'<circle cx="{x + (col + 0.5) * step:.2f}" cy="{y + (row + 0.5) * step:.2f}" '
            f'r="{radius[kind]:.2f}" fill="{fill[kind]}"/>'
        )
    parts.append("</g>")
    ring = colors["mark"] if mode.endswith("-r") else contour
    parts.append(
        f'<circle cx="{cx0:.2f}" cy="{cy0:.2f}" r="{size / 2:.2f}" fill="none" '
        f'stroke="{ring}" stroke-width="0.75"/>'
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
            word = "DAY" if count == 1 else "DAYS"
            parts.append(_unit(word, x + visual + 8, top, scale, colors["muted"]))
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


def _unit(word, x, number_top, number_scale, fill, measure=False):
    """A lighter day word, smaller than the count and sitting on its baseline."""
    scale = max(1.05, round(number_scale * 0.62, 2))
    top = number_top + _figure_height(number_scale) - _figure_height(scale)
    drawn, visual = _figure(word, x, top, fill, scale, weight=0.85)
    return (drawn, visual) if measure else drawn


def _figure(text, x, y, fill, scale, weight=1.4):
    drawn, width = dots(text, x, y, fill, scale=scale, weight=weight)
    return drawn, width - (scale + 1.1)


def _figure_end(text, right, y, fill, scale):
    _drawn, visual = _figure(text, 0, y, fill, scale)
    drawn, _visual = _figure(text, right - visual, y, fill, scale)
    return drawn


def _count(count, x, y, colors, scale, caption):
    """A dot-grid count, the unit in a lighter grid, then the caption."""
    drawn, visual = _figure(f"{count:,}", x, y, colors["figure"], scale)
    word = "DAY" if count == 1 else "DAYS"
    word_x = x + visual + 8
    unit_drawn, unit_visual = _unit(word, word_x, y, scale, colors["muted"], measure=True)
    return [
        drawn,
        unit_drawn,
        label(word_x + unit_visual + 10, _unit_line(y, scale, 13), caption, colors["muted"], 13, 0.15),
    ]


# A day lights squares in reading order: one, the top pair, an L, then the block.
def _graph(days, x, y, weeks, cell, gap, colors, show=None, accent=None):
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
    latest = None
    for week, row, count in cells:
        if week < origin:
            continue
        rank = level(count)
        if rank == 0:
            fill, extra = colors["rule"], ""
        else:
            fill = colors["figure"]
            extra = f' opacity="{opacity[rank]}"' if rank in opacity else ""
        latest = (week, row)
        parts.append(
            f'<rect x="{x + (week - origin) * step}" y="{y + row * step}" width="{cell}" height="{cell}" '
            f'fill="{fill}"{extra}/>'
        )
    if accent and latest:
        week, row = latest
        parts.append(
            f'<rect x="{x + (week - origin) * step}" y="{y + row * step}" width="{cell}" height="{cell}" '
            f'fill="{accent}"/>'
        )
    return "".join(parts)


def _variant(card, login, mode, size, filename, glyph=True):
    url = f"https://github.com/itsrealkaran/nothing-github-contributions?username={login}&theme={mode}&size={size}"
    if not glyph:
        url += "&glyph=0"
    shown = f"{mode} · {size}" if glyph else f"{mode} · {size} · glyph=0"
    return [
        f"**{card}** · {shown}",
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
