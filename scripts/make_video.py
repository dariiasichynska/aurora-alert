"""Renders assets/aurora-walkthrough.mp4 (1280x720, 30 fps) and a README GIF.
Animated walkthrough of one run of each Make scenario. Values are illustrative."""
import math, pathlib, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"; TMP = pathlib.Path("/tmp/aurora_video"); TMP.mkdir(exist_ok=True)
W, H, FPS, SS = 1280, 720, 30, 2           # draw at 2x, downsample for anti-aliasing
BG, CARD, LINE, INK, INK2 = (13, 17, 23), (22, 27, 34), (48, 54, 61), (240, 239, 236), (154, 164, 178)
GREEN, BLUE, VIOLET, RED, AMBER = (62, 224, 143), (57, 135, 229), (144, 133, 233), (230, 103, 103), (232, 170, 60)
FD = "/usr/share/fonts/opentype/inter/"
_f = {}
def font(size, w="Regular"):
    k = (size, w)
    if k not in _f: _f[k] = ImageFont.truetype(FD + f"Inter-{w}.otf", size * SS)
    return _f[k]

def ease(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)
def seg(t, a, b): return ease((t - a) / (b - a))
def mix(c1, c2, k): return tuple(int(c1[i] + (c2[i] - c1[i]) * k) for i in range(3))

class Canvas:
    def __init__(self):
        self.im = Image.new("RGB", (W * SS, H * SS), BG); self.d = ImageDraw.Draw(self.im)
    def S(self, *v): return [x * SS for x in v]
    def text(self, x, y, s, size=18, w="Regular", fill=INK, anchor="la", alpha=1.0):
        self.d.text(self.S(x, y), s, font=font(size, w), fill=mix(BG, fill, alpha), anchor=anchor)
    def rrect(self, x, y, w, h, r=12, fill=CARD, outline=LINE, width=1, alpha=1.0):
        self.d.rounded_rectangle(self.S(x, y, x + w, y + h), r * SS, fill=mix(BG, fill, alpha),
                                 outline=mix(BG, outline, alpha) if outline else None, width=width * SS)
    def line(self, x1, y1, x2, y2, fill=INK2, width=2, alpha=1.0):
        self.d.line(self.S(x1, y1, x2, y2), fill=mix(BG, fill, alpha), width=width * SS)
    def circle(self, x, y, r, fill, alpha=1.0):
        self.d.ellipse(self.S(x - r, y - r, x + r, y + r), fill=mix(BG, fill, alpha))
    def glow(self, x, y, color, k=1.0):
        g = Image.new("RGB", self.im.size, (0, 0, 0)); gd = ImageDraw.Draw(g)
        r = 26 * SS; gd.ellipse((x * SS - r, y * SS - r, x * SS + r, y * SS + r), fill=mix((0, 0, 0), color, 0.8 * k))
        g = g.filter(ImageFilter.GaussianBlur(14 * SS))
        self.im = Image.fromarray(__import__("numpy").clip(
            __import__("numpy").asarray(self.im, dtype="int16") + __import__("numpy").asarray(g, dtype="int16"), 0, 255).astype("uint8"))
        self.d = ImageDraw.Draw(self.im); self.circle(x, y, 7, mix(color, (255, 255, 255), 0.4))
    def frame(self): return self.im.resize((W, H), Image.LANCZOS)

def header(c, title, sub, alpha=1.0, note=True):
    c.rrect(0, 0, W, 6, r=0, fill=GREEN, outline=None, alpha=alpha)
    c.text(48, 40, title, 30, "Bold", alpha=alpha)
    c.text(48, 82, sub, 17, fill=INK2, alpha=alpha)
    if note: c.text(W - 48, H - 30, "illustrative values · real scenario logic", 13, fill=INK2, anchor="ra", alpha=alpha * 0.9)

def node(c, x, y, title, sub, accent, alpha=1.0, lit=0.0, dim=False):
    a = alpha * (0.35 if dim else 1.0)
    c.rrect(x, y, 190, 96, fill=mix(CARD, accent, 0.18 * lit), outline=mix(LINE, accent, lit), width=2, alpha=a)
    c.rrect(x, y, 5, 96, r=2, fill=accent, outline=None, alpha=a)
    c.text(x + 20, y + 22, title, 20, "SemiBold", alpha=a)
    for i, s in enumerate(sub): c.text(x + 20, y + 54 + i * 20, s, 14, fill=INK2, alpha=a)

