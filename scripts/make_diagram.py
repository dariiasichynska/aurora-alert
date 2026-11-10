"""Draws assets/architecture.svg and assets/banner.svg (hand-built SVG, no deps)."""
import pathlib
A = pathlib.Path(__file__).resolve().parent.parent / "assets"
SURF, CARD, LINE, INK, INK2 = "#0d1117", "#161b22", "#30363d", "#f0efec", "#9aa4b2"
GREEN, BLUE, VIOLET = "#3ee08f", "#3987e5", "#9085e9"
FONT = "font-family='-apple-system,Segoe UI,Helvetica,Arial,sans-serif'"

def node(x, y, w, h, icon, title, sub, accent):
    return (f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='10' fill='{CARD}' stroke='{LINE}'/>"
            f"<rect x='{x}' y='{y}' width='4' height='{h}' rx='2' fill='{accent}'/>"
            f"<text x='{x+16}' y='{y+26}' {FONT} font-size='15' fill='{INK}' font-weight='600'>{title}</text>"
            + "".join(f"<text x='{x+16}' y='{y+46+i*15}' {FONT} font-size='11.5' fill='{INK2}'>{s}</text>"
                      for i, s in enumerate(sub)))

def arrow(x1, x2, y):
    return (f"<line x1='{x1}' y1='{y}' x2='{x2-7}' y2='{y}' stroke='{INK2}' stroke-width='1.6'/>"
            f"<path d='M{x2-8},{y-5} L{x2},{y} L{x2-8},{y+5} z' fill='{INK2}'/>")

def gate(cx, y, lines):
    out = (f"<path d='M{cx-9},{y-8} h18 l-6,8 v7 l-6,3 v-10 z' fill='none' stroke='{GREEN}' "
           f"stroke-width='1.4' stroke-linejoin='round'/>")
    for i, l in enumerate(lines):
        out += (f"<text x='{cx}' y='{y+26+i*14}' text-anchor='middle' {FONT} font-size='11' "
                f"fill='{GREEN}'>{l}</text>")
    return out

def lane(y0, title, cadence, nodes, gates):
    W, H, GAP, X0 = 172, 86, 48, 24
    s = (f"<text x='{X0}' y='{y0}' {FONT} font-size='17' font-weight='700' fill='{INK}'>{title}</text>"
         f"<text x='{X0}' y='{y0+20}' {FONT} font-size='12' fill='{INK2}'>{cadence}</text>")
    y = y0 + 38
    for i, n in enumerate(nodes):
        x = X0 + i * (W + GAP)
        s += node(x, y, W, H, *n)
        if i < len(nodes) - 1:
            s += arrow(x + W + 4, x + W + GAP - 4, y + H / 2)
            if gates[i]:
                s += gate(x + W + GAP / 2, y + H + 22, gates[i])
    return s

fly = lane(110, "① Soll ich zu Aurora fliegen?  — trip planner",
           "Daily at 21:00 · looks 2 days ahead (22:00 local) · 5 sites in Lapland",
           [("⏰", "Schedule", ["daily 21:00", "Make scheduler"], VIOLET),
            ("☁️", "Open-Meteo", ["cloud_cover + _low", "Abisko · Kiruna · Saariselkä", "Levi · Rovaniemi"], BLUE),
            ("🌍", "NOAA Kp", ["planetary K-index", "3-day forecast"], BLUE),
            ("💨", "NOAA wind", ["solar-wind speed", "coronal-hole hint"], BLUE),
            ("✈️", "Telegram", ["private chat", "+ public channel", "Google Flights links"], GREEN)],
           [["low clouds &lt; 40 %", "at any site"], ["Kp ≥ 3.67"], None, None])
live = lane(390, "② Soll ich raus für Aurora?  — go-outside alarm",
            "Every 30 min · 20:00–06:00 · real-time solar wind at L1 (≈ 30–60 min lead time)",
            [("⏰", "Schedule", ["every 30 min", "night window only"], VIOLET),
             ("🧲", "NOAA IMF", ["Bz (GSM) + Bt", "magnetic field"], BLUE),
             ("💨", "NOAA wind", ["proton speed", "km/s"], BLUE),
             ("🚨", "Telegram", ["plain-language alert", "+ camera settings"], GREEN)],
            [["−100 &lt; Bz &lt; −3 nT", "(field points south)"], ["speed > 450 km/s"], None])

