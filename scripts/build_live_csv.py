"""Builds data/live_scenario_runs.csv from the Make execution log
(transcribed: operations per 15-min run, UTC). 1 op = Bz filter stopped,
2 ops = speed filter stopped, 3 ops = Telegram alert sent."""
import csv, datetime as dt, pathlib

def block(start, ops):
    t = dt.datetime.fromisoformat(start)
    for o in ops:
        yield t, o
        t += dt.timedelta(minutes=15)

runs = []
runs += block("2026-10-21T01:15", [2,1,1,2,1,1,1,1,2,1,1,1])                     # -> 04:00
runs += block("2026-10-21T18:00", [3,1,1,1,1,3,1,1,3,3,3,3,3,3,1,3,1,1,1,3,1,1,1,1,
                                     1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1])          # -> 22.10 04:00
runs += block("2026-10-22T18:00", [3,3,3,3,1,1,3,3,1,1,3,3,1,3,3,3,1,1,1,1,1,1,1,1,
                                     1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1])          # -> 23.10 04:00
out = pathlib.Path(__file__).resolve().parent.parent / "data" / "live_scenario_runs.csv"
with out.open("w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["timestamp_utc", "operations", "outcome"])
    for t, o in runs:
        w.writerow([t.strftime("%Y-%m-%dT%H:%MZ"), o,
                    {1: "bz_not_south", 2: "wind_too_slow", 3: "alert_sent"}[o]])
print(len(runs), "runs ->", out)
