"use strict";

const { dots, label, openSvg } = require("./frame");
const { theme } = require("./nothing");
const { add, commas, f, fixed, pyRound, sub } = require("./format");

function render(mode, size, data) {
  if (size === "mini") return mini(mode, data);
  if (size === "compact") return compact(mode, data);
  if (size === "wide") return wide(mode, data);
  return regular(mode, data);
}

function mini(mode, data) {
  const colors = theme(mode);
  const portrait = shown(data);
  const parts = [
    openSvg(mode, 220, 182, data.login + " contributions", portrait ? 0 : 6, 14),
  ];
  const nameX = portrait ? 60 : 28;
  if (portrait) parts.push(place(data, 14, 12, 40, colors, mode));
  parts.push(label(nameX, 28, data.name, colors.fg, 13, 0));
  parts.push(label(nameX, 46, "@" + data.login, colors.muted, 11, 0.2));
  const scale = 2.2;
  const top = 62;
  const [drawn, visual] = figure(commas(data.last_year), 16, top, colors.figure, scale);
  parts.push(drawn);
  parts.push(label(
    add(add(16, visual), 8),
    sub(add(top, f(figureHeight(scale))), 2),
    "Last year",
    colors.muted,
    11,
    0.2
  ));
  if (mode.endsWith("-r")) parts.push(`<rect x="200" y="14" width="6" height="6" fill="${colors.mark}"/>`);
  parts.push(graph(data.days, 16, 98, 53, 8, 2, colors, 19, accent(mode, colors)));
  parts.push("</svg>");
  return parts.join("\n");
}

function compact(mode, data) {
  const colors = theme(mode);
  const parts = [
    open(mode, 495, 168, data),
    ...who(data, colors, 495, mode),
    ...(mode.endsWith("-r") ? [rule(20, 475, 76, colors, mode)] : []),
    ...stats(data, colors, 495, 108, 132),
    "</svg>",
  ];
  return parts.join("\n");
}

function regular(mode, data) {
  const colors = theme(mode);
  const parts = [
    open(mode, 495, 250, data),
    ...who(data, colors, 495, mode),
    graph(data.days, 20, 78, 53, 6, 2, colors, null, accent(mode, colors)),
    ...yearLine(data, colors, 20, 156),
    rule(20, 475, 176, colors, mode),
    ...stats(data, colors, 495, 206, 228),
    "</svg>",
  ];
  return parts.join("\n");
}

function wide(mode, data) {
  const colors = theme(mode);
  const parts = [
    open(mode, 896, 318, data),
    ...who(data, colors, 896, mode, 28),
    graph(data.days, 20, 88, 53, 13, 3, colors, null, accent(mode, colors)),
    ...yearLine(data, colors, 20, 224),
    rule(20, 876, 248, colors, mode),
    ...stats(data, colors, 896, 278, 300),
    languages(data, colors, 876, 224),
    "</svg>",
  ];
  return parts.join("\n");
}

function accent(mode, colors) {
  return mode.endsWith("-r") ? colors.mark : null;
}

function rule(x1, x2, y, colors, mode) {
  const stroke = mode.endsWith("-r") ? colors.mark : colors.rule;
  return `<line x1="${x1}" y1="${y}" x2="${x2}" y2="${y}" stroke="${stroke}"/>`;
}

function open(mode, width, height, data) {
  const mark = shown(data) ? 0 : 8;
  return openSvg(mode, width, height, data.login + " contributions", mark);
}

function who(data, colors, width, mode, totalSize = 22) {
  const head = shown(data)
    ? [
      place(data, 18, 14, 48, colors, mode),
      label(78, 36, data.name, colors.fg, 16, 0),
      label(78, 56, "@" + data.login, colors.muted, 12, 0.2),
    ]
    : [
      label(40, 36, data.name, colors.fg, 16, 0),
      label(40, 56, "@" + data.login, colors.muted, 12, 0.2),
    ];
  const scale = totalSize >= 26 ? 3.4 : 2.8;
  return head.concat([
    figureEnd(commas(data.all_time), width - 20, 16, colors.figure, scale),
    label(width - 20, 60, "contributions since " + data.year, colors.muted, 12, 0.2, "end"),
  ]);
}

