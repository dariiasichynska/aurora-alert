# Design notes

Why the values are what they are. Several of them look like mistakes and are not.

## Deliberate values — do not "fix"

**`Bz < -3`, not `-5`.** The alert threshold is tuned for sites under the auroral oval (Rovaniemi sits at 66.5° N), where weaker southward field is already enough. At mid-latitudes `-5` or lower would be the right number.

**The second condition `Bz > -100`.** NOAA returns `-999` as a fill value when the satellite feed drops out. Without this guard a data outage reads as an extreme storm and fires a false alarm at 3 a.m. Keep it.

**`cloud_cover_low`, not `cloud_cover`.** Aurora emits above 100 km, higher than any cloud. Thin cirrus dims it but does not hide it. Filtering on total cloud cover discarded usable nights; filtering on the low layer does not.

**Index `[71]` in the Open-Meteo arrays.** Open-Meteo returns hourly arrays starting at 00:00 local time today. Day after tomorrow at 22:00 is therefore `48 + 22 + 1 = 71` — the `+1` because Make indexes arrays from 1, not 0.

**Index `[80]` in the Kp forecast.** NOAA ships a rolling window of ~7 days observed plus 3 days predicted, in 3-hour steps. Element 80 lands on the day after tomorrow at 21:00 UTC. Verified against `time_tag`; re-check that field if NOAA ever changes the archive depth, because the index would shift silently.

**Threshold `Kp ≥ 3.67`.** Kp is measured in thirds. A threshold of `4` would exclude `3.67`, which is a perfectly good night under the oval. "About 4" means 3.67.

**Time window instead of self-deactivation.** The Make API can stop a scenario programmatically, but runs outside a schedule window cost zero operations anyway. Same outcome, less machinery, no API token needed at runtime.

## Why Bz and not just Kp

Most aurora tutorials filter on the Kp index alone. Kp is computed after the fact, with up to three hours of lag — it tells you what already happened.

Bz, the north–south component of the interplanetary magnetic field, is measured by DSCOVR at the L1 point. When Bz turns southward, it reconnects with Earth's northward field and opens a path for solar wind energy. It gives 20–40 minutes of warning.

That lead time is also the reason for two scenarios: 40 minutes is useless for booking a flight, and a 2-day forecast is useless for deciding whether to put a coat on.

## Debugging note

During a G3 storm the alert scenario stayed silent. The investigation ran in three steps, and the order matters:

1. **Execution History** — every run consumed exactly one operation. So the filter was stopping the chain correctly and nothing had crashed.
2. **Filter Inspector** — it shows each condition separately: `Bz < -5` not met, `Bz > -100` met. So the data was valid, just not negative enough.
3. **Source data** — NOAA's alert feed put the storm peak at 21:27. The scenario had been switched on at 22:35. The field had already turned northward.

The system had been correct. Two initial hypotheses — broken filter, stale source data — were both wrong.

The reusable part: *one operation per run* is itself a diagnostic. It distinguishes "filter working" from "scenario broken" before you look at any values.

## Known gotcha: API writes clear the sample cache

Overwriting a blueprint through the Make REST API drops the stored data samples under `metadata.designer.samples`. The scenarios keep running, but the mapping tree in the editor shows empty. Fix: click **Run once**, which repopulates the structure.
