"use strict";

const { cells } = require("./glyph");
const {
  addDays,
  contributionTotals,
  dateOnly,
  dayKey,
  gh,
  mostCommon,
  parseDay,
  pyRound,
  request,
  utcNow,
} = require("./github");

async function load(login, options) {
  const glyph = !options || options.glyph !== false;
  const pfp = !options || options.pfp !== false;
  const data = await contributionTotals(login, { name: true });
  const [current, longest] = streaks(data.days);
  return {
    login: data.login,
    name: data.name,
    last_year: data.lastYear,
    all_time: data.allTime,
    stars: data.stars,
    stars_label: data.starsLabel,
    since: data.since,
    year: data.year,
    current,
    longest,
    languages: await topPublic(data.repos),
    days: data.days,
    glyph: pfp && glyph ? await portrait(login) : [],
    photo: pfp && !glyph ? await photo(login) : "",
  };
}

async function avatar(login) {
  const response = await request("https://github.com/" + login + ".png", {
    headers: { "User-Agent": "nothing-stat-card" },
  });
  if (response.status < 200 || response.status >= 300) return null;
  return response.body;
}

async function portrait(login) {
  try {
    const blob = await avatar(login);
    if (!blob) return [];
    return cells(blob);
  } catch (error) {
    return [];
  }
}

async function photo(login) {
  try {
    const blob = await avatar(login);
    if (!blob || !blob.length) return "";
    return "data:image/png;base64," + blob.toString("base64");
  } catch (error) {
    return "";
  }
}

function streaks(days) {
  const parsed = days.map(([day, count]) => [day, count]);
  parsed.sort((a, b) => (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0));
  let longest = 0;
  let run = 0;
  let previous = null;
  for (const [day, count] of parsed) {
    if (count <= 0) {
      run = 0;
      previous = day;
      continue;
    }
    const yesterday = dayKey(addDays(parseDay(day), -1));
    run = previous === yesterday && run ? run + 1 : 1;
    longest = Math.max(longest, run);
    previous = day;
  }
  const today = dayKey(dateOnly(utcNow()));
  const byDay = new Map(parsed);
  let cursor = (byDay.get(today) || 0) ? today : dayKey(addDays(parseDay(today), -1));
  let current = 0;
  while ((byDay.get(cursor) || 0) > 0) {
    current += 1;
    cursor = dayKey(addDays(parseDay(cursor), -1));
  }
  return [current, longest];
}

async function topPublic(repos) {
  const totals = new Map();
  for (const repo of repos) {
    if (repo.private || repo.fork) continue;
    const stats = await gh("repos/" + repo.full_name + "/languages");
    for (const [name, amount] of Object.entries(stats || {})) {
      totals.set(name, (totals.get(name) || 0) + amount);
    }
  }
  const grand = [...totals.values()].reduce((sum, value) => sum + value, 0) || 1;
  const rows = [];
  for (const [name, amount] of mostCommon(totals)) {
    const share = pyRound(100 * amount / grand);
    if (share <= 0) continue;
    rows.push([name, share]);
    if (rows.length === 3) break;
  }
  return rows;
}

module.exports = { load };