def gate(c, cx, y, label, state, alpha=1.0):
    """state: None (pending), True (pass), False (stop)."""
    col = INK2 if state is None else (GREEN if state else RED)
    c.d.polygon([tuple(c.S(cx - 11, y - 9)), tuple(c.S(cx + 11, y - 9)), tuple(c.S(cx + 3, y + 1)),
                 tuple(c.S(cx + 3, y + 10)), tuple(c.S(cx - 3, y + 13)), tuple(c.S(cx - 3, y + 1))],
                outline=mix(BG, col, alpha), width=2 * SS)
    c.text(cx, y + 26, label, 14, "SemiBold", fill=col, anchor="ma", alpha=alpha)
    if state is not None:
        c.text(cx, y + 48, "PASS" if state else "STOP", 14, "Bold", fill=col, anchor="ma", alpha=alpha)

def ops_counter(c, n, alpha=1.0):
    c.rrect(W - 250, 34, 202, 58, fill=CARD, alpha=alpha)
    c.text(W - 234, 46, "Make operations", 13, fill=INK2, alpha=alpha)
    c.text(W - 234, 64, str(n), 22, "Bold", fill=GREEN if n else INK2, alpha=alpha)

def data_card(c, x, y, lines, alpha, accent=BLUE):
    if alpha <= 0: return
    w = max(font(15).getlength(l) for l in lines) / SS + 36
    c.rrect(x, y, w, 20 + 24 * len(lines), fill=(17, 26, 38), outline=accent, alpha=alpha)
    for i, l in enumerate(lines): c.text(x + 18, y + 12 + i * 24, l, 15, alpha=alpha)

def fade(t, dur): return min(1.0, t / 0.4, (dur - t) / 0.4)

# ------------------------------------------------------------------ scenes
X0, GAP, NW = 48, 48, 190
def nx(i): return X0 + i * (NW + GAP)
NY = 230; CY = NY + 48

def pulse_pos(t, path):
    """path: list of (t0, t1, i_from, i_to) -> current (x, y) of the data pulse or None."""
    for t0, t1, a, b in path:
        if t0 <= t <= t1:
            k = ease((t - t0) / (t1 - t0)); return nx(a) + NW + (nx(b) - nx(a) - NW) * k, CY
    return None

def scene_title(t, dur=3.5):
    c = Canvas(); a = fade(t, dur)
    for i, col in enumerate([GREEN, BLUE, VIOLET]):
        yy = 250 + i * 18 + 10 * math.sin(t * 1.4 + i)
        c.rrect(80 + 60 * i, yy, W - 160 - 120 * i, 6, r=3, fill=col, outline=None, alpha=a * 0.6)
    c.text(W / 2, 330, "Aurora Alert", 64, "Bold", anchor="mm", alpha=a)
    c.text(W / 2, 400, "How one run of each Make scenario works", 24, fill=INK2, anchor="mm", alpha=a)
    c.text(W / 2, 450, "Open-Meteo  ·  NOAA SWPC  ·  Telegram Bot API", 18, fill=INK2, anchor="mm", alpha=a)
    return c.frame()

FLY = [("Schedule", ["daily 21:00"], VIOLET), ("Open-Meteo", ["clouds, 5 sites", "+2 days, 22:00"], BLUE),
       ("NOAA Kp", ["3-day forecast"], BLUE), ("NOAA wind", ["solar-wind speed"], BLUE),
       ("Telegram", ["chat + channel", "+ flight links"], GREEN)]