function shown(data) {
  return Boolean((data.glyph && data.glyph.length) || data.photo);
}

function place(data, x, y, size, colors, mode) {
  if (data.photo) return photoMark(data.photo, x, y, size, colors, mode);
  return portraitMark(data.glyph || [], x, y, size, colors, mode);
}

function photoMark(href, x, y, size, colors, mode) {
  const cx0 = x + size / 2;
  const cy0 = y + size / 2;
  const contour = mode === "red" || mode === "blue" || mode === "yellow" ? colors.figure : colors.muted;
  const ring = mode.endsWith("-r") ? colors.mark : contour;
  return (
    `<clipPath id="pfp"><circle cx="${fixed(cx0, 2)}" cy="${fixed(cy0, 2)}" r="${fixed(size / 2, 2)}"/></clipPath>` +
    `<image href="${href}" x="${x}" y="${y}" width="${size}" height="${size}" ` +
    `clip-path="url(#pfp)" preserveAspectRatio="xMidYMid slice"/>` +
    `<circle cx="${fixed(cx0, 2)}" cy="${fixed(cy0, 2)}" r="${fixed(size / 2, 2)}" fill="none" ` +
    `stroke="${ring}" stroke-width="0.75"/>`
  );
}

function portraitMark(cells, x, y, size, colors, mode) {
  const step = size / 18;
  const radius = { 1: step * 0.28, 2: step * 0.38, 3: step * 0.46 };
  const contour = mode === "red" || mode === "blue" || mode === "yellow" ? colors.figure : colors.muted;
  const fill = { 1: contour, 2: colors.figure, 3: colors.figure };
  const cx0 = x + size / 2;
  const cy0 = y + size / 2;
  const parts = [
    `<clipPath id="pfp"><circle cx="${fixed(cx0, 2)}" cy="${fixed(cy0, 2)}" r="${fixed(size / 2, 2)}"/></clipPath>`,
    '<g clip-path="url(#pfp)">',
  ];
  for (const cell of cells) {
    const col = cell[0];
    const row = cell[1];
    const kind = cell[2];
    parts.push(
      `<circle cx="${fixed(x + (col + 0.5) * step, 2)}" cy="${fixed(y + (row + 0.5) * step, 2)}" ` +
      `r="${fixed(radius[kind], 2)}" fill="${fill[kind]}"/>`
    );
  }
  parts.push("</g>");
  const ring = mode.endsWith("-r") ? colors.mark : contour;
  parts.push(
    `<circle cx="${fixed(cx0, 2)}" cy="${fixed(cy0, 2)}" r="${fixed(size / 2, 2)}" fill="none" ` +
    `stroke="${ring}" stroke-width="0.75"/>`
  );
  return parts.join("");
}

function yearLine(data, colors, x, y) {
  const scale = 1.55;
  const top = y - figureHeight(scale) + 2;
  const [drawn, visual] = figure(commas(data.last_year), x, top, colors.figure, scale);
  return [
    drawn,
    label(add(add(x, visual), 8), y, "contributions in the last year", colors.muted, 13, 0.15),
  ];
}

function stats(data, colors, width, numberY, captionY) {
  const scale = 2.2;
  const top = numberY - figureHeight(scale) + 2;
  const columns = [
    [data.longest, "day", "Longest streak"],
    [data.current, "day", "Current streak"],
    [data.stars, "", "Stars"],
  ];
  const span = width / 3;
  const parts = [];
  columns.forEach(([count, unit, caption], index) => {
    const x = index === 0 ? 20 : f(span * index);
    const [drawn, visual] = figure(commas(count), x, top, colors.figure, scale);
    parts.push(drawn);
    if (unit) {
      const word = count === 1 ? "DAY" : "DAYS";
      parts.push(unitWord(word, add(add(x, visual), 8), top, scale, colors.muted));
    }
    parts.push(label(x, captionY, caption, colors.muted, 12, 0.2));
  });
  return parts;
}

