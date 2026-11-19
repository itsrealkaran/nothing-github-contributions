"""Turn a profile photo into a Nothing glyph.

The room around the person is dropped. What remains is a field of equal
dots: the figure colour for the lit parts, the muted colour for the outer
contour, and gaps where the photo is dark. The photo itself is never drawn.
"""

import struct
import zlib

GRID = 18


def cells(blob):
    image = _image(blob)
    if not image:
        return []
    width, height, rows = image
    mask = _subject(width, height, rows)
    box = _focus(width, height, rows, mask)
    if not box:
        return []
    left, top, right, bottom = box
    sampled = _resample(rows, mask, left, top, right, bottom, GRID)
    kept = _resample_mask(mask, width, height, left, top, right, bottom, GRID)
    dots = []
    for y in range(GRID):
        for x in range(GRID):
            if not kept[y][x]:
                continue
            kind = 1 if _edge(kept, x, y) else _tone(sampled[y][x])
            if kind:
                dots.append((x, y, kind))
    return _joined(dots)


def _joined(dots):
    occupied = {(x, y) for x, y, _kind in dots}
    kept = []
    for x, y, kind in dots:
        if any((x + dx, y + dy) in occupied for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1))):
            kept.append((x, y, kind))
    return kept


def _tone(pixel):
    red, green, blue = pixel
    luma = 0.2126 * red + 0.7152 * green + 0.0722 * blue
    if luma >= 168:
        return 3
    if luma >= 96:
        return 2
    return 0


def _edge(mask, x, y):
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nx, ny = x + dx, y + dy
        if nx < 0 or ny < 0 or nx >= GRID or ny >= GRID or not mask[ny][nx]:
            return True
    return False


