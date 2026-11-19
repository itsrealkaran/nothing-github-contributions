"use strict";

const zlib = require("zlib");
const { pyRound } = require("./format");

const GRID = 18;
const ZZ = [
  0, 1, 8, 16, 9, 2, 3, 10, 17, 24, 32, 25, 18, 11, 4, 5, 12, 19, 26, 33,
  40, 48, 41, 34, 27, 20, 13, 6, 7, 14, 21, 28, 35, 42, 49, 56, 57, 50, 43, 36,
  29, 22, 15, 23, 30, 37, 44, 51, 58, 59, 52, 45, 38, 31, 39, 46, 53, 60, 61, 54,
  47, 55, 62, 63,
];
const COS = Array.from({ length: 8 }, (_, u) => (
  Array.from({ length: 8 }, (_, x) => Math.cos((2 * x + 1) * u * Math.PI / 16))
));

function cells(blob) {
  const image = decode(blob);
  if (!image) return [];
  const [width, height, rows] = image;
  const mask = subject(width, height, rows);
  const box = focus(width, height, rows, mask);
  if (!box) return [];
  const [left, top, right, bottom] = box;
  const sampled = resample(rows, mask, left, top, right, bottom, GRID);
  const kept = resampleMask(mask, width, height, left, top, right, bottom, GRID);
  const dots = [];
  for (let y = 0; y < GRID; y += 1) {
    for (let x = 0; x < GRID; x += 1) {
      if (!kept[y][x]) continue;
      const kind = edge(kept, x, y) ? 1 : tone(sampled[y][x]);
      if (kind) dots.push([x, y, kind]);
    }
  }
  return joined(dots);
}

function joined(dots) {
  const occupied = new Set(dots.map(([x, y]) => x + "," + y));
  return dots.filter(([x, y]) => (
    [[-1, 0], [1, 0], [0, -1], [0, 1]].some(([dx, dy]) => occupied.has((x + dx) + "," + (y + dy)))
  ));
}

function tone(pixel) {
  const luma = 0.2126 * pixel[0] + 0.7152 * pixel[1] + 0.0722 * pixel[2];
  if (luma >= 168) return 3;
  if (luma >= 96) return 2;
  return 0;
}

function edge(mask, x, y) {
  for (const [dx, dy] of [[-1, 0], [1, 0], [0, -1], [0, 1]]) {
    const nx = x + dx;
    const ny = y + dy;
    if (nx < 0 || ny < 0 || nx >= GRID || ny >= GRID || !mask[ny][nx]) return true;
  }
  return false;
}

function luma(red, green, blue) {
  return 0.2126 * red + 0.7152 * green + 0.0722 * blue;
}

function subject(width, height, rows) {
  let dark = 0;
  for (let y = 0; y < height; y += 2) {
    for (let x = 0; x < width; x += 2) {
      const pixel = rows[y][x];
      if (pixel[3] < 16 || luma(pixel[0], pixel[1], pixel[2]) < 28) dark += 1;
    }
  }
  const samples = Math.floor((height + 1) / 2) * Math.floor((width + 1) / 2);
  const background = Array.from({ length: height }, () => Array(width).fill(false));
  if (dark / samples > 0.62) {
    for (let y = 0; y < height; y += 1) {
      for (let x = 0; x < width; x += 1) {
        const pixel = rows[y][x];
        background[y][x] = pixel[3] < 16 || luma(pixel[0], pixel[1], pixel[2]) < 28;
      }
    }
    return background;
  }
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const pixel = rows[y][x];
      background[y][x] = room(pixel[0], pixel[1], pixel[2], pixel[3]);
    }
  }
  return background;
}

function skin(red, green, blue) {
  return red > 120 && green > 55 && blue < 175 && red > green + 12 && (red - blue) > 28 && green > blue;
}

function room(red, green, blue, alpha) {
  if (alpha < 16) return true;
  if (skin(red, green, blue)) return false;
  const chroma = Math.max(red, green, blue) - Math.min(red, green, blue);
  const light = luma(red, green, blue);
  if (light > 42 && chroma < 26) return true;
  return light > 165 && chroma < 42;
}