svg = (f"<svg xmlns='http://www.w3.org/2000/svg' width='1100' height='640' viewBox='0 0 1100 640'>"
       f"<defs><linearGradient id='g' x1='0' x2='1'><stop offset='0' stop-color='{GREEN}'/>"
       f"<stop offset='.55' stop-color='{BLUE}'/><stop offset='1' stop-color='{VIOLET}'/></linearGradient></defs>"
       f"<rect width='1100' height='640' rx='16' fill='{SURF}'/>"
       f"<rect x='0' y='0' width='1100' height='5' rx='2' fill='url(#g)'/>"
       f"<text x='24' y='52' {FONT} font-size='22' font-weight='700' fill='{INK}'>Two Make.com scenarios, three public data feeds, zero servers</text>"
       f"<text x='24' y='76' {FONT} font-size='13' fill='{INK2}'>Each filter stops the run early — later HTTP calls and Telegram are never executed (and never billed as operations).</text>"
       f"{fly}{live}"
       f"<text x='24' y='620' {FONT} font-size='11' fill='{INK2}'>Data: Open-Meteo forecast API · NOAA SWPC products (K-index forecast, solar-wind mag field, solar-wind speed) · Delivery: Telegram Bot API</text>"
       f"</svg>")
(A / "architecture.svg").write_text(svg, encoding="utf-8")

banner = (f"<svg xmlns='http://www.w3.org/2000/svg' width='1100' height='260' viewBox='0 0 1100 260'>"
          f"<defs><linearGradient id='sky' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='#05070d'/>"
          f"<stop offset='1' stop-color='#0d1117'/></linearGradient>"
          f"<linearGradient id='a1' x1='0' x2='1'><stop offset='0' stop-color='{GREEN}' stop-opacity='0'/>"
          f"<stop offset='.3' stop-color='{GREEN}' stop-opacity='.75'/><stop offset='.7' stop-color='#2bd3c6' stop-opacity='.55'/>"
          f"<stop offset='1' stop-color='{VIOLET}' stop-opacity='0'/></linearGradient>"
          f"<filter id='blur' x='-20%' y='-80%' width='140%' height='260%'><feGaussianBlur stdDeviation='14'/></filter></defs>"
          f"<rect width='1100' height='260' rx='16' fill='url(#sky)'/>"
          f"<g filter='url(#blur)'>"
          f"<path d='M-20,150 C180,40 330,170 520,90 S860,30 1120,120 L1120,175 C860,90 700,190 520,140 S180,110 -20,200 z' fill='url(#a1)'/>"
          f"<path d='M80,120 C260,70 420,130 600,70 S900,90 1060,60 L1060,85 C900,120 760,100 600,105 S260,110 80,150 z' fill='{VIOLET}' opacity='.35'/></g>"
          + "".join(f"<circle cx='{x}' cy='{y}' r='{r}' fill='#fff' opacity='{o}'/>" for x, y, r, o in
                    [(60,30,1.2,.8),(140,70,.8,.6),(260,25,1,.7),(400,45,.7,.5),(530,22,1.3,.8),(690,40,.8,.6),
                     (820,18,1,.7),(930,55,.9,.6),(1040,28,1.2,.8),(330,60,.6,.5),(760,65,.7,.5)])
          + f"<path d='M0,225 L90,205 L160,218 L250,196 L360,214 L470,200 L560,220 L680,198 L790,216 L900,202 L1010,219 L1100,206 L1100,260 L0,260 z' fill='#05070d'/>"
          f"<text x='40' y='118' {FONT} font-size='40' font-weight='800' fill='{INK}'>Aurora Alert</text>"
          f"<text x='42' y='150' {FONT} font-size='16' fill='#c9d1d9'>Space-weather &amp; cloud data → no-code decision logic → Telegram</text>"
          f"<text x='42' y='176' {FONT} font-size='13' fill='{INK2}'>Built with Make.com · Open-Meteo · NOAA SWPC · Telegram Bot API</text>"
          f"</svg>")
(A / "banner.svg").write_text(banner, encoding="utf-8")
print("diagram + banner written")
