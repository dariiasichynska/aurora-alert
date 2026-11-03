# Aurora Alert — two Make.com scenarios

Event-driven aurora monitoring built on [Make.com](https://make.com). Two scenarios answer two different questions, pull from four public API endpoints, and push plain-language alerts to Telegram: to a private group and to a public channel anyone can join.

The engineering point is cost: the system runs on Make's free tier (1,000 operations/month) and uses about **40** of them in normal operation. A naive implementation of the same logic would burn over **8,000**.

---

## The two questions

| | Scenario 1 — flight planner | Scenario 2 — tonight alert |
| --- | --- | --- |
| Question | Is it worth booking a flight? | Is it worth stepping outside right now? |
| Forecast horizon | 2 days | ~1 hour |
| Trigger | daily, 21:00 | every 30 min, 20:00–06:00 only |
| Signal | cloud cover at 5 sites + Kp forecast | IMF Bz + solar wind speed |
| Output | Telegram message with pre-dated flight-search links | Telegram alert with plain-language conditions |
| Sent to | private group + public channel | private group + public channel |
| Normally | always on | enabled on demand |

They cannot be one scenario: their forecast horizons differ by a factor of ~50.

---

## Architecture

```mermaid
flowchart LR
  subgraph S1["Scenario 1 — flight planner (daily 21:00)"]
    A1[HTTP: Open-Meteo<br/>5 locations, 1 request] --> F1{{"Clouds low &lt; 40%<br/>at any site"}}
    F1 --> A2[HTTP: NOAA<br/>Kp forecast] --> F2{{"Kp ≥ 3.67"}}
    F2 --> A3[HTTP: NOAA<br/>solar wind speed] --> A4[Telegram<br/>group] --> A5[Telegram<br/>channel]
  end
  subgraph S2["Scenario 2 — tonight alert (30 min, night window)"]
    B1[HTTP: NOAA<br/>magnetic field] --> G1{{"Bz &lt; −3<br/>and Bz &gt; −100"}}
    G1 --> B2[HTTP: NOAA<br/>solar wind speed] --> G2{{"speed &gt; 450 km/s"}}
    G2 --> B3[Telegram<br/>group] --> B4[Telegram<br/>channel]
  end
```

Both follow the same shape: fetch, filter, fetch again only if needed, notify.

---

## Why it costs ~40 operations instead of 8,700

Make bills **per executed module**, not per scenario run. Filters are free and stop everything to their right.

That single fact drives the whole design:

1. **Every expensive call sits behind a free check.** On a typical night the chain stops after module 1 — one operation, not three.
2. **Module order is not arbitrary.** The first module always runs and always costs one operation, so the first slot goes to the fetch that most often says *no* and returns the smallest payload.
3. **Time windows beat conditional logic.** A run outside the schedule window costs nothing at all. 96 runs/day become 20 runs/night.
4. **Batch what the API will batch.** Open-Meteo accepts five coordinate pairs in one request and returns an array. Five locations, one operation.
5. **One message, any number of readers.** Public alerts go to a Telegram channel, not to a list of subscribers. Sending costs one operation whether the channel has 3 readers or 3,000.

| Variant | Operations/month |
| --- | --- |
| Every 15 min, round the clock, all modules | ~8,700 |
| This architecture, normal operation | ~40 |
| This architecture, including one week of travel | ~180 |

### No iterators — on purpose

The NOAA Kp file holds ~1,400 entries. An Iterator would split it into 1,400 bundles and every downstream module would run 1,400 times. One execution would consume a month and a half of free-tier budget.

Instead the needed element is addressed directly:

```
{{parseNumber(5.data[80].kp)}}
```

---

## Public Telegram channel

Every alert goes to two places: my private Telegram group, as before, and a public channel that anyone can join. The channel link is on [dariiasichynska.github.io](https://dariiasichynska.github.io/#projekte).

The second Telegram module sits behind the same filters as the first, so it only runs when an alert is actually sent: one extra operation per alert, not per run. Alerts are rare, so this adds a few operations a month.

Why a channel and not a bot with a subscriber list:

- **Cost stays flat.** A bot that messages each subscriber individually needs a loop: every new subscriber adds one operation per alert, plus a second scenario to register `/start` commands. A channel needs neither.
- **No personal data to store.** The scenarios never see who reads the channel. No chat IDs, no names, no data store.
- **Readers stay private.** Unlike a group, channel members cannot see each other or post. The private group stays private.

Scenario 1 runs every evening, so subscribers get a message whenever a Lapland night two days ahead looks promising. Scenario 2 runs only when I switch it on, so its "go outside" alerts are occasional.

---

## Changelog

**2026-11** — tuned for the free-tier budget, published to a public channel

- Scenario 2 polls every **30 minutes** instead of 15. Half the runs per night: a week of travel now costs ~180 operations instead of ~320. Trade-off: an alert can arrive up to 30 minutes after the field turns south instead of 15.
- Scenario 2 solar wind threshold raised from **400 to 450 km/s**. Fewer alerts on marginal nights, fewer operations.
- Both scenarios now also post to a public Telegram channel, in addition to the private group (see above).

**2026-10** — first public version

---

## Data sources

All public, no authentication, no API keys.

| Source | Endpoint | Used for |
| --- | --- | --- |
| Open-Meteo | `/v1/forecast` | `cloud_cover`, `cloud_cover_low` for 5 Lapland sites |
| NOAA SWPC | `/products/noaa-planetary-k-index-forecast.json` | 3-day Kp forecast |
| NOAA SWPC | `/products/summary/solar-wind-mag-field.json` | `bz_gsm`, `bt` (IMF, from DSCOVR) |
| NOAA SWPC | `/products/summary/solar-wind-speed.json` | `proton_speed` |

Monitored locations: Abisko, Kiruna (SE), Saariselkä, Levi, Rovaniemi (FI).

---

## Setup

1. **Import** a blueprint: Make → *Create a new scenario* → ⋯ menu → *Import Blueprint* → pick a file from `blueprints/`.
2. **Telegram connection.** Create a bot via [@BotFather](https://t.me/botfather), then open the Telegram module and add your own connection. The blueprints ship with no connection attached.
3. **Chat IDs.** Each scenario ends with two Telegram modules.
   - **Group or private chat** — replace `YOUR_TELEGRAM_CHAT_ID` in the first one. Add the bot, post a message, and read the id from `https://api.telegram.org/bot<TOKEN>/getUpdates` — group ids are negative.
   - **Public channel** — replace `@YOUR_PUBLIC_CHANNEL` in the second one with `@your_channel_name`, and add the bot to the channel as an administrator with permission to post. Don't need a channel? Delete the second module.
4. **Departure airport.** Replace `YOUR_AIRPORT` in the Telegram message of scenario 1 with your own IATA code (5 occurrences, inside the flight-search URLs).
5. **Locations.** Edit the `latitude` / `longitude` lists in the Open-Meteo URL of scenario 1. Order matters: `data[1]` is the first coordinate pair, `data[2]` the second, and so on. Keep the filter conditions and message mappings in sync. The destination codes (KRN, LLA, IVL, KTT, RVN) sit in the message text and must match.
6. **Thresholds.** See `docs/architecture.md` before changing them — several values look wrong but are not.

Notification texts are in Ukrainian. Scenario 2 renders roughly as:

```
🚨🌌 AURORA — GO OUTSIDE!
⏱ Starting in 30–60 minutes.

🚪 Door to the atmosphere: WIDE OPEN
(-12.4 nT — the deeper the minus, the better)
💨 Solar wind: fast
(521 km/s)
🔋 Reserve: medium
(11 nT)
```

The wording is produced by nested `if()` cascades that translate raw instrument readings into something readable at 2 a.m.

---

## What was removed before publishing

The blueprints in this repo are sanitised exports, not raw ones. Removed:

- the Telegram **chat ID** of the private group → `YOUR_TELEGRAM_CHAT_ID`, and the channel name → `@YOUR_PUBLIC_CHANNEL`
- the Make **connection ID** and its label (`parameters.__IMTCONN__` and `metadata.restore.parameters.__IMTCONN__`)
- cached **API response samples** under `metadata.designer.samples` — these held request timestamps and CDN trace headers
- account identifiers: team ID, scenario IDs, creator name and e-mail
- the **departure airport** in the flight-search links → `YOUR_AIRPORT`, so the blueprint works from any departure point

**No tokens were ever in these files.** Make stores bot tokens and OAuth credentials in the Connection object, which is never part of a blueprint export. Neither scenario sets or reads cookies (`shareCookies: false` throughout).

If you export your own blueprints, check the same four places before committing.

---

## Licence

MIT — see `LICENSE`.