function languages(data, colors, x, y) {
  const rows = data.languages || [];
  if (!rows.length) return "";
  const text = rows.map(([name, share]) => name + " " + share + "%").join("  ·  ");
  return label(x, y, text, colors.muted, 12, 0.15, "end");
}

function figureHeight(scale) {
  return 6 * (scale + 1.1) + scale;
}

function unitWord(word, x, numberTop, numberScale, fill) {
  const scale = Math.max(1.05, pyRound(numberScale * 0.62, 2));
  const top = numberTop + figureHeight(numberScale) - figureHeight(scale);
  const [drawn] = figure(word, x, top, fill, scale, 0.85);
  return drawn;
}

function figure(text, x, y, fill, scale, weight = 1.4) {
  const [drawn, width] = dots(text, x, y, fill, scale, weight);
  return [drawn, f(width - (scale + 1.1))];
}

function figureEnd(text, right, y, fill, scale) {
  const [, visual] = figure(text, 0, y, fill, scale);
  const [drawn] = figure(text, right - visual, y, fill, scale);
  return drawn;
}

function graph(days, x, y, weeks, cell, gap, colors, show, mark) {
  const byDay = new Map();
  for (const [day, count] of days || []) byDay.set(day, count);
  const now = new Date();
  const today = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()));
  const weekday = (today.getUTCDay() + 6) % 7;
  const sunday = new Date(today.getTime() - ((weekday + 1) % 7) * 86400000);
  const start = new Date(sunday.getTime() - (weeks - 1) * 7 * 86400000);
  const cells = [];
  const counted = [];
  for (let week = 0; week < weeks; week += 1) {
    for (let row = 0; row < 7; row += 1) {
      const day = new Date(start.getTime() + (week * 7 + row) * 86400000);
      if (day > today) continue;
      const key = iso(day);
      const count = byDay.get(key) || 0;
      cells.push([week, row, count]);
      if (count) counted.push(count);
    }
  }
  counted.sort((a, b) => a - b);
  function level(count) {
    if (count <= 0 || !counted.length) return 0;
    if (count <= counted[Math.floor(counted.length / 4)]) return 1;
    if (count <= counted[Math.floor(counted.length / 2)]) return 2;
    if (count <= counted[Math.floor((3 * counted.length) / 4)]) return 3;
    return 4;
  }
  const opacity = { 1: "0.35", 2: "0.55", 3: "0.78" };
  const step = cell + gap;
  const shown = show == null ? weeks : show;
  const origin = weeks - shown;
  const parts = [];
  let latest = null;
  for (const [week, row, count] of cells) {
    if (week < origin) continue;
    const rank = level(count);
    let fill = colors.figure;
    let extra = "";
    if (rank === 0) {
      fill = colors.rule;
    } else if (opacity[rank]) {
      extra = ` opacity="${opacity[rank]}"`;
    }
    latest = [week, row];
    parts.push(
      `<rect x="${x + (week - origin) * step}" y="${y + row * step}" width="${cell}" height="${cell}" ` +
      `fill="${fill}"${extra}/>`
    );
  }
  if (mark && latest) {
    const [week, row] = latest;
    parts.push(
      `<rect x="${x + (week - origin) * step}" y="${y + row * step}" width="${cell}" height="${cell}" fill="${mark}"/>`
    );
  }
  return parts.join("");
}

function iso(date) {
  const pad = (value) => String(value).padStart(2, "0");
  return date.getUTCFullYear() + "-" + pad(date.getUTCMonth() + 1) + "-" + pad(date.getUTCDate());
}

module.exports = { render };
