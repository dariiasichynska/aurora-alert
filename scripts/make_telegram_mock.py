"""Draws assets/telegram-messages.svg: the two alert templates as chat bubbles.
Numbers are ILLUSTRATIVE (template filled with sample values), labelled as such."""
import pathlib
from xml.sax.saxutils import escape
A = pathlib.Path(__file__).resolve().parent.parent / "assets"
FONT = "font-family='-apple-system,Segoe UI,Helvetica,Arial,sans-serif'"
BG, BUBBLE, INK, INK2, LINK = "#0e1621", "#182533", "#f0efec", "#8b9bab", "#6ab3f3"

fly = ["🌌 Aurora 09.11, 22:00", "⚡ Kp: 4.33", "", "In brackets: low clouds. They decide.", "━━━━━━━━━━━━━━",
       "🇸🇪 ABISKO / KIRUNA", "Abisko 35% (12%) · Kiruna 60% (48%)", "✈️ KRN — 90 km", "§google.com/travel/flights?q=…KRN…",
       "✈️ LLA — 340 km, +4 h", "§google.com/travel/flights?q=…LLA…", "━━━━━━━━━━━━━━",
       "🇫🇮 SAARISELKÄ — 20% (5%)", "✈️ IVL", "§google.com/travel/flights?q=…IVL…", "━━━━━━━━━━━━━━",
       "🇫🇮 LEVI — 72% (66%)  ·  🇫🇮 ROVANIEMI — 41% (30%)", "", "🌞💨 Solar wind: 612 km/s",
       "⚡ Looks like a coronal hole — expect a repeat around 06.12"]
live = ["🚨🌌 AURORA ALERT — GO OUTSIDE!", "", "⏱ It should start within 30–60 minutes.", "Dress warmly, this takes more than five minutes.",
        "", "🧭 Look NORTH", "Away from street lights. At first you will only see", "a grey band above the horizon — that is it.",
        "━━━━━━━━━━━━━━", "🚪 Door to the atmosphere: WIDE OPEN", "(−12.4 nT — the more negative, the better)", "",
        "💨 Solar wind: very fast", "(640 km/s)", "", "🔋 Power reserve: large — check again", "in half an hour  (17.8 nT)",
        "━━━━━━━━━━━━━━", "📷 5–10 s, ISO 1600, focus at ∞, tripod"]

def bubble(x, title, lines):
    h = 70 + 19 * len(lines)
    s = (f"<text x='{x}' y='40' {FONT} font-size='14' font-weight='700' fill='{INK}'>{title}</text>"
         f"<rect x='{x}' y='56' width='470' height='{h}' rx='14' fill='{BUBBLE}'/>"
         f"<text x='{x+16}' y='82' {FONT} font-size='13' font-weight='700' fill='{LINK}'>Aurora Alert bot</text>")
    for i, l in enumerate(lines):
        c = LINK if l.startswith("§") else INK
        s += (f"<text x='{x+16}' y='{106+i*19}' {FONT} font-size='13' fill='{c}'>{escape(l.lstrip('§'))}</text>")
    s += f"<text x='{x+454}' y='{56+h-12}' text-anchor='end' {FONT} font-size='11' fill='{INK2}'>21:00 ✓✓</text>"
    return s, h

a, ha = bubble(20, "① Trip planner — daily 21:00", fly)
b, hb = bubble(510, "② Go-outside alarm — real time", live)
H = max(ha, hb) + 100
svg = (f"<svg xmlns='http://www.w3.org/2000/svg' width='1000' height='{H}' viewBox='0 0 1000 {H}'>"
       f"<rect width='1000' height='{H}' rx='16' fill='{BG}'/>{a}{b}"
       f"<text x='20' y='{H-16}' {FONT} font-size='11' fill='{INK2}'>Message layouts are the real Make templates; the numbers shown are illustrative sample values.</text></svg>")
(A / "telegram-messages.svg").write_text(svg, encoding="utf-8")
print("telegram mock written")
