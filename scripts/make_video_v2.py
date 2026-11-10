"""Walkthrough video built from real Make.com screenshots (video_src/*.jpg).
Output: assets/aurora-walkthrough.mp4 (1280x720, 30 fps) + assets/aurora-walkthrough.gif"""
import math, pathlib, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import make_video as v1          # reuse title + stats scenes and fonts

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC, OUT = ROOT / "video_src", ROOT / "assets"
TMP = pathlib.Path("/tmp/aurora_video2"); TMP.mkdir(exist_ok=True)
W, H, FPS = 1280, 720, 30
INK, INK2, GREEN, VIOLET, BLUE = (240, 239, 236), (170, 178, 190), (62, 224, 143), (144, 133, 233), (57, 135, 229)
def font(s, w="Regular"): return v1.ImageFont.truetype(v1.FD + f"Inter-{w}.otf", s)
ease, seg = v1.ease, v1.seg
_cache = {}
def src(name):
    if name not in _cache: _cache[name] = Image.open(SRC / name).convert("RGB")
    return _cache[name]

def shot(t, dur, name, z0, z1, caption, step, path=None, path_t=(0.6, 3.2), top=False):
    """Ken-Burns over a real screenshot. z = (cx, cy, zoom) in source px (800x450 frame)."""
    im = src(name); sw, sh = im.size; k = ease(t / dur)
    cx, cy, z = (z0[i] + (z1[i] - z0[i]) * k for i in range(3))
    w, h = sw / z, sh / z
    x0 = min(max(cx - w / 2, 0), sw - w); y0 = min(max(cy - h / 2, 0), sh - h)
    fr = im.resize((W, H), Image.LANCZOS, box=(x0, y0, x0 + w, y0 + h)).convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    def to_frame(px, py): return ((px - x0) * W / w, (py - y0) * H / h)
    if path:                                   # data pulse travelling over the real canvas
        p = (t - path_t[0]) / (path_t[1] - path_t[0])
        if 0 <= p <= 1:
            n = len(path) - 1; i = min(int(p * n), n - 1); q = ease(p * n - i)
            px = path[i][0] + (path[i + 1][0] - path[i][0]) * q; py = path[i][1] + (path[i + 1][1] - path[i][1]) * q
            fx, fy = to_frame(px, py)
            g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
            gd.ellipse((fx - 34, fy - 34, fx + 34, fy + 34), fill=GREEN + (170,))
            ov = Image.alpha_composite(ov, g.filter(ImageFilter.GaussianBlur(16))); d = ImageDraw.Draw(ov)
            d.ellipse((fx - 9, fy - 9, fx + 9, fy + 9), fill=(220, 255, 235, 255))
    # caption band (bottom by default, top when the content sits at the bottom of the screenshot)
    a = min(1, t / 0.5); by = 0 if top else H - 150
    for i in range(150):
        yy = by + i; r = (150 - i) / 150 if top else i / 150
        d.line((0, yy, W, yy), fill=(8, 10, 16, int(225 * a * min(1, r * 3.75))))
    ty = 22 if top else H - 92
    d.rounded_rectangle((40, ty, 84, ty + 44), 10, fill=VIOLET + (int(255 * a),))
    d.text((62, ty + 22), step, font=font(22, "Bold"), fill=(255, 255, 255, int(255 * a)), anchor="mm")
    d.text((100, ty + 8), caption[0], font=font(24, "SemiBold"), fill=INK + (int(255 * a),))
    if len(caption) > 1: d.text((100, ty + 40), caption[1], font=font(18), fill=INK2 + (int(255 * a),))
    d.rounded_rectangle((W - 214, ty + 5, W - 24, ty + 39), 17, fill=(44, 50, 64, int(240 * a)))
    d.text((W - 119, ty + 22), "real Make.com scenario", font=font(14, "SemiBold"), fill=(255, 255, 255, int(230 * a)), anchor="mm")
    fr = Image.alpha_composite(fr, ov).convert("RGB")
    f = min(1.0, t / 0.35, (dur - t) / 0.35)
    return Image.blend(Image.new("RGB", (W, H), (8, 10, 16)), fr, max(0.0, f)) if f < 1 else fr

