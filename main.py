#!/usr/bin/env python3
"""Sum up 24 November 2026 world news in one image.

Standard library only (no Pillow, no network). Writes a deterministic
1024x1024 PNG to /output/entry.png, falling back to output/entry.png.
Text is drawn with an embedded 5x7 bitmap font, scaled up.
"""
import binascii
import os
import struct
import zlib

W, H = 1024, 1024
BG = (255, 255, 255)
CARD = (242, 244, 247)
ACCENT = (0, 90, 180)
TEXT = (17, 24, 39)
MUTED = (75, 85, 99)
GOLD = (251, 191, 36)

# 5x7 bitmap font, '#' = pixel on
FONT = {
    'A': ["01110","10001","10001","11111","10001","10001","10001"],
    'B': ["11110","10001","10001","11110","10001","10001","11110"],
    'C': ["01110","10001","10000","10000","10000","10001","01110"],
    'D': ["11110","10001","10001","10001","10001","10001","11110"],
    'E': ["11111","10000","10000","11110","10000","10000","11111"],
    'F': ["11111","10000","10000","11110","10000","10000","10000"],
    'G': ["01110","10001","10000","10111","10001","10001","01111"],
    'H': ["10001","10001","10001","11111","10001","10001","10001"],
    'I': ["01110","00100","00100","00100","00100","00100","01110"],
    'J': ["00111","00010","00010","00010","00010","10010","01100"],
    'K': ["10001","10010","10100","11000","10100","10010","10001"],
    'L': ["10000","10000","10000","10000","10000","10000","11111"],
    'M': ["10001","11011","10101","10101","10001","10001","10001"],
    'N': ["10001","11001","10101","10011","10001","10001","10001"],
    'O': ["01110","10001","10001","10001","10001","10001","01110"],
    'P': ["11110","10001","10001","11110","10000","10000","10000"],
    'Q': ["01110","10001","10001","10001","10101","10010","01101"],
    'R': ["11110","10001","10001","11110","10100","10010","10001"],
    'S': ["01111","10000","10000","01110","00001","00001","11110"],
    'T': ["11111","00100","00100","00100","00100","00100","00100"],
    'U': ["10001","10001","10001","10001","10001","10001","01110"],
    'V': ["10001","10001","10001","10001","10001","01010","00100"],
    'W': ["10001","10001","10001","10101","10101","11011","10001"],
    'X': ["10001","10001","01010","00100","01010","10001","10001"],
    'Y': ["10001","10001","01010","00100","00100","00100","00100"],
    'Z': ["11111","00001","00010","00100","01000","10000","11111"],
    '0': ["01110","10001","10011","10101","11001","10001","01110"],
    '1': ["00100","01100","00100","00100","00100","00100","01110"],
    '2': ["01110","10001","00001","00110","01000","10000","11111"],
    '3': ["11111","00010","00100","00010","00001","10001","01110"],
    '4': ["00010","00110","01010","10010","11111","00010","00010"],
    '5': ["11111","10000","11110","00001","00001","10001","01110"],
    '6': ["00110","01000","10000","11110","10001","10001","01110"],
    '7': ["11111","00001","00010","00100","01000","01000","01000"],
    '8': ["01110","10001","10001","01110","10001","10001","01110"],
    '9': ["01110","10001","10001","01111","00001","00010","01100"],
    ' ': ["00000","00000","00000","00000","00000","00000","00000"],
    '.': ["00000","00000","00000","00000","00000","01100","01100"],
    ',': ["00000","00000","00000","00000","01100","00100","01000"],
    '-': ["00000","00000","00000","01110","00000","00000","00000"],
    ':': ["00000","01100","01100","00000","01100","01100","00000"],
    '%': ["11001","11010","00010","00100","01000","01011","10011"],
    '/': ["00001","00010","00010","00100","01000","01000","10000"],
    "'": ["00100","00100","01000","00000","00000","00000","00000"],
    '(': ["00010","00100","01000","01000","01000","00100","00010"],
    ')': ["01000","00100","00010","00010","00010","00100","01000"],
    '*': ["00000","10101","01110","11111","01110","10101","00000"],
}