def scene_fly(t, dur=16.0):
    c = Canvas(); a = fade(t, dur)
    header(c, "① Soll ich zu Aurora fliegen?", "Trip planner — a night with an alert", a)
    path = [(1.0, 2.2, 0, 1), (5.0, 6.2, 1, 2), (8.4, 9.6, 2, 3), (10.6, 11.8, 3, 4)]
    reached = [0.0, 2.2, 6.2, 9.6, 11.8]
    ops = sum(1 for r in reached[1:] if t >= r) + (1 if t >= 12.6 else 0)
    ops_counter(c, ops, a)
    for i, (ti, sub, col) in enumerate(FLY):
        lit = seg(t, reached[i], reached[i] + 0.4) * (1 - 0.6 * seg(t, reached[i] + 1.8, reached[i] + 2.4)) if i else 0
        if i == 4: lit = seg(t, 11.8, 12.3)
        node(c, nx(i), NY, ti, sub, col, alpha=a * seg(t, 0.1 * i, 0.1 * i + 0.6), lit=lit)
        if i < 4: c.line(nx(i) + NW + 4, CY, nx(i + 1) - 6, CY, alpha=a * 0.8)
    gate(c, nx(1) + NW + GAP / 2, NY + 140, "low clouds < 40 %", True if t > 4.4 else None, a)
    gate(c, nx(2) + NW + GAP / 2, NY + 140, "Kp ≥ 3.67", True if t > 7.8 else None, a)
    data_card(c, nx(1) - 20, NY + 230, ["Low clouds at 22:00 (+2 days)", "Abisko 12 %  ·  Kiruna 48 %",
              "Saariselkä 5 %  ·  Levi 66 %", "Rovaniemi 30 %   →  3 sites clear"], a * seg(t, 2.4, 2.9) * (1 - seg(t, 4.8, 5.2)))
    data_card(c, nx(2) - 20, NY + 230, ["Kp forecast for that night: 4.33", "≥ 3.67  →  strong enough to fly"],
              a * seg(t, 6.4, 6.9) * (1 - seg(t, 8.2, 8.6)))
    data_card(c, nx(3) - 60, NY + 230, ["Solar wind: 612 km/s", "> 580  →  coronal-hole hint, repeat in ~27 days"],
              a * seg(t, 9.8, 10.3) * (1 - seg(t, 11.4, 11.8)))
    data_card(c, nx(3) - 40, NY + 230, ["Telegram → private chat + public channel", "cloud cover per site · Kp · wind",
              "Google Flights links for KRN · LLA · IVL · KTT · RVN"], a * seg(t, 12.4, 12.9), accent=GREEN)
    p = pulse_pos(t, path)
    if p: c.glow(p[0], p[1], GREEN)
    return c.frame()

def scene_quiet(t, dur=8.0):
    c = Canvas(); a = fade(t, dur)
    header(c, "① Most evenings look like this", "The filter stops the run early — Telegram never runs, almost nothing is billed", a)
    path = [(0.8, 1.8, 0, 1), (2.6, 3.6, 1, 2)]
    ops = (1 if t >= 1.8 else 0) + (1 if t >= 3.6 else 0)
    ops_counter(c, ops, a)
    for i, (ti, sub, col) in enumerate(FLY):
        node(c, nx(i), NY, ti, sub, col, alpha=a, dim=(i >= 3 and t > 4.6), lit=0.7 if (i == 2 and 3.6 < t < 4.6) else 0)
        if i < 4: c.line(nx(i) + NW + 4, CY, nx(i + 1) - 6, CY, alpha=a * (0.25 if (i >= 2 and t > 4.6) else 0.8))
    gate(c, nx(1) + NW + GAP / 2, NY + 140, "low clouds < 40 %", True if t > 2.2 else None, a)
    gate(c, nx(2) + NW + GAP / 2, NY + 140, "Kp ≥ 3.67", False if t > 4.4 else None, a)
    data_card(c, nx(2) - 20, NY + 230, ["Kp forecast: 2.67  <  3.67", "run stops here  →  2 operations, no message"],
              a * seg(t, 4.6, 5.1), accent=RED)
    p = pulse_pos(t, path)
    if p: c.glow(p[0], p[1], GREEN)
    return c.frame()

LIVE = [("Schedule", ["every 30 min", "20:00–06:00"], VIOLET), ("NOAA IMF", ["Bz + Bt at L1"], BLUE),
        ("NOAA wind", ["proton speed"], BLUE), ("Telegram", ["go-outside alert", "chat + channel"], GREEN)]

def scene_live(t, dur=13.0):
    c = Canvas(); a = fade(t, dur)
    header(c, "② Soll ich raus für Aurora?", "Go-outside alarm — real-time solar wind, 30–60 min before it hits Earth", a)
    path = [(1.0, 2.2, 0, 1), (4.6, 5.8, 1, 2), (8.0, 9.2, 2, 3)]
    reached = [0, 2.2, 5.8, 9.2]
    ops = sum(1 for r in reached[1:] if t >= r) + (1 if t >= 9.8 else 0)
    ops_counter(c, ops, a)
    for i, (ti, sub, col) in enumerate(LIVE):
        lit = seg(t, 9.2, 9.7) if i == 3 else (seg(t, reached[i], reached[i] + .4) * (1 - .6 * seg(t, reached[i] + 1.8, reached[i] + 2.4)) if i else 0)
        node(c, nx(i), NY, ti, sub, col, alpha=a * seg(t, 0.1 * i, 0.1 * i + 0.6), lit=lit)
        if i < 3: c.line(nx(i) + NW + 4, CY, nx(i + 1) - 6, CY, alpha=a * 0.8)
    gate(c, nx(1) + NW + GAP / 2, NY + 140, "−100 < Bz < −3 nT", True if t > 4.0 else None, a)
    gate(c, nx(2) + NW + GAP / 2, NY + 140, "speed > 450 km/s", True if t > 7.4 else None, a)
    data_card(c, nx(1) - 20, NY + 230, ["Bz = −12.4 nT  →  field points south", "“doors wide open” (< −10)",
              "Bt = 17.8 nT  →  big power reserve"], a * seg(t, 2.4, 2.9) * (1 - seg(t, 4.4, 4.8)))
    data_card(c, nx(2) - 20, NY + 230, ["Proton speed: 640 km/s", "“very fast” (> 600)"],
              a * seg(t, 6.0, 6.5) * (1 - seg(t, 7.8, 8.2)))
    data_card(c, nx(2) - 20, NY + 230, ["ПОЛЯРНЕ СЯЙВО — ВИХОДЬ!", "look north, away from street lights",
              "camera: 5–10 s · ISO 1600 · focus ∞ · tripod"], a * seg(t, 9.8, 10.3), accent=GREEN)
    p = pulse_pos(t, path)
    if p: c.glow(p[0], p[1], GREEN)
    return c.frame()

