# Extend the daytime-fog window earlier to capture inland incursion fog

**Status:** open · **Priority:** high · **Created:** 2026-05-09 · **Builds on:** ticket 22 (daytime fog detection)

## Symptom

Several inland-incursion redwood sites get classified **not suitable** by the
current pipeline because their `fog_days` value is well below the 50-day
threshold, while coastal pixels a few km west pass easily. From the latest
`annotate_ground_truth_points.py` run:

| Site | Lat | Lon | fog_days | Suitable? |
|---|---|---|---|---|
| Russian River mouth (Pacific shore) | 38.45 | -123.13 | **102.2** | yes |
| Armstrong Redwoods (~20 km inland, Russian River valley) | 38.54 | -123.01 | **29.2** | **no** |
| Eureka coast | 40.80 | -124.16 | 109.5 | yes |
| Humboldt Redwoods (~60 km inland, Eel River valley) | 40.31 | -123.98 | **27.7** | **no** |
| Pepperwood Preserve (Sonoma, inland) | 38.57 | -122.71 | 43.8 | borderline |

Both failed sites are surrounded by mature *Sequoia sempervirens* old-growth
groves; both are widely cited canonical redwood habitat. The "fog hugs the
coast so tightly it stops at the river mouth" pattern visible in
`outputs/study_area_fog_days_daytime.tif` around the Russian River is the
specific tell.

## Root cause

We are sampling GOES-18 Ch2 at **17–21 UTC = 10 AM – 2 PM PDT**
(`scripts/18_download_daytime_goes18.py`, `DAYTIME_HOURS = [17, 18, 19, 20, 21]`).
That window starts **after** the morning marine layer has burnt off in
inland-incursion zones.

Torregrosa et al. 2016 (the GOES-W FLCC paper for our exact region) calls this
out explicitly in their Discussion (§4):

> "do not resolve clouds at night when the majority of the deepest FLCC inland
> incursion occurs (Figure 5c). At the inland edge of FLCC incursion, **FLCC
> often dissipates earlier than 10:30 A.M.** and is therefore not fully
> captured by MODIS or AVHRR."

Our 17 UTC start is 10:00 AM PDT — exactly the cutoff Torregrosa flags. We
have reproduced the MODIS sampling problem with GOES.

The geography lines up with the paper's own catalog of deep-incursion valleys
(§3.2.1, location numbers from their Fig. 2):

- Humboldt Redwoods sits in **Eel River valley**, listed by Torregrosa as
  "Humboldt Bay-Eel River (100 km, LN 1)" — the **longest inland incursion
  in the entire study area**.
- Armstrong Redwoods sits in **Russian River valley**, listed as
  "Petaluma Gap-Russian River (75 km, LN 4)".
- Their Figure 5c (Night Fraction FLCC) shows both valleys in the >0.55 band
  — i.e. the majority of fog hours at these pixels happen at night. By
  10 AM PDT a large fraction of those hours are gone.

Conversely, coastal pixels (Russian River mouth, Eureka shore) sit in the
afternoon-persistent regime — Torregrosa's Fig. 5a shows 7 AM-6 PM mean FLCC
of 9-14 h/d hugging the immediate coastline. Our window happens to fall
inside the part of the diurnal cycle where the coast stays cloudy and the
incursion zones are clear, which is why the suitability map currently looks
like a thin coastal ribbon plus disconnected high-elevation interior patches
rather than the canonical fog-belt shape.

## What we are NOT doing wrong

- The albedo threshold (0.25) and the OR-merge per day are mechanically fine.
  Sanity points behave as designed: Sacramento ≈ 0 fog days, Muir Woods ≈ 63.
- The 184-day extrapolation factor is correct.
- GOES-18 is the right satellite (Torregrosa specifically recommends GOES-W
  for our study area; r²=0.83 vs Monterey ceilings).
- The 50-day threshold (lowered from the original 80-day "fog past noon"
  station heuristic) was already a partial concession to this measurement
  bias and is well-tuned for what the *current* window measures.