function focus(width, height, rows, background) {
  const xs = [];
  const ys = [];
  for (let y = 0; y < height; y += 2) {
    for (let x = 0; x < width; x += 2) {
      if (background[y][x]) continue;
      const pixel = rows[y][x];
      if (skin(pixel[0], pixel[1], pixel[2])) {
        xs.push(x);
        ys.push(y);
      }
    }
  }
  if (xs.length < 30) return bounds(background, width, height);
  const left = Math.min(...xs);
  const right = Math.max(...xs);
  const top = Math.min(...ys);
  const bottom = Math.max(...ys);
  const faceW = Math.max(1, right - left);
  const faceH = Math.max(1, bottom - top);
  return [
    Math.max(0, left - Math.floor(faceW / 4)),
    Math.max(0, top - Math.floor(faceH * 0.7)),
    Math.min(width, right + Math.floor(faceW / 4)),
    Math.min(height, bottom + Math.floor(faceH / 3)),
  ];
}

function bounds(background, width, height) {
  let left = width;
  let top = height;
  let right = 0;
  let bottom = 0;
  let found = false;
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      if (background[y][x]) continue;
      found = true;
      left = Math.min(left, x);
      top = Math.min(top, y);
      right = Math.max(right, x);
      bottom = Math.max(bottom, y);
    }
  }
  if (!found) return null;
  return [left, top, right + 1, bottom + 1];
}

function resample(rows, background, left, top, right, bottom, grid) {
  const spanX = right - left;
  const spanY = bottom - top;
  const sampled = [];
  for (let y = 0; y < grid; y += 1) {
    const row = [];
    const y0 = top + Math.floor(y * spanY / grid);
    const y1 = Math.max(y0 + 1, top + Math.floor((y + 1) * spanY / grid));
    for (let x = 0; x < grid; x += 1) {
      const x0 = left + Math.floor(x * spanX / grid);
      const x1 = Math.max(x0 + 1, left + Math.floor((x + 1) * spanX / grid));
      const total = [0, 0, 0];
      let count = 0;
      for (let py = y0; py < Math.min(y1, bottom); py += 1) {
        for (let px = x0; px < Math.min(x1, right); px += 1) {
          if (background[py][px]) continue;
          const pixel = rows[py][px];
          total[0] += pixel[0];
          total[1] += pixel[1];
          total[2] += pixel[2];
          count += 1;
        }
      }
      row.push(count ? total.map((channel) => Math.floor(channel / count)) : [0, 0, 0]);
    }
    sampled.push(row);
  }
  return sampled;
}

function resampleMask(background, width, height, left, top, right, bottom, grid) {
  const spanX = right - left;
  const spanY = bottom - top;
  const kept = [];
  for (let y = 0; y < grid; y += 1) {
    const row = [];
    const y0 = top + Math.floor(y * spanY / grid);
    const y1 = Math.max(y0 + 1, top + Math.floor((y + 1) * spanY / grid));
    for (let x = 0; x < grid; x += 1) {
      const x0 = left + Math.floor(x * spanX / grid);
      const x1 = Math.max(x0 + 1, left + Math.floor((x + 1) * spanX / grid));
      let subjectCount = 0;
      let total = 0;
      for (let py = y0; py < Math.min(y1, height); py += 1) {
        for (let px = x0; px < Math.min(x1, width); px += 1) {
          total += 1;
          if (!background[py][px]) subjectCount += 1;
        }
      }
      row.push(total && subjectCount / total >= 0.04);
    }
    kept.push(row);
  }
  return kept;
}

function decode(data) {
  if (data.length >= 8 && data[0] === 0x89 && data[1] === 0x50) return png(data);
  if (data.length >= 2 && data[0] === 0xff && data[1] === 0xd8) return jpeg(data);
  return null;
}

