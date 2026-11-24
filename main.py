"""Sum up 24 November 2026 world news in one image.

Writes a deterministic 1024x1024 PNG to /output/entry.png using only the
Python standard library: a hand-built 5x7 bitmap font, a card layout and a
minimal PNG encoder on top of zlib.
"""

import os
import struct
import zlib

W = H = 1024
BG = (255, 255, 255)
INK = (17, 22, 33)
HEADER = (14, 22, 40)
HEADER_TEXT = (255, 255, 255)
RULE = (205, 211, 222)
BODY = (70, 80, 97)
TAG = (176, 26, 36)
TAG_TEXT = (255, 255, 255)
HEADER_H = 162

GLYPHS = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "01100", "01000"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "'": ("01100", "01100", "01000", "00000", "00000", "00000", "00000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
}

GLYPH_W = 5
GLYPH_H = 7
SPACING = 1


class Canvas:
    def __init__(self, width, height, color):
        self.width = width
        self.height = height
        self.pixels = bytearray(bytes(color) * (width * height))

    def rect(self, x, y, w, h, color):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.width, x + w), min(self.height, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            start = (yy * self.width + x0) * 3
            self.pixels[start:start + len(row)] = row

    def text(self, x, y, s, color, scale, bold=False, tracking=0):
        cx = x
        for ch in s.upper():
            glyph = GLYPHS.get(ch, GLYPHS[" "])
            for gy, row in enumerate(glyph):
                for gx, bit in enumerate(row):
                    if bit == "1":
                        self.rect(cx + gx * scale, y + gy * scale, scale, scale, color)
                        if bold:
                            self.rect(cx + gx * scale + 1, y + gy * scale, scale, scale, color)
            cx += (GLYPH_W + SPACING) * scale + tracking
        return cx


def text_width(s, scale, tracking=0):
    return len(s) * ((GLYPH_W + SPACING) * scale + tracking)


def wrap(s, scale, max_width, tracking=0):
    lines = []
    line = ""
    for word in s.split():
        candidate = word if not line else line + " " + word
        if text_width(candidate, scale, tracking) <= max_width:
            line = candidate
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def write_png(path, canvas):
    raw = bytearray()
    stride = canvas.width * 3
    for y in range(canvas.height):
        raw.append(0)
        raw += canvas.pixels[y * stride:(y + 1) * stride]

    def chunk(tag, data):
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    header = struct.pack(">IIBBBBB", canvas.width, canvas.height, 8, 2, 0, 0, 0)
    out = b"\x89PNG\r\n\x1a\n"
    out += chunk(b"IHDR", header)
    out += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    out += chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(out)


STORIES = (
    ("NVIDIA", "HUANG BACK AS CEO",
     "HUANG REINSTATED. SHARES ROSE 31% IN A DAY."),
    ("UKRAINE", "WARSHIP SUNK OFF LIBYA",
     "DRONES SANK RUSSIAN CORVETTE MERKURY."),
    ("HORMUZ", "THREE TANKERS HIT MINES",
     "REPORTED BY IRAN IN THE STRAIT OF HORMUZ."),
    ("GAZA", "STRIKES KILL SECURITY CHIEF",
     "ISRAELI STRIKES KILLED A HAMAS CHIEF AND 6 MORE."),
    ("ZAPORIZHZHIA", "ATTACK KILLS TWO",
     "A RUSSIAN ATTACK KILLED TWO AND WOUNDED 40."),
    ("INDONESIA", "FACTORY FIRE KILLS 26",
     "A FACTORY FIRE IN BANTEN KILLED 26 PEOPLE."),
)


def draw_card(canvas, x, y, w, h, number, place, title, body):
    canvas.rect(x, y, w, h, RULE)
    canvas.rect(x + 2, y + 2, w - 4, h - 4, BG)
    canvas.rect(x + 2, y + 2, w - 4, 6, HEADER)

    pad = 18
    tag = "%d  %s" % (number, place)
    tag_w = text_width(tag, 3) + 2 * 10
    canvas.rect(x + pad, y + 24, tag_w, 30, TAG)
    canvas.text(x + pad + 10, y + 24 + 6, tag, TAG_TEXT, 3)

    ty = y + 68
    for line in wrap(title, 4, w - 2 * pad):
        canvas.text(x + pad, ty, line, INK, 4, bold=True)
        ty += 36

    ty += 8
    canvas.rect(x + pad, ty, w - 2 * pad, 2, RULE)
    ty += 16

    lines = wrap(body, 3, w - 2 * pad)
    assert len(lines) <= 2, body
    for line in lines:
        canvas.text(x + pad, ty, line, BODY, 3)
        ty += 28


def build():
    canvas = Canvas(W, H, BG)

    canvas.rect(0, 0, W, HEADER_H, HEADER)
    canvas.text(40, 30, "WORLD NEWS", HEADER_TEXT, 9, bold=True)
    canvas.rect(40, 106, 944, 3, (120, 134, 160))
    canvas.text(40, 122, "24 NOVEMBER 2026", HEADER_TEXT, 4, bold=True)
    stamp = "SIX STORIES"
    canvas.text(984 - text_width(stamp, 3), 126, stamp, (168, 180, 202), 3)

    margin = 30
    gap = 20
    card_w = (W - 2 * margin - gap) // 2
    top = HEADER_H + 24
    card_h = (H - top - margin - 2 * gap) // 3

    for i, (place, title, body) in enumerate(STORIES):
        col, row = i % 2, i // 2
        x = margin + col * (card_w + gap)
        y = top + row * (card_h + gap)
        draw_card(canvas, x, y, card_w, card_h, i + 1, place, title, body)

    return canvas


def output_path():
    target = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    try:
        os.makedirs(target, exist_ok=True)
        probe = os.path.join(target, ".write-test")
        with open(probe, "wb"):
            pass
        os.remove(probe)
    except OSError:
        target = "output"
        os.makedirs(target, exist_ok=True)
    return os.path.join(target, "entry.png")


def main():
    path = output_path()
    write_png(path, build())
    print(path, os.path.getsize(path), "bytes")


if __name__ == "__main__":
    main()