The bug is the time window, not the algorithm.

## Proposed fix — add 15:00 and 16:00 UTC slots

Extend `DAYTIME_HOURS` from `[17, 18, 19, 20, 21]` to `[15, 16, 17, 18, 19, 20, 21]`
(8 AM – 2 PM PDT). Captures the morning hours when inland marine layer is
still in place but starting to retreat.

Why these hours specifically:

- **15 UTC = 8 AM PDT** is solidly past sunrise across our bbox / season
  (Eureka sunrise ranges from ~5:38 AM PDT at solstice to ~6:55 AM PDT at
  equinox), so we don't need the "skip first/last 30 min around sunrise"
  caveat from Rastogi 2016.
- **16 UTC = 9 AM PDT** is the midpoint of the dissipation window
  Torregrosa describes ("often dissipates earlier than 10:30 A.M.").
- We do **not** propose adding 13–14 UTC (6–7 AM PDT). At those hours,
  late-September solar zenith approaches the dawn-glare regime where Ch2
  reflectance gets noisy (low-sun surface inflation can mimic cloud).
  Worth revisiting only if 15–16 UTC alone doesn't fully recover the
  inland incursion zones.

This aligns with the Torregrosa paper's own definition of "daytime"
(15:00–23:00 + 00:00–03:00 UTC = 7 AM – 6 PM PDT) — they treat 7 AM
onward as daytime, and the morning hours carry real ecological signal in
their FLCC index.

### Ecological defense

The original station heuristic was "fog past noon ≥ 80 days/season,"
motivated by canopy interception during photosynthetically active hours.
Morning fog (8–10 AM PDT) still satisfies the spirit of that criterion:

- Photosynthesis is active by 8 AM in summer.
- Foliar uptake during morning fog hours is documented (Dawson 1998;
  Limm et al. 2009).
- Reduced morning evapotranspiration is a real water-budget benefit
  even when fog clears by noon.
- Drip from morning canopy interception is a real soil-moisture input.

The narrow "fog must persist past noon" framing is a station-instrument
artifact (a single observation per day at a fixed time), not the actual
ecological criterion.

### Data-acquisition cost

- 2 extra UTC hours × 7 days × 6 weeks × 3 years × 2 scans/hr = **504 new files**.
- Subset Ch2 files are ~700 KB each → ~0.35 GB additional disk.
- `scripts/18_download_daytime_goes18.py` already deduplicates against
  existing files, so re-running with the extended `DAYTIME_HOURS` list
  will only download the new (15, 16 UTC) slots — about 30 minutes of
  S3 traffic at the current 8-worker pool.

### Pipeline changes

1. `scripts/18_download_daytime_goes18.py` — `DAYTIME_HOURS = [15, 16, 17, 18, 19, 20, 21]`.
   Update the docstring header time-range comment.
2. `scripts/19_create_daytime_fog_layer.py` — no logical change; the
   aggregation step is hour-agnostic. Update the docstring "17–21 UTC"
   comment to "15–21 UTC (8 AM – 2 PM PDT)".
3. `scripts/suitability.py` — update the `FOG_DAYS_THRESHOLD` comment
   ("17–21 UTC" → "15–21 UTC"). The numeric threshold may need re-tuning
   after the layer is regenerated; see below.
4. Re-run the pipeline (`19_…` then `04_…`) and `annotate_ground_truth_points.py`.

### Threshold re-tuning

After the regen, expect:

- **Coastal pixels barely change** — they're already cloudy through the
  afternoon, OR-merging earlier hours doesn't add new fog-days.
- **Inland-incursion pixels rise sharply** — Armstrong Redwoods, Humboldt
  Redwoods, Pepperwood should all gain 20–60 fog days based on
  Torregrosa's diurnal numbers (Fig. 6c shows Pepperwood at ~3 h/d
  daytime average over 7 AM-6 PM; the morning fraction roughly doubles
  the count vs. midday-only sampling).
