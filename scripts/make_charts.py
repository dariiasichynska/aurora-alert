"""Renders the README charts from data/*.csv into assets/*.svg.
Palette: first three dark-mode slots of the validated reference palette
(blue / orange / aqua), every colour also carries a direct label."""
import csv, pathlib, datetime as dt
from collections import Counter
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

ROOT = pathlib.Path(__file__).resolve().parent.parent
A = ROOT / "assets"
SURF, INK, INK2, GRID = "#0d1117", "#f0efec", "#9aa4b2", "#262c36"
BLUE, ORANGE, AQUA = "#3987e5", "#d95926", "#199e70"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "text.color": INK,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
    "ytick.color": INK2, "svg.fonttype": "none",
})

def rbar(ax, x, h, w, c, y0=0):
    ax.add_patch(FancyBboxPatch((x - w / 2, y0), w, h, boxstyle="round,pad=0,rounding_size=0.12",
                                fc=c, ec=SURF, lw=1.5, mutation_aspect=0.6))

# ---------- 1. Flight scenario: what stopped each evening ----------
rows = [r for r in csv.DictReader(open(ROOT / "data/flight_scenario_runs.csv")) if r["type"] == "auto"
        and r["timestamp_utc"][11:13] in ("19", "20")]
stage = {"1": (1, ORANGE), "2": (2, BLUE), "4": (3, AQUA), "5": (3, AQUA)}
fig, ax = plt.subplots(figsize=(10, 3.4), dpi=100)
fig.patch.set_facecolor(SURF); ax.set_facecolor(SURF)
for i, r in enumerate(rows):
    h, c = stage[r["operations"]]
    rbar(ax, i, h, 0.72, c)
ax.set_xlim(-0.8, len(rows) - 0.2); ax.set_ylim(0, 3.55)
ax.set_yticks([1, 2, 3], ["Clouds", "Kp too low", "Alert sent"])
ticks = [i for i, r in enumerate(rows) if r["timestamp_utc"][8:10] in ("15", "20", "25", "01", "05", "09")]
ax.set_xticks(ticks, [dt.date.fromisoformat(rows[i]["timestamp_utc"][:10]).strftime("%d %b") for i in ticks])
for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
ax.tick_params(left=False)
ax.yaxis.grid(True, color=GRID, lw=0.8); ax.set_axisbelow(True)
n = Counter(stage[r["operations"]][0] for r in rows)
ax.set_title(f"Flight check · {len(rows)} evenings · {n[3]} trip alerts", loc="left",
             fontsize=13, fontweight="bold", pad=22)
ax.text(0, 1.04, "How far each nightly run got: weather filter → Kp filter → Telegram",
        transform=ax.transAxes, color=INK2, fontsize=9.5)
fig.tight_layout(); fig.savefig(A / "flight-timeline.svg", facecolor=SURF, metadata={"Date": None}); plt.close(fig)

# ---------- 2. Flight funnel ----------
total, clear, alerts = len(rows), n[2] + n[3], n[3]
fig, ax = plt.subplots(figsize=(10, 2.3), dpi=100)
fig.patch.set_facecolor(SURF); ax.set_facecolor(SURF)
steps = [("Evenings checked", total, "#5d6b80"), ("Low clouds < 40 % somewhere", clear, BLUE),
         ("…and Kp ≥ 3.67 → alert", alerts, AQUA)]
for k, (lab, v, c) in enumerate(steps):
    y = 2 - k
    ax.barh(y, v, height=0.62, color=c, edgecolor=SURF, lw=2)
    ax.text(-0.6, y, lab, ha="right", va="center", color=INK, fontsize=10.5)
    ax.text(v + 0.4, y, f"{v}  ({v / total:.0%})", va="center", color=INK, fontsize=10.5, fontweight="bold")
ax.set_xlim(0, total * 1.18); ax.set_ylim(-0.5, 2.5); ax.axis("off")
fig.subplots_adjust(left=0.3, right=0.98, top=0.95, bottom=0.05)
fig.savefig(A / "flight-funnel.svg", facecolor=SURF, metadata={"Date": None}); plt.close(fig)

# ---------- 3. Live scenario: 15-minute heat strip over two storm nights ----------
live = list(csv.DictReader(open(ROOT / "data/live_scenario_runs.csv")))
col = {"bz_not_south": BLUE, "wind_too_slow": ORANGE, "alert_sent": AQUA}
nights = {}
for r in live:
    t = dt.datetime.strptime(r["timestamp_utc"], "%Y-%m-%dT%H:%MZ") + dt.timedelta(hours=2)  # CEST
    night = (t - dt.timedelta(hours=12)).date()
    slot = ((t.hour - 20) % 24) * 4 + t.minute // 15
    nights.setdefault(night, {})[slot] = r["outcome"]
fig, ax = plt.subplots(figsize=(10, 2.9), dpi=100)
fig.patch.set_facecolor(SURF); ax.set_facecolor(SURF)
labels = []
for row, (night, slots) in enumerate(sorted(nights.items())):
    y = len(nights) - 1 - row
    for s in range(41):
        c = col.get(slots.get(s), None)
        ax.add_patch(FancyBboxPatch((s + 0.08, y + 0.12), 0.84, 0.76, boxstyle="round,pad=0,rounding_size=0.12",
                                    fc=c or "none", ec=c or GRID, lw=0 if c else 0.6, ls=":"))
    k = sum(v == "alert_sent" for v in slots.values())
    labels.append((y, f"{night:%a %d.%m}", f"{k} alerts" if k else "0 alerts"))
for y, a, b in labels:
    ax.text(-0.6, y + 0.5, a, ha="right", va="center", color=INK, fontsize=10)
    ax.text(41.6, y + 0.5, b, ha="left", va="center", color=INK, fontsize=10, fontweight="bold")
ax.set_xlim(-0.2, 41); ax.set_ylim(0, len(nights) + 0.1)
ax.set_xticks([0, 8, 16, 24, 32, 40], ["20:00", "22:00", "00:00", "02:00", "04:00", "06:00"])
ax.set_yticks([])
for s in ("top", "right", "left", "bottom"): ax.spines[s].set_visible(False)
ax.tick_params(bottom=False)
ax.set_title("Live check · every 15 min · nights of 20 – 22 Oct 2026 (local time)", loc="left",
             fontsize=13, fontweight="bold", pad=34)
for i, (lab, c) in enumerate([("Bz not south enough", BLUE), ("Wind ≤ 450 km/s", ORANGE),
                              ("Alert sent", AQUA), ("no run logged", None)]):
    x = i * 0.25
    ax.add_patch(FancyBboxPatch((x, 1.11), 0.018, 0.07, transform=ax.transAxes, clip_on=False,
                                boxstyle="round,pad=0,rounding_size=0.004",
                                fc=c or "none", ec=c or INK2, lw=0 if c else 0.8, ls=":"))
    ax.text(x + 0.026, 1.145, lab, transform=ax.transAxes, va="center", color=INK2, fontsize=9.5)
fig.subplots_adjust(left=0.1, right=0.9, top=0.72, bottom=0.12)
fig.savefig(A / "live-heatstrip.svg", facecolor=SURF, metadata={"Date": None}); plt.close(fig)
print("charts written to", A)