def ribbons(t, alpha):
    im = Image.new("RGB", (W, H), (5, 7, 13)); g = Image.new("RGB", (W, H), (0, 0, 0)); d = ImageDraw.Draw(g)
    for j, (col, base, amp, sp) in enumerate([(GREEN, 250, 60, 0.9), ((43, 211, 198), 300, 45, 1.2), (VIOLET, 210, 40, 0.7)]):
        pts = [(x, base + amp * math.sin(x / 170 + t * sp + j) + 25 * math.sin(x / 61 + t * 1.7)) for x in range(-40, W + 60, 40)]
        poly = pts + [(x, y + 70 + 30 * math.sin(x / 90 + t + j)) for x, y in reversed(pts)]
        d.polygon(poly, fill=tuple(int(c * 0.55 * alpha) for c in col))
    g = g.filter(ImageFilter.GaussianBlur(22))
    im = Image.fromarray(__import__("numpy").clip(__import__("numpy").asarray(im, "int16") + __import__("numpy").asarray(g, "int16"), 0, 255).astype("uint8"))
    dd = ImageDraw.Draw(im)
    for x, y, r in [(90, 60, 1.6), (230, 120, 1.1), (420, 50, 1.4), (610, 95, 1.0), (760, 40, 1.6), (930, 110, 1.2), (1110, 70, 1.5), (1220, 140, 1.0)]:
        tw = 0.6 + 0.4 * math.sin(t * 3 + x)
        dd.ellipse((x - r, y - r, x + r, y + r), fill=tuple(int(255 * tw * alpha) for _ in range(3)))
    dd.polygon([(0, 640), (120, 610), (230, 628), (360, 598), (520, 622), (650, 600), (800, 626), (960, 604), (1120, 628), (1280, 608), (1280, 720), (0, 720)], fill=(3, 4, 8))
    return im

def scene_beautiful(t, dur=4.0):
    a = min(1.0, t / 0.6, (dur - t) / 0.5)
    im = ribbons(t, a); d = ImageDraw.Draw(im)
    k = seg(t, 0.5, 1.4)
    d.text((W / 2, 330), "But sometimes", font=font(40, "SemiBold"), fill=tuple(int(c * k * a) for c in INK2), anchor="mm")
    k2 = seg(t, 1.1, 2.1)
    d.text((W / 2, 395), "something beautiful happens…", font=font(56, "Bold"), fill=tuple(int(c * k2 * a) for c in INK), anchor="mm")
    return im

def scene_message(t, dur=5.5):
    """The alert as it arrives in Telegram (English template, illustrative values)."""
    a = min(1.0, t / 0.4, (dur - t) / 0.4)
    im = Image.new("RGB", (W, H), (14, 22, 33)); d = ImageDraw.Draw(im)
    lines = ["🚨 AURORA ALERT — GO OUTSIDE!", "", "It should start within 30–60 minutes.", "Dress warmly, this takes more than five minutes.", "",
             "Look NORTH, away from street lights. At first you will only see", "a grey band above the horizon — that is it.", "",
             "Door to the atmosphere: WIDE OPEN   (−12.4 nT)", "Solar wind: very fast   (640 km/s)",
             "Power reserve: large — check again in half an hour   (17.8 nT)", "", "Photo: 5–10 s exposure, ISO 1600, manual focus at ∞, tripod."]
    shown = int(len(lines) * seg(t, 0.4, 2.6)) if t < 2.6 else len(lines)
    x0, y0, bw = 230, 70, 820; bh = 70 + 30 * len(lines)
    rise = 30 * (1 - seg(t, 0, 0.6))
    d.rounded_rectangle((x0, y0 + rise, x0 + bw, y0 + bh + rise), 20, fill=tuple(int(c * a) for c in (24, 37, 51)))
    d.text((x0 + 28, y0 + 22 + rise), "Aurora Alert bot", font=font(18, "Bold"), fill=tuple(int(c * a) for c in (106, 179, 243)))
    for i, l in enumerate(lines[:shown]):
        f = font(21, "SemiBold") if i == 0 else font(18)
        d.text((x0 + 28, y0 + 58 + i * 30 + rise), l.replace("🚨 ", ""), font=f, fill=tuple(int(c * a) for c in INK))
    d.text((x0 + bw - 24, y0 + bh - 16 + rise), "22:15 ✓✓", font=font(14), fill=tuple(int(c * a) for c in INK2), anchor="rs")
    d.text((W / 2, H - 40), "② What arrives in Telegram  ·  illustrative values, real template", font=font(16),
           fill=tuple(int(c * a) for c in INK2), anchor="mm")
    return im

FLY_PATH = [(133, 165), (287, 257), (405, 152), (573, 152), (725, 152)]
LIVE_PATH = [(141, 200), (340, 200), (531, 197), (716, 197)]
def S(name, dur, z0, z1, cap, step, path=None, pt=(0.6, 3.2), top=False):
    return (lambda t, d=dur: shot(t, d, name, z0, z1, cap, step, path, pt, top)), dur