- The 50-day threshold may end up too lenient relative to negative
  controls (Sacramento, Mineral). Re-tune against ground truth + ticket 29
  negatives before declaring done. The principled move is to fit the
  threshold once we have both positive and negative anchors (see
  ticket 30 — weighted suitability rule).

## Validation plan

A. **Ground-truth points.** All 12 currently-classified positives should
   stay positive; the 5 currently-failing positives (Armstrong, Humboldt,
   Grove of Old Trees, Navarro River, Limekiln) should pass. Limekiln is a
   special case (south-of-bbox heat ceiling and tmin issues — not purely a
   fog-window problem); the other four are direct tests.

B. **Spatial sanity.** Visual diff of the new vs. old
   `study_area_fog_days_daytime.tif`. Expected: smooth gradient inland from
   the coast in the Russian River, Eel River, Mendocino, and Pajaro
   incursion valleys, instead of the current cliff-edge-at-river-mouth
   pattern. The cliff is the bug.

C. **Negative controls (ticket 29 prerequisites).** Sacramento and Modesto
   should not move materially — they're outside the marine fog regime
   regardless of hour. If they jump significantly, the morning window has
   introduced non-marine-cloud false positives (e.g. early-morning
   high-cumulus over the Central Valley) and we need to investigate
   before re-tuning the threshold.

D. **Cross-check against Torregrosa Fig. 5a.** Their decadal mean
   7 AM-6 PM FLCC h/d map is the closest published analog to what our
   layer should look like. Locations they call out as 9-10 h/d
   (Humboldt-Eel River valleys, Russian River valley) should land in the
   "passes 50 fog-days" zone after the fix.

## Risks / things that could go wrong

- **Solar zenith angle at 15 UTC in late September.** At 41.95°N, DOY 266
  (Sep 23), 15 UTC is ~7 AM PDT solar time, with sun ~10° above the
  horizon. CMI is calibrated reflectance, but at very low elevation
  angles Ch2 over bright surfaces (dry grass, bare soil) can creep up
  toward 0.25. Mitigation: spot-check a few clear-sky inland pixels in
  late-Sep 15 UTC scenes; if needed, drop 15 UTC for September only or
  raise the threshold slightly for that hour.
- **High-cumulus contamination.** Summer convection over the Trinity Alps
  and the Sierra (just inside our eastern bbox) can produce afternoon
  cumulus with albedo > 0.25; that's already in the current layer but
  morning slots will catch additional cumulus development. The ticket-29
  negatives (Mineral / Lassen vicinity) are the right test.
- **Marine-layer ≠ fog-touching-canopy.** The fundamental "satellite sees
  cloud tops, not cloud bases" gap from ticket 29 is unchanged. This fix
  reduces a different bias (time-of-day sampling) but does not address
  the cloud-base-altitude gap.

## Out of scope

- A full Option C (Torregrosa month-hour matched IR algorithm). That's
  still the principled long-term fix and is documented in ticket 22; this
  ticket buys most of the value with a one-line config change and
  ~500 extra files.
- Adding **nighttime** fog detection back in. The original v0 used
  nighttime BTD (Ch13 − Ch7); merging it would address the same
  geography from a different angle but adds a separate algorithm path
  and the existing nighttime layer was retired for known reasons.
  Defer; revisit only if the morning-extension fix is insufficient.
- Re-fitting `FOG_DAYS_THRESHOLD` as part of this ticket. Threshold
  selection should follow ticket 29 (negatives) + ticket 30 (weighted
  rule) so we tune once with both anchors available, not twice.

## References

- Torregrosa et al. 2016, *Earth and Space Science* (in repo root):
  Fig. 5a/c (mean daytime FLCC + night fraction), §3.2.1 (catalog of
  inland-incursion valleys), §4 Discussion ("FLCC often dissipates
  earlier than 10:30 A.M.").
- Ticket 22 — original daytime-fog design doc; this ticket is a follow-up.
- Ticket 29 — negative control points; needed to tune the threshold
  honestly after the regen.
- Ticket 30 — weighted suitability rule; the right place to do final
  threshold/coefficient tuning once both positives and negatives are
  in place.