def _luma(red, green, blue):
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def _subject(width, height, rows):
    """Drop the empty room. A picture that is already dots on black keeps the dots."""
    dark = 0
    for y in range(0, height, 2):
        for x in range(0, width, 2):
            red, green, blue, alpha = rows[y][x]
            if alpha < 16 or _luma(red, green, blue) < 28:
                dark += 1
    samples = ((height + 1) // 2) * ((width + 1) // 2)
    if dark / samples > 0.62:
        background = [[False] * width for _ in range(height)]
        for y in range(height):
            for x in range(width):
                red, green, blue, alpha = rows[y][x]
                background[y][x] = alpha < 16 or _luma(red, green, blue) < 28
        return background
    background = [[False] * width for _ in range(height)]
    for y in range(height):
        row = rows[y]
        for x in range(width):
            red, green, blue, alpha = row[x]
            background[y][x] = _room(red, green, blue, alpha)
    return background


def _skin(red, green, blue):
    return (
        red > 120 and green > 55 and blue < 175
        and red > green + 12 and (red - blue) > 28
        and green > blue
    )


def _room(red, green, blue, alpha):
    if alpha < 16:
        return True
    if _skin(red, green, blue):
        return False
    chroma = max(red, green, blue) - min(red, green, blue)
    luma = _luma(red, green, blue)
    # Grey backdrop, a flat wall, and a white shirt. Hair and the face stay.
    if luma > 42 and chroma < 26:
        return True
    return luma > 165 and chroma < 42


def _focus(width, height, rows, background):
    xs = []
    ys = []
    for y in range(0, height, 2):
        for x in range(0, width, 2):
            if background[y][x]:
                continue
            red, green, blue, _alpha = rows[y][x]
            if _skin(red, green, blue):
                xs.append(x)
                ys.append(y)
    if len(xs) < 30:
        return _bounds(background, width, height)
    left, right = min(xs), max(xs)
    top, bottom = min(ys), max(ys)
    face_w = max(1, right - left)
    face_h = max(1, bottom - top)
    return (
        max(0, left - face_w // 4),
        max(0, top - int(face_h * 0.7)),
        min(width, right + face_w // 4),
        min(height, bottom + face_h // 3),
    )


def _bounds(background, width, height):
    left, top, right, bottom = width, height, 0, 0
    found = False
    for y in range(height):
        for x in range(width):
            if background[y][x]:
                continue
            found = True
            left = min(left, x)
            top = min(top, y)
            right = max(right, x)
            bottom = max(bottom, y)
    if not found:
        return None
    return left, top, right + 1, bottom + 1


def _resample(rows, background, left, top, right, bottom, grid):
    span_x = right - left
    span_y = bottom - top
    sampled = []
    for y in range(grid):
        row = []
        y0 = top + int(y * span_y / grid)
        y1 = max(y0 + 1, top + int((y + 1) * span_y / grid))
        for x in range(grid):
            x0 = left + int(x * span_x / grid)
            x1 = max(x0 + 1, left + int((x + 1) * span_x / grid))
            total = [0, 0, 0]
            count = 0
            for py in range(y0, min(y1, bottom)):
                line = rows[py]
                mask = background[py]
                for px in range(x0, min(x1, right)):
                    if mask[px]:
                        continue
                    pixel = line[px]
                    total[0] += pixel[0]
                    total[1] += pixel[1]
                    total[2] += pixel[2]
                    count += 1
            if count:
                row.append(tuple(channel // count for channel in total))
            else:
                row.append((0, 0, 0))
        sampled.append(row)
    return sampled


def _resample_mask(background, width, height, left, top, right, bottom, grid):
    span_x = right - left
    span_y = bottom - top
    kept = []
    for y in range(grid):
        row = []
        y0 = top + int(y * span_y / grid)
        y1 = max(y0 + 1, top + int((y + 1) * span_y / grid))
        for x in range(grid):
            x0 = left + int(x * span_x / grid)
            x1 = max(x0 + 1, left + int((x + 1) * span_x / grid))
            subject = 0
            total = 0
            for py in range(y0, min(y1, height)):
                for px in range(x0, min(x1, width)):
                    total += 1
                    if not background[py][px]:
                        subject += 1
            row.append(total and subject / total >= 0.04)
        kept.append(row)
    return kept


def _image(data):
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return _png(data)
    if data.startswith(b"\xff\xd8"):
        return _jpeg(data)
    return None


def _jpeg(data):
    tables, frame, scans = _jpeg_markers(data)
    if not frame or not scans:
        return None
    width, height, components = frame
    if any(item[1] != 8 for item in components):
        return None
    max_h = max(item[2] for item in components)
    max_v = max(item[3] for item in components)
    mcu_w = 8 * max_h
    mcu_h = 8 * max_v
    across = (width + mcu_w - 1) // mcu_w
    down = (height + mcu_h - 1) // mcu_h
    planes = {item[0]: [[0] * (across * mcu_w) for _ in range(down * mcu_h)] for item in components}
    predictors = {item[0]: 0 for item in components}
    reader = _Bits(scans)
    order = {item[0]: item for item in components}
    try:
        for my in range(down):
            for mx in range(across):
                for comp_id, _depth, samp_h, samp_v, qt, dc, ac in _scan_plan(components, tables):
                    quant = tables["q"][qt]
                    for vy in range(samp_v):
                        for vx in range(samp_h):
                            block = _block(reader, tables["h"][(0, dc)], tables["h"][(1, ac)], predictors, comp_id)
                            for index, value in enumerate(block):
                                block[index] = value * quant[index]
                            spatial = _idct(block)
                            scale_x = max_h // samp_h
                            scale_y = max_v // samp_v
                            origin_x = mx * mcu_w + vx * 8 * scale_x
                            origin_y = my * mcu_h + vy * 8 * scale_y
                            plane = planes[comp_id]
                            for y in range(8):
                                for x in range(8):
                                    value = spatial[y * 8 + x]
                                    for dy in range(scale_y):
                                        for dx in range(scale_x):
                                            px = origin_x + x * scale_x + dx
                                            py = origin_y + y * scale_y + dy
                                            if py < len(plane) and px < len(plane[0]):
                                                plane[py][px] = value
    except (IndexError, KeyError):
        return None
    y_id, cb_id, cr_id = (components[index][0] for index in range(3))
    rows = []
    for y in range(height):
        row = []
        for x in range(width):
            yy = planes[y_id][y][x]
            cb = planes[cb_id][y][x] - 128
            cr = planes[cr_id][y][x] - 128
            red = _clamp(yy + 1.402 * cr)
            green = _clamp(yy - 0.344136 * cb - 0.714136 * cr)
            blue = _clamp(yy + 1.772 * cb)
            row.append((red, green, blue, 255))
        rows.append(row)
    return width, height, rows


def _scan_plan(components, tables):
    plan = []
    for comp_id, depth, samp_h, samp_v, qt in components:
        dc, ac = tables["map"][comp_id]
        plan.append((comp_id, depth, samp_h, samp_v, qt, dc, ac))
    return plan


def _clamp(value):
    return max(0, min(255, int(round(value))))


_ZZ = (
    0, 1, 8, 16, 9, 2, 3, 10, 17, 24, 32, 25, 18, 11, 4, 5, 12, 19, 26, 33,
    40, 48, 41, 34, 27, 20, 13, 6, 7, 14, 21, 28, 35, 42, 49, 56, 57, 50, 43, 36,
    29, 22, 15, 23, 30, 37, 44, 51, 58, 59, 52, 45, 38, 31, 39, 46, 53, 60, 61, 54,
    47, 55, 62, 63,
)


def _block(reader, dc_table, ac_table, predictors, comp_id):
    block = [0] * 64
    category = _huff(reader, dc_table)
    diff = _magnitude(reader, category)
    predictors[comp_id] += diff
    block[0] = predictors[comp_id]
    index = 1
    while index < 64:
        symbol = _huff(reader, ac_table)
        if symbol == 0:
            break
        run, category = symbol >> 4, symbol & 15
        index += run
        if index >= 64:
            break
        block[_ZZ[index]] = _magnitude(reader, category)
        index += 1
    return block


def _magnitude(reader, category):
    if category == 0:
        return 0
    bits = reader.read(category)
    if bits < (1 << (category - 1)):
        return bits - (1 << category) + 1
    return bits


def _huff(reader, table):
    code = 0
    for length in range(1, 17):
        code = (code << 1) | reader.read(1)
        symbol = table.get((length, code))
        if symbol is not None:
            return symbol
    raise KeyError("huffman")


def _idct(block):
    out = [0.0] * 64
    for y in range(8):
        for x in range(8):
            total = 0.0
            for v in range(8):
                cv = 0.70710678118 if v == 0 else 1.0
                for u in range(8):
                    cu = 0.70710678118 if u == 0 else 1.0
                    total += (
                        cu * cv * block[v * 8 + u]
                        * _COS[u][x]
                        * _COS[v][y]
                    )
            out[y * 8 + x] = total / 4 + 128
    return out


_COS = tuple(
    tuple(__import__("math").cos((2 * x + 1) * u * __import__("math").pi / 16) for x in range(8))
    for u in range(8)
)


class _Bits:
    def __init__(self, data):
        self.data = data
        self.pos = 0
        self.left = 0
        self.cur = 0

    def read(self, count):
        value = 0
        for _ in range(count):
            if self.left == 0:
                self.cur = self.data[self.pos]
                self.pos += 1
                if self.cur == 0xFF:
                    marker = self.data[self.pos]
                    self.pos += 1
                    if marker != 0x00:
                        raise IndexError("marker in scan")
                self.left = 8
            self.left -= 1
            value = (value << 1) | ((self.cur >> self.left) & 1)
        return value


def _jpeg_markers(data):
    tables = {"q": {}, "h": {}, "map": {}}
    frame = None
    scan = bytearray()
    offset = 2
    while offset < len(data) - 1:
        if data[offset] != 0xFF:
            offset += 1
            continue
        while offset < len(data) and data[offset] == 0xFF:
            offset += 1
        if offset >= len(data):
            break
        marker = data[offset]
        offset += 1
        if marker == 0xD9:
            break
        if marker == 0xDA:
            length = int.from_bytes(data[offset:offset + 2], "big")
            header = data[offset + 2:offset + length]
            count = header[0]
            cursor = 1
            for _ in range(count):
                comp_id = header[cursor]
                table = header[cursor + 1]
                tables["map"][comp_id] = (table >> 4, table & 15)
                cursor += 2
            offset += length
            while offset < len(data) - 1:
                if data[offset] == 0xFF and data[offset + 1] != 0x00 and not (0xD0 <= data[offset + 1] <= 0xD7):
                    break
                scan.append(data[offset])
                offset += 1
            continue
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            continue
        length = int.from_bytes(data[offset:offset + 2], "big")
        chunk = data[offset + 2:offset + length]
        offset += length
        if marker == 0xDB:
            cursor = 0
            while cursor < len(chunk):
                info = chunk[cursor]
                cursor += 1
                size = 128 if info >> 4 else 64
                if size != 64:
                    return tables, None, None
                tables["q"][info & 15] = list(chunk[cursor:cursor + 64])
                cursor += 64
        elif marker == 0xC4:
            cursor = 0
            while cursor < len(chunk):
                info = chunk[cursor]
                cursor += 1
                counts = list(chunk[cursor:cursor + 16])
                cursor += 16
                symbols = list(chunk[cursor:cursor + sum(counts)])
                cursor += sum(counts)
                tables["h"][(info >> 4, info & 15)] = _huffman(counts, symbols)
        elif marker == 0xC0:
            height = int.from_bytes(chunk[1:3], "big")
            width = int.from_bytes(chunk[3:5], "big")
            components = []
            cursor = 6
            for _ in range(chunk[5]):
                samp = chunk[cursor + 1]
                components.append((chunk[cursor], chunk[0], samp >> 4, samp & 15, chunk[cursor + 2]))
                cursor += 3
            frame = (width, height, components)
    return tables, frame, bytes(scan)


def _huffman(counts, symbols):
    table = {}
    code = 0
    index = 0
    for length, count in enumerate(counts, start=1):
        for _ in range(count):
            table[(length, code)] = symbols[index]
            index += 1
            code += 1
        code <<= 1
    return table


def _png(data):
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return None
    offset = 8
    width = height = None
    depth = color = interlace = None
    palette = None
    transparent = None
    parts = []
    while offset + 8 <= len(data):
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        kind = data[offset + 4:offset + 8]
        chunk = data[offset + 8:offset + 8 + length]
        offset += 12 + length
        if kind == b"IHDR":
            width, height, depth, color, _comp, _filter, interlace = struct.unpack(">IIBBBBB", chunk)
        elif kind == b"PLTE":
            palette = [tuple(chunk[index:index + 3]) for index in range(0, len(chunk), 3)]
        elif kind == b"tRNS" and palette is not None:
            transparent = list(chunk)
        elif kind == b"IDAT":
            parts.append(chunk)
        elif kind == b"IEND":
            break
    if not width or depth != 8 or interlace or color not in (0, 2, 3, 6):
        return None
    channels = {0: 1, 2: 3, 3: 1, 6: 4}[color]
    raw = zlib.decompress(b"".join(parts))
    stride = width * channels
    rows = []
    cursor = 0
    previous = bytearray(stride)
    for _y in range(height):
        filter_kind = raw[cursor]
        cursor += 1
        scan = bytearray(raw[cursor:cursor + stride])
        cursor += stride
        _unfilter(filter_kind, scan, previous, channels)
        previous = scan
        row = []
        for x in range(width):
            pixel = scan[x * channels:(x + 1) * channels]
            if color == 0:
                row.append((pixel[0], pixel[0], pixel[0], 255))
            elif color == 2:
                row.append((pixel[0], pixel[1], pixel[2], 255))
            elif color == 6:
                row.append((pixel[0], pixel[1], pixel[2], pixel[3]))
            else:
                entry = palette[pixel[0]]
                alpha = 255 if transparent is None or pixel[0] >= len(transparent) else transparent[pixel[0]]
                row.append((entry[0], entry[1], entry[2], alpha))
        rows.append(row)
    return width, height, rows


def _unfilter(kind, scan, previous, channels):
    if kind == 0:
        return
    for index, value in enumerate(scan):
        left = scan[index - channels] if index >= channels else 0
        up = previous[index]
        upper_left = previous[index - channels] if index >= channels else 0
        if kind == 1:
            scan[index] = (value + left) & 255
        elif kind == 2:
            scan[index] = (value + up) & 255
        elif kind == 3:
            scan[index] = (value + ((left + up) // 2)) & 255
        elif kind == 4:
            scan[index] = (value + _paeth(left, up, upper_left)) & 255


def _paeth(left, up, upper_left):
    estimate = left + up - upper_left
    distances = (abs(estimate - left), abs(estimate - up), abs(estimate - upper_left))
    if distances[0] <= distances[1] and distances[0] <= distances[2]:
        return left
    if distances[1] <= distances[2]:
        return up
    return upper_left