SCENES = [
    ("01_title", v1.scene_title, 3.5),
    ("02_fly_editor", *S("fly_editor.jpg", 5.0, (400, 225, 1.0), (420, 215, 1.12),
        ("Soll ich zu Aurora fliegen?  —  trip planner", "Runs daily at 21:00 · checks the night two days ahead · 5 sites in Lapland"), "1", FLY_PATH, (0.7, 4.3))),
    ("03_fly_http", *S("fly_http_openmeteo.jpg", 4.0, (400, 225, 1.0), (350, 200, 1.25),
        ("Step 1 · Open-Meteo API", "Cloud cover for Abisko, Kiruna, Saariselkä, Levi, Rovaniemi · no API key needed"), "1")),
    ("04_fly_clouds", *S("fly_filter_clouds.jpg", 4.0, (400, 225, 1.0), (400, 230, 1.22),
        ("Filter · low clouds < 40 % at ANY site", "Five OR-rules: one clear site is enough to drive there"), "1")),
    ("05_fly_kp", *S("fly_filter_kp.jpg", 4.0, (400, 225, 1.0), (540, 230, 1.3),
        ("Filter · Kp forecast ≥ 3.67", "NOAA SWPC planetary K-index, 3-hour slot for 22:00 local"), "1")),
    ("06_fly_tg", *S("fly_telegram_en.jpg", 4.0, (400, 225, 1.0), (360, 260, 1.22),
        ("Telegram · private chat + public channel", "Cloud cover per site, Kp, solar wind and Google Flights links"), "1")),
    ("07_fly_run", *S("fly_run_overview.jpg", 4.5, (400, 225, 1.0), (560, 400, 1.3),
        ("Real run · 7 Nov 2026 · alert sent", "Every module executed · 5 operations · 1 second"), "1", top=True)),
    ("08_quiet", *S("fly_run_quiet.jpg", 5.5, (400, 225, 1.0), (600, 400, 1.3),
        ("Most evenings look like this", "9 Nov · Kp too low → “The bundle did not pass through the filter” · 2 operations, no message"), "1", top=True)),
    ("09_beautiful", scene_beautiful, 4.0),
    ("10_live_editor", *S("live_editor.jpg", 5.0, (400, 225, 1.0), (430, 220, 1.12),
        ("Soll ich raus für Aurora?  —  go-outside alarm", "Every 30 min, 20:00–06:00 · real-time solar wind measured at L1"), "2", LIVE_PATH, (0.7, 4.2))),
    ("11_live_bz", *S("live_filter_bz.jpg", 4.0, (400, 225, 1.0), (440, 280, 1.25),
        ("Filter · −100 < Bz < −3 nT", "Interplanetary magnetic field points south: the door to the atmosphere is open"), "2")),
    ("12_live_speed", *S("live_filter_speed.jpg", 4.0, (400, 225, 1.0), (600, 230, 1.28),
        ("Filter · solar wind faster than 450 km/s", "Fast wind delivers more energy · 30–60 minutes of warning"), "2")),
    ("13_message", scene_message, 5.5),
    ("14_stats", v1.scene_stats, 7.0),
]

def render(name, fn, dur):
    tmp, final = TMP / f"{name}.tmp.mp4", TMP / f"{name}.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
                          "-pix_fmt", "yuv420p", str(tmp)], stdin=subprocess.PIPE)
    for f in range(int(dur * FPS)):
        t = f / FPS
        p.stdin.write((fn(t, dur) if fn in (v1.scene_title, v1.scene_stats, scene_beautiful, scene_message) else fn(t)).tobytes())
    p.stdin.close()
    if p.wait() == 0: tmp.rename(final)
    else: sys.exit(f"render failed: {name}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        for name, fn, dur in SCENES:
            t = dur * 0.6
            im = fn(t, dur) if fn in (v1.scene_title, v1.scene_stats, scene_beautiful, scene_message) else fn(t)
            im.save(f"/tmp/prev/v2_{name}.png")
        sys.exit()
    for s in SCENES: render(*s)
    (TMP / "list.txt").write_text("".join(f"file '{TMP / (n + '.mp4')}'\n" for n, _, _ in SCENES))
    mp4 = OUT / "aurora-walkthrough.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(TMP / "list.txt"),
                    "-c", "copy", "-movflags", "+faststart", str(mp4)], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(mp4), "-vf",
                    "fps=10,scale=860:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer:bayer_scale=4",
                    str(OUT / "aurora-walkthrough.gif")], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "1.8", "-i", str(mp4), "-frames:v", "1", str(OUT / "aurora-walkthrough-cover.jpg")], check=True)
    print("written", mp4)