def scene_stats(t, dur=7.0):
    c = Canvas(); a = fade(t, dur)
    header(c, "Real numbers from the Make execution log", "9 Oct – 9 Nov 2026", a, note=False)
    cards = [("32", "evening runs of the trip planner", "all successful"),
             ("9", "trip alerts", "28 % of evenings"),
             ("2.5", "operations per evening", "≈ 75 per month"),
             ("21", "live alerts in 2 storm nights", "→ next: cooldown")]
    for i, (big, l1, l2) in enumerate(cards):
        k = a * seg(t, 0.4 + 0.35 * i, 1.0 + 0.35 * i); x = 48 + i * 300
        c.rrect(x, 200 - 20 * (1 - k), 276, 220, fill=CARD, alpha=k)
        c.text(x + 24, 230 - 20 * (1 - k), big, 64, "Bold", fill=GREEN if i < 3 else AMBER, alpha=k)
        c.text(x + 24, 330 - 20 * (1 - k), l1, 16, alpha=k)
        c.text(x + 24, 360 - 20 * (1 - k), l2, 15, fill=INK2, alpha=k)
    c.text(W / 2, 520, "No servers · no code to host · free tier", 22, "SemiBold", fill=INK2, anchor="mm", alpha=a * seg(t, 2.0, 2.6))
    c.text(W / 2, 580, "Built by Dariia Sichynska", 20, "SemiBold", fill=INK, anchor="mm", alpha=a * seg(t, 2.8, 3.4))
    return c.frame()

SCENES = [("01_title", scene_title, 3.5), ("02_fly", scene_fly, 16.0), ("03_quiet", scene_quiet, 8.0),
          ("04_live", scene_live, 13.0), ("05_stats", scene_stats, 7.0)]

def render(name, fn, dur):
    tmp, final = TMP / f"{name}.tmp.mp4", TMP / f"{name}.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
                          "-pix_fmt", "yuv420p", str(tmp)], stdin=subprocess.PIPE)
    for f in range(int(dur * FPS)):
        p.stdin.write(fn(f / FPS, dur).tobytes() if fn.__code__.co_argcount == 2 else fn(f / FPS).tobytes())
    p.stdin.close()
    if p.wait() == 0: tmp.rename(final)
    else: sys.exit(f"render failed: {name}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "preview":   # stills at the busiest moments
        for name, fn, dur, t in [("fly", scene_fly, 16, 3.6), ("fly2", scene_fly, 16, 14), ("quiet", scene_quiet, 8, 6),
                                 ("live", scene_live, 13, 11.5), ("stats", scene_stats, 7, 4), ("title", scene_title, 3.5, 1.7)]:
            fn(t, dur).save(f"/tmp/prev/v_{name}.png")
        sys.exit()
    for s in SCENES: render(*s)
    (TMP / "list.txt").write_text("".join(f"file '{TMP / (n + '.mp4')}'\n" for n, _, _ in SCENES))
    mp4 = OUT / "aurora-walkthrough.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(TMP / "list.txt"),
                    "-c", "copy", "-movflags", "+faststart", str(mp4)], check=True)
    gif = OUT / "aurora-walkthrough.gif"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(mp4), "-vf",
                    "fps=12,scale=900:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=96[p];[b][p]paletteuse=dither=bayer:bayer_scale=4",
                    str(gif)], check=True)
    print("written", mp4, gif)