function jpeg(data) {
  const marked = jpegMarkers(data);
  if (!marked.frame || !marked.scan.length) return null;
  const [width, height, components] = marked.frame;
  if (components.some((item) => item[1] !== 8)) return null;
  const maxH = Math.max(...components.map((item) => item[2]));
  const maxV = Math.max(...components.map((item) => item[3]));
  const mcuW = 8 * maxH;
  const mcuH = 8 * maxV;
  const across = Math.floor((width + mcuW - 1) / mcuW);
  const down = Math.floor((height + mcuH - 1) / mcuH);
  const planes = {};
  const predictors = {};
  for (const item of components) {
    planes[item[0]] = Array.from({ length: down * mcuH }, () => Array(across * mcuW).fill(0));
    predictors[item[0]] = 0;
  }
  const reader = new Bits(marked.scan);
  try {
    for (let my = 0; my < down; my += 1) {
      for (let mx = 0; mx < across; mx += 1) {
        for (const plan of scanPlan(components, marked.tables)) {
          const [compId, , sampH, sampV, qt, dc, ac] = plan;
          const quant = marked.tables.q[qt];
          for (let vy = 0; vy < sampV; vy += 1) {
            for (let vx = 0; vx < sampH; vx += 1) {
              const block = readBlock(reader, marked.tables.h.get(key(0, dc)), marked.tables.h.get(key(1, ac)), predictors, compId);
              for (let index = 0; index < block.length; index += 1) block[index] *= quant[index];
              const spatial = idct(block);
              const scaleX = Math.floor(maxH / sampH);
              const scaleY = Math.floor(maxV / sampV);
              const originX = mx * mcuW + vx * 8 * scaleX;
              const originY = my * mcuH + vy * 8 * scaleY;
              const plane = planes[compId];
              for (let y = 0; y < 8; y += 1) {
                for (let x = 0; x < 8; x += 1) {
                  const value = spatial[y * 8 + x];
                  for (let dy = 0; dy < scaleY; dy += 1) {
                    for (let dx = 0; dx < scaleX; dx += 1) {
                      const px = originX + x * scaleX + dx;
                      const py = originY + y * scaleY + dy;
                      if (py < plane.length && px < plane[0].length) plane[py][px] = value;
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  } catch (error) {
    return null;
  }
  const yId = components[0][0];
  const cbId = components[1][0];
  const crId = components[2][0];
  const rows = [];
  for (let y = 0; y < height; y += 1) {
    const row = [];
    for (let x = 0; x < width; x += 1) {
      const yy = planes[yId][y][x];
      const cb = planes[cbId][y][x] - 128;
      const cr = planes[crId][y][x] - 128;
      row.push([
        clamp(yy + 1.402 * cr),
        clamp(yy - 0.344136 * cb - 0.714136 * cr),
        clamp(yy + 1.772 * cb),
        255,
      ]);
    }
    rows.push(row);
  }
  return [width, height, rows];
}

function scanPlan(components, tables) {
  return components.map((item) => {
    const mapped = tables.map[item[0]];
    return [item[0], item[1], item[2], item[3], item[4], mapped[0], mapped[1]];
  });
}

function clamp(value) {
  return Math.max(0, Math.min(255, pyRound(value)));
}

function readBlock(reader, dcTable, acTable, predictors, compId) {
  const block = Array(64).fill(0);
  const category = huff(reader, dcTable);
  predictors[compId] += magnitude(reader, category);
  block[0] = predictors[compId];
  let index = 1;
  while (index < 64) {
    const symbol = huff(reader, acTable);
    if (symbol === 0) break;
    const run = symbol >> 4;
    const size = symbol & 15;
    index += run;
    if (index >= 64) break;
    block[ZZ[index]] = magnitude(reader, size);
    index += 1;
  }
  return block;
}

function magnitude(reader, category) {
  if (category === 0) return 0;
  const bits = reader.read(category);
  if (bits < (1 << (category - 1))) return bits - (1 << category) + 1;
  return bits;
}

function huff(reader, table) {
  let code = 0;
  for (let length = 1; length < 17; length += 1) {
    code = (code << 1) | reader.read(1);
    const symbol = table.get(key(length, code));
    if (symbol !== undefined) return symbol;
  }
  const error = new Error("huffman");
  error.code = "huffman";
  throw error;
}

function idct(block) {
  const out = Array(64).fill(0);
  for (let y = 0; y < 8; y += 1) {
    for (let x = 0; x < 8; x += 1) {
      let total = 0;
      for (let v = 0; v < 8; v += 1) {
        const cv = v === 0 ? 0.70710678118 : 1;
        for (let u = 0; u < 8; u += 1) {
          const cu = u === 0 ? 0.70710678118 : 1;
          total += cu * cv * block[v * 8 + u] * COS[u][x] * COS[v][y];
        }
      }
      out[y * 8 + x] = total / 4 + 128;
    }
  }
  return out;
}

class Bits {
  constructor(data) {
    this.data = data;
    this.pos = 0;
    this.left = 0;
    this.cur = 0;
  }

  read(count) {
    let value = 0;
    for (let i = 0; i < count; i += 1) {
      if (this.left === 0) {
        if (this.pos >= this.data.length) throw new Error("eof");
        this.cur = this.data[this.pos];
        this.pos += 1;
        if (this.cur === 0xff) {
          const marker = this.data[this.pos];
          this.pos += 1;
          if (marker !== 0x00) throw new Error("marker in scan");
        }
        this.left = 8;
      }
      this.left -= 1;
      value = (value << 1) | ((this.cur >> this.left) & 1);
    }
    return value;
  }
}

function key(a, b) {
  return a + ":" + b;
}

function jpegMarkers(data) {
  const tables = { q: {}, h: new Map(), map: {} };
  let frame = null;
  const scan = [];
  let offset = 2;
  while (offset < data.length - 1) {
    if (data[offset] !== 0xff) {
      offset += 1;
      continue;
    }
    while (offset < data.length && data[offset] === 0xff) offset += 1;
    if (offset >= data.length) break;
    const marker = data[offset];
    offset += 1;
    if (marker === 0xd9) break;
    if (marker === 0xda) {
      const length = (data[offset] << 8) | data[offset + 1];
      const header = data.subarray(offset + 2, offset + length);
      const count = header[0];
      let cursor = 1;
      for (let i = 0; i < count; i += 1) {
        const compId = header[cursor];
        const table = header[cursor + 1];
        tables.map[compId] = [table >> 4, table & 15];
        cursor += 2;
      }
      offset += length;
      while (offset < data.length - 1) {
        if (data[offset] === 0xff && data[offset + 1] !== 0x00 && !(data[offset + 1] >= 0xd0 && data[offset + 1] <= 0xd7)) break;
        scan.push(data[offset]);
        offset += 1;
      }
      continue;
    }
    if (marker === 0xd8 || marker === 0x01 || (marker >= 0xd0 && marker <= 0xd7)) continue;
    const length = (data[offset] << 8) | data[offset + 1];
    const chunk = data.subarray(offset + 2, offset + length);
    offset += length;
    if (marker === 0xdb) {
      let cursor = 0;
      while (cursor < chunk.length) {
        const info = chunk[cursor];
        cursor += 1;
        const size = info >> 4 ? 128 : 64;
        if (size !== 64) return { tables, frame: null, scan: Buffer.alloc(0) };
        tables.q[info & 15] = Array.from(chunk.subarray(cursor, cursor + 64));
        cursor += 64;
      }
    } else if (marker === 0xc4) {
      let cursor = 0;
      while (cursor < chunk.length) {
        const info = chunk[cursor];
        cursor += 1;
        const counts = Array.from(chunk.subarray(cursor, cursor + 16));
        cursor += 16;
        const total = counts.reduce((sum, count) => sum + count, 0);
        const symbols = Array.from(chunk.subarray(cursor, cursor + total));
        cursor += total;
        tables.h.set(key(info >> 4, info & 15), huffman(counts, symbols));
      }
    } else if (marker === 0xc0) {
      const height = (chunk[1] << 8) | chunk[2];
      const width = (chunk[3] << 8) | chunk[4];
      const components = [];
      let cursor = 6;
      for (let i = 0; i < chunk[5]; i += 1) {
        const samp = chunk[cursor + 1];
        components.push([chunk[cursor], chunk[0], samp >> 4, samp & 15, chunk[cursor + 2]]);
        cursor += 3;
      }
      frame = [width, height, components];
    }
  }
  return { tables, frame, scan: Buffer.from(scan) };
}

function huffman(counts, symbols) {
  const table = new Map();
  let code = 0;
  let index = 0;
  counts.forEach((count, lengthIndex) => {
    const length = lengthIndex + 1;
    for (let i = 0; i < count; i += 1) {
      table.set(key(length, code), symbols[index]);
      index += 1;
      code += 1;
    }
    code <<= 1;
  });
  return table;
}

function png(data) {
  if (!(data[0] === 0x89 && data.toString("ascii", 1, 4) === "PNG")) return null;
  let offset = 8;
  let width = 0;
  let height = 0;
  let depth = 0;
  let color = 0;
  let interlace = 0;
  let palette = null;
  let transparent = null;
  const parts = [];
  while (offset + 8 <= data.length) {
    const length = data.readUInt32BE(offset);
    const kind = data.toString("ascii", offset + 4, offset + 8);
    const chunk = data.subarray(offset + 8, offset + 8 + length);
    offset += 12 + length;
    if (kind === "IHDR") {
      width = chunk.readUInt32BE(0);
      height = chunk.readUInt32BE(4);
      depth = chunk[8];
      color = chunk[9];
      interlace = chunk[12];
    } else if (kind === "PLTE") {
      palette = [];
      for (let index = 0; index < chunk.length; index += 3) palette.push([chunk[index], chunk[index + 1], chunk[index + 2]]);
    } else if (kind === "tRNS" && palette) {
      transparent = Array.from(chunk);
    } else if (kind === "IDAT") {
      parts.push(chunk);
    } else if (kind === "IEND") {
      break;
    }
  }
  if (!width || depth !== 8 || interlace || ![0, 2, 3, 6].includes(color)) return null;
  const channels = { 0: 1, 2: 3, 3: 1, 6: 4 }[color];
  const raw = zlib.inflateSync(Buffer.concat(parts));
  const stride = width * channels;
  const rows = [];
  let cursor = 0;
  let previous = Buffer.alloc(stride);
  for (let y = 0; y < height; y += 1) {
    const filterKind = raw[cursor];
    cursor += 1;
    const scan = Buffer.from(raw.subarray(cursor, cursor + stride));
    cursor += stride;
    unfilter(filterKind, scan, previous, channels);
    previous = scan;
    const row = [];
    for (let x = 0; x < width; x += 1) {
      const pixel = scan.subarray(x * channels, (x + 1) * channels);
      if (color === 0) row.push([pixel[0], pixel[0], pixel[0], 255]);
      else if (color === 2) row.push([pixel[0], pixel[1], pixel[2], 255]);
      else if (color === 6) row.push([pixel[0], pixel[1], pixel[2], pixel[3]]);
      else {
        const entry = palette[pixel[0]];
        const alpha = transparent == null || pixel[0] >= transparent.length ? 255 : transparent[pixel[0]];
        row.push([entry[0], entry[1], entry[2], alpha]);
      }
    }
    rows.push(row);
  }
  return [width, height, rows];
}

function unfilter(kind, scan, previous, channels) {
  if (kind === 0) return;
  for (let index = 0; index < scan.length; index += 1) {
    const left = index >= channels ? scan[index - channels] : 0;
    const up = previous[index];
    const upperLeft = index >= channels ? previous[index - channels] : 0;
    const value = scan[index];
    if (kind === 1) scan[index] = (value + left) & 255;
    else if (kind === 2) scan[index] = (value + up) & 255;
    else if (kind === 3) scan[index] = (value + Math.floor((left + up) / 2)) & 255;
    else if (kind === 4) scan[index] = (value + paeth(left, up, upperLeft)) & 255;
  }
}

function paeth(left, up, upperLeft) {
  const estimate = left + up - upperLeft;
  const distances = [Math.abs(estimate - left), Math.abs(estimate - up), Math.abs(estimate - upperLeft)];
  if (distances[0] <= distances[1] && distances[0] <= distances[2]) return left;
  if (distances[1] <= distances[2]) return up;
  return upperLeft;
}

module.exports = { cells };
