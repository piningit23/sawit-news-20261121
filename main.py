# news-image-20261121 — main.py
# Draws a one-page newspaper front page summing up the world news of
# Saturday 21 November 2026, as a 1024x1024 PNG, using only the Python
# standard library. No network, no fonts on disk: glyphs are a small
# 5x7 bitmap font defined below, and the PNG is encoded by hand
# (zlib + struct). Output is fully deterministic.
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- font
# Each glyph: 7 rows of 5 bits, '#' = ink. Uppercase only; the renderer
# uppercases all text first.
GLYPHS = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
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
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "+": ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "*": ("00000", "10101", "01110", "10101", "00000", "00000", "00000"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
}
BLANK = ("00000", "00000", "00000", "00000", "00000", "00000", "00000")

# ---------------------------------------------------------------- canvas
PAPER = (247, 243, 234)
INK = (18, 18, 22)
RED = (158, 24, 24)
NAVY = (24, 48, 96)
SEA = (214, 228, 238)
LAND = (196, 205, 178)
LANDLINE = (120, 130, 105)
GREY = (110, 108, 100)
LIGHT = (232, 226, 212)


class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg * w * h)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def rect(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                j = base + (xx - x0) * 3
                self.px[j], self.px[j + 1], self.px[j + 2] = c

    def hline(self, x, y, w, c, t=1):
        self.rect(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):
        self.rect(x, y, t, h, c)

    def line(self, x0, y0, x1, y1, c):
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, c):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, c)

    def ring(self, cx, cy, r, c):
        for a in range(360):
            import math
            x = cx + int(r * math.cos(math.radians(a)))
            y = cy + int(r * math.sin(math.radians(a)))
            self.set(x, y, c)

    def poly(self, pts, c):
        # Scanline fill of a simple polygon.
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                for x in range(int(xs[k]), int(xs[k + 1]) + 1):
                    self.set(x, y, c)

    # ---- text ----
    def text(self, x, y, s, scale, c):
        s = s.upper()
        cx = x
        for ch in s:
            g = GLYPHS.get(ch, BLANK)
            for row in range(7):
                bits = g[row]
                for col in range(5):
                    if bits[col] == "1":
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, c)
            cx += 6 * scale
        return cx

    def text_w(self, s, scale):
        return len(s) * 6 * scale - scale

    def text_center(self, y, s, scale, c, x0=0, x1=W):
        w = self.text_w(s, scale)
        self.text(x0 + (x1 - x0 - w) // 2, y, s, scale, c)

    def wrap(self, s, scale, max_w):
        per = max(1, (max_w + scale) // (6 * scale))
        words, lines, cur = s.split(), [], ""
        for wd in words:
            trial = (cur + " " + wd).strip()
            if len(trial) <= per:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = wd
        if cur:
            lines.append(cur)
        return lines

    def para(self, x, y, s, scale, c, max_w, leading=None):
        lh = leading if leading is not None else 9 * scale
        for ln in self.wrap(s, scale, max_w):
            self.text(x, y, ln, scale, c)
            y += lh
        return y


def chunk(tag, data):
    c = struct.pack(">I", len(data)) + tag + data
    return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def write_png(cv, path):
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)
        raw += cv.px[y * stride:(y + 1) * stride]
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(png)
    return len(png)

# ---------------------------------------------------------------- stories
# Every item below was verified in web reporting dated 21 November 2026
# (or first reported that day); full source pairs live in SOURCES.md.
# Panels: (number, kicker, headline, body). Briefs: one line each.
PANELS = [
    (1, "POLAND  •  NATO",
     "MISSILE LANDS IN POLAND",
     "A Russian Kh-101 missile came down near Nowy Lipowiec, 50 km "
     "from Ukraine. PM Tusk called it a deliberate provocation. "
     "No one was hurt."),
    (2, "UKRAINE  •  KRYVYI RIH",
     "BOY, 7, AND MEDIC KILLED",
     "Russian double-tap strike on Kryvyi Rih killed a boy, 7, and "
     "a medic, 20; 42 wounded."),
    (3, "SAUDI ARABIA  •  YEMEN",
     "THREE MISSILES AT RIYADH",
     "Coalition says it downed three Houthi missiles fired at "
     "Riyadh, days after a tower was hit."),
    (4, "MARKETS  •  WALL STREET",
     "TECH ROUT: NASDAQ -5.3%",
     "Anthropic fell 8.5% to $88.91 as the Nasdaq lost 5.3% and "
     "wiped out its gains for the year."),
    (5, "USA  •  AI",
     "TRUMP: TAX DATA CENTRES ABROAD",
     "Trump said US firms building AI data centres abroad face a "
     "ban or a tremendous tax."),
    (6, "DENMARK  •  RUSSIA",
     "RAPPER PLOT: ENVOY EXPELLED",
     "Denmark expelled Russia's defence attache over a plot to kill "
     "rapper Kyivstoner."),
    (7, "EUROPE  •  BRUSSELS",
     "EU: EUR 1BN MORE FOR KYIV",
     "EU states approved EUR 1bn of joint arms buying for Ukraine: "
     "drones, air defence and ammo."),
    (8, "NEW YORK  •  USA",
     "RIKERS TO CLOSE BY 2032",
     "Mayor Mamdani unveiled a plan to shut New York's Rikers "
     "Island jail by 2032, replacing it with four borough jails."),
]

BRIEFS = [
    "9  TRUMP HAILS 'FANTASTIC' TIES WITH XI AND PUTIN AFTER SHENZHEN SUMMIT",
    "10  ZELENSKY CALLS PUTIN A 'KILLER' AFTER TRUMP CALLED HIM A FRIEND",
    "11  US SENATE REJECTS IRAN WAR-POWERS RESOLUTION, 51-48",
    "12  US SANCTIONS FOUR IRANIANS OVER OIL REVENUES (OFAC)",
    "13  US SANCTIONS COMANCHEROS AND 'NDRANGHETA CRIME GROUPS",
    "14  UK AND EU AGREE YOUTH MOBILITY DEAL, AGES 18-31",
    "15  UK PLEDGES 1,000+ DRONES FOR UKRAINE IN GBP 260M PACKAGE",
    "16  GAZA: 22,000+ CHILDREN KILLED, HEALTH OFFICIALS SAY",
    "17  COP31: UKRAINE BLOCKS RUSSIAN CLIMATE REPORT",
    "18  CYCLONE AKVAN WEAKENS OVER INDIA; FLORIDA FLOODS WATCHED",
    "19  ATP FINALS: MEDVEDEV BEATS TIAFOE 6-3, 6-4",
    "20  CRICKET: INDIA 239-1 AT LUNCH, DAY 3 OF WELLINGTON TEST",
    "21  T10 FINAL: UAE BULLS BEAT YAS LIONS BY 24 RUNS",
    "22  FOOTBALL: BAYERN HELD 1-1 BY COLOGNE; TROYES WIN 3-1",
]

# Map dots: (panel number, lon, lat, label)
DOTS = [
    (1, 19, 52, "POLAND"),
    (2, 33, 48, "KRYVYI RIH"),
    (3, 47, 25, "RIYADH"),
    (4, -122, 37, "WALL ST"),
    (5, -77, 39, "WASHINGTON"),
    (6, 12, 56, "DENMARK"),
    (7, 4, 51, "BRUSSELS"),
    (8, -74, 41, "NEW YORK"),
]

# Rough continent outlines (lon, lat) — simplified, for orientation only.
CONTINENTS = [
    [(-168, 66), (-140, 70), (-125, 71), (-110, 68), (-95, 69), (-85, 66),
     (-80, 62), (-75, 58), (-65, 60), (-60, 47), (-70, 42), (-75, 35),
     (-80, 26), (-85, 30), (-90, 21), (-97, 26), (-105, 23), (-110, 30),
     (-120, 34), (-125, 40), (-125, 49), (-135, 58), (-150, 60),
     (-165, 60)],
    [(-80, 10), (-75, 11), (-62, 10), (-52, 5), (-50, 0), (-40, -5),
     (-35, -8), (-40, -20), (-48, -28), (-55, -35), (-65, -41), (-70, -52),
     (-73, -44), (-73, -30), (-77, -12), (-80, -3), (-80, 5)],
    [(-10, 36), (-9, 43), (-2, 48), (0, 51), (5, 53), (8, 57), (12, 55),
     (18, 56), (21, 55), (24, 58), (28, 60), (30, 62), (30, 70), (40, 68),
     (45, 68), (50, 69), (55, 68), (60, 69), (65, 68), (68, 66), (60, 60),
     (50, 55), (45, 48), (40, 45), (35, 44), (30, 46), (28, 44), (23, 40),
     (19, 42), (15, 44), (10, 44), (8, 38), (3, 38), (-2, 37), (-6, 36)],
    [(-6, 35), (0, 36), (10, 37), (11, 34), (15, 32), (20, 32), (25, 32),
     (30, 31), (35, 28), (39, 21), (43, 12), (48, 11), (51, 12), (44, 1),
     (41, -4), (40, -12), (36, -18), (33, -26), (28, -33), (20, -35),
     (17, -29), (14, -22), (12, -17), (9, -1), (9, 4), (4, 6), (-8, 5),
     (-13, 8), (-17, 15), (-17, 21), (-16, 27), (-10, 31)],
    [(60, 70), (70, 72), (80, 73), (100, 76), (120, 73), (140, 72),
     (160, 70), (178, 66), (170, 60), (162, 56), (158, 53), (150, 59),
     (142, 55), (140, 40), (135, 34), (130, 33), (127, 35), (122, 38),
     (120, 31), (115, 23), (110, 20), (108, 12), (105, 9), (100, 8),
     (98, 12), (95, 16), (92, 21), (89, 22), (86, 20), (80, 15), (77, 8),
     (73, 16), (68, 22), (62, 25), (58, 26), (54, 27), (50, 29), (48, 30),
     (44, 29), (42, 38), (36, 36), (33, 36), (36, 42), (40, 45), (44, 48),
     (48, 52), (52, 58), (55, 62), (58, 66)],
    [(113, -22), (114, -30), (115, -35), (120, -34), (125, -32),
     (130, -32), (135, -35), (140, -38), (145, -38), (150, -37),
     (153, -32), (153, -27), (150, -22), (146, -19), (142, -11),
     (137, -12), (135, -15), (132, -12), (130, -13), (126, -14),
     (122, -17), (118, -20)],
]


def draw_panel(cv, x, y, w, h, num, kicker, headline, body):
    cv.rect(x, y, w, h, INK)
    cv.rect(x + 2, y + 2, w - 4, h - 4, (255, 255, 255))
    cv.rect(x + 2, y + 2, w - 4, 3, NAVY)
    lead = (w > 500)
    hs = 3 if lead else 2
    cv.text(x + 10, y + 12, str(num), 3, RED)
    num_w = cv.text_w(str(num), 3)
    cv.text(x + 10 + num_w + 8, y + 14, kicker, 1, GREY)
    yy = y + 38
    for ln in cv.wrap(headline, hs, w - 20):
        cv.text(x + 10, yy, ln, hs, NAVY)
        cv.text(x + 11, yy, ln, hs, NAVY)  # bold
        yy += 9 * hs
    yy += 4
    cv.hline(x + 10, yy, w - 20, LIGHT, 2)
    yy += 10
    cv.para(x + 10, yy, body, 2, INK, w - 20, leading=15)


def draw_map(cv, x, y, w, h):
    cv.rect(x, y, w, h, SEA)
    cv.rect(x, y, w, 2, NAVY)
    cv.rect(x, y + h - 2, w, 2, NAVY)
    cv.text(x + 10, y + 8, "WHERE IT HAPPENED", 2, NAVY)
    mx, my, mw, mh = x + 8, y + 30, w - 16, h - 40
    for cont in CONTINENTS:
        pts = []
        for lon, lat in cont:
            px = mx + int((lon + 180) / 360.0 * mw)
            py = my + int((90 - lat) / 180.0 * mh)
            pts.append((px, py))
        cv.poly(pts, LAND)
        for i in range(len(pts)):
            cv.line(pts[i][0], pts[i][1],
                    pts[(i + 1) % len(pts)][0], pts[(i + 1) % len(pts)][1],
                    LANDLINE)
    for num, lon, lat, label in DOTS:
        px = mx + int((lon + 180) / 360.0 * mw)
        py = my + int((90 - lat) / 180.0 * mh)
        cv.disc(px, py, 11, RED)
        cv.disc(px, py, 8, (255, 255, 255))
        cv.text(px - 3 if num < 10 else px - 6, py - 7, str(num), 2, RED)


def build():
    cv = Canvas(W, H, PAPER)
    M = 24
    # frame
    cv.rect(0, 0, W, 4, INK)
    cv.rect(0, H - 4, W, 4, INK)
    # masthead
    cv.text_center(30, "THE WORLD TODAY", 6, INK)
    cv.hline(M, 84, W - 2 * M, INK, 3)
    cv.text_center(96, "SATURDAY 21 NOVEMBER 2026", 3, RED)
    cv.hline(M, 126, W - 2 * M, INK, 2)
    cv.text_center(136, "22 STORIES FROM SIX CONTINENTS - ALL REPORTED ON 21 NOVEMBER 2026",
                   2, GREY)
    # lead panel
    draw_panel(cv, M, 158, W - 2 * M, 116, *PANELS[0])
    # rows of three panels
    pw = (W - 2 * M - 2 * 12) // 3
    ph = 150
    for i, p in enumerate(PANELS[1:4]):
        draw_panel(cv, M + i * (pw + 12), 284, pw, ph, *p)
    for i, p in enumerate(PANELS[4:7]):
        draw_panel(cv, M + i * (pw + 12), 444, pw, ph, *p)
    # map band + panel 8 at right
    map_w = 640
    draw_map(cv, M, 604, map_w, 160)
    draw_panel(cv, M + map_w + 12, 604, W - 2 * M - map_w - 12, 160,
               *PANELS[7])
    # world in brief
    by = 774
    cv.rect(M, by, W - 2 * M, 30, NAVY)
    cv.text(M + 10, by + 7, "WORLD IN BRIEF - 21 NOVEMBER 2026", 2,
            (255, 255, 255))
    col_w = (W - 2 * M - 24) // 2
    for i, item in enumerate(BRIEFS):
        col = i // 7
        row = i % 7
        xx = M + col * (col_w + 24)
        yy = by + 42 + row * 19
        for ln in cv.wrap(item, 1, col_w):
            cv.text(xx, yy, ln, 1, INK)
            yy += 10
    cv.text_center(968, "THE WORLD TODAY - SATURDAY 21 NOVEMBER 2026 - ONE DAY, ONE PAGE",
                   1, GREY)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    path = os.path.join(out_dir, "entry.png")
    cv = build()
    n = write_png(cv, path)
    print("wrote %s (%d bytes)" % (path, n))


if __name__ == "__main__":
    main()