HEADLINES = [
    ("1  NVIDIA", "HUANG BACK AS CEO",
     "NVIDIA REINSTATED JENSEN HUANG AS CEO. SHARES ROSE 31% IN A DAY."),
    ("2  UKRAINE", "WARSHIP SUNK OFF LIBYA",
     "UKRAINE SANK THE RUSSIAN CORVETTE MERKURY OFF LIBYA WITH DRONES."),
    ("3  HORMUZ", "THREE TANKERS HIT MINES",
     "IRAN SAID THREE TANKERS HIT MINES IN THE STRAIT OF HORMUZ."),
    ("4  GAZA", "STRIKES KILL SECURITY CHIEF",
     "ISRAELI STRIKES KILLED A HAMAS SECURITY CHIEF AND SIX OTHERS."),
    ("5  ZAPORIZHZHIA", "ATTACK KILLS TWO",
     "A RUSSIAN ATTACK KILLED TWO IN ZAPORIZHZHIA AND WOUNDED 40."),
    ("6  INDONESIA", "FACTORY FIRE KILLS 26",
     "A FACTORY FIRE IN BANTEN, INDONESIA KILLED 26 PEOPLE."),
]

def chunk(typ, data):
    c = struct.pack(">I", len(data)) + typ + data
    return c + struct.pack(">I", binascii.crc32(typ + data) & 0xffffffff)

def save_png(path, buf):
    raw = b"".join(b"\x00" + bytes(buf[y*W*3:(y+1)*W*3]) for y in range(H))
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)

class Canvas:
    def __init__(self):
        self.buf = bytearray(BG * W * H)
    def rect(self, x, y, w, h, color):
        for yy in range(max(0, y), min(H, y + h)):
            base = (yy * W + max(0, x)) * 3
            for xx in range(max(0, x), min(W, x + w)):
                i = (yy * W + xx) * 3
                self.buf[i:i+3] = bytes(color)
    def text(self, x, y, s, scale, color):
        cx = x
        for ch in s.upper():
            glyph = FONT.get(ch, FONT[' '])
            for gy, row in enumerate(glyph):
                for gx, bit in enumerate(row):
                    if bit == '1':
                        self.rect(cx + gx*scale, y + gy*scale, scale, scale, color)
            cx += 6 * scale
        return cx
    def text_w(self, s, scale):
        return len(s) * 6 * scale
    def wrap(self, s, scale, max_w):
        words = s.split()
        lines, cur = [], ""
        for w in words:
            t = (cur + " " + w).strip()
            if self.text_w(t, scale) <= max_w:
                cur = t
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines

def main():
    c = Canvas()
    c.rect(0, 0, W, 110, (17, 24, 39))
    c.rect(0, 110, W, 4, ACCENT)
    c.text(40, 20, "WORLD NEWS", 7, (255, 255, 255))
    c.text(40, 78, "24 NOVEMBER 2026", 3, ACCENT)
    c.rect(830, 24, 154, 56, GOLD)
    c.text(848, 38, "24 NOV", 3, (0, 0, 0))
    y = 124
    for kicker, title, body in HEADLINES:
        c.rect(32, y, 960, 132, CARD)
        c.rect(32, y, 8, 132, ACCENT)
        c.text(62, y + 12, kicker, 2, ACCENT)
        c.text(62, y + 36, title, 4, TEXT)
        lines = c.wrap(body, 3, 880)
        ly = y + 82
        for line in lines[:2]:
            c.text(62, ly, line, 3, MUTED)
            ly += 26
        y += 142
    c.text(40, 988, "SOURCES: ONE TURN, JUST SECURITY, REUTERS * 24 NOV 2026", 2, MUTED)
    written = []
    here = os.path.dirname(os.path.abspath(__file__))
    for p in ("/output/entry.png", os.path.join(here, "output", "entry.png")):
        try:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            n = save_png(p, c.buf)
            written.append(p)
            print(f"wrote {p} {n} bytes")
        except Exception as e:
            print(f"skip {p}: {e}")
    if not written:
        raise SystemExit("could not write any output")

if __name__ == "__main__":
    main()
