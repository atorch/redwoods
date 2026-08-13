# Northern range limit — what should stop the suitability area at/near the OR border?

**Status:** open · **Priority:** medium · **Created:** 2026-05-17 · **Related:** ticket 32 (temperature constraints), ticket 22 / 33 / 34 (fog), ticket 05 (geographic extent)

## Why this ticket exists

Our current map's suitability area ends in a horizontal east-west line right
around the CA-Oregon border. That edge is **an artifact of the bbox**
(`outputs/study_area_bbox.json` has `max_lat = 42.089`, derived from
ground-truth points + a 0.3° margin in `01_process_study_area_rainfall.py`),
not anything the rule itself is doing.

The question this ticket investigates: if we extended the bbox into Oregon
or Washington, **would our rule correctly stop classifying the coast as
suitable**, and if not, what variable should make it stop?

## What the documented native range actually does

Coast redwood's native range extends *slightly* into Oregon — into the Chetco
River drainage near Brookings (~42.0–42.05°N). The Wikipedia and parks.ca.gov
maps cut off at the state line for political reasons; the biological edge is
~10 km inside Oregon. So our current map showing Brookings as suitable is
not wrong — it's approximately the documented range edge. The bbox happens
to clip at almost exactly the right place, but only by coincidence.

What stops redwoods from extending further north (per the Silvics manual and
the Save the Redwoods League literature):

1. **Summer fog / low-cloud frequency drops sharply north of Cape Blanco
   (~42.85°N).** The California Current's strongest coastal upwelling sits off
   central/northern CA; SSTs warm to the north, the marine inversion weakens,
   and summer stratus thins. Coast redwood depends on fog drip and
   fog-suppressed VPD during the dry season; without it, summer water stress
   wins.
2. **Extreme winter freezes.** Even when *mean* tmin is mild on the coast,
   the Oregon coast sees occasional Arctic outbreaks reaching −10 to −15 °C
   (1972, 1989, 1990, 2008). Silvics: "rarely below −9 °C." Single events
   can kill redwoods or kill the seedlings/young trees that close range edges.
3. **Wet summers favor competitors.** Coastal OR/WA gets meaningful
   Jun–Aug precipitation; coastal CA almost none. Sitka spruce, western
   hemlock, and Douglas fir are better-adapted to that wet-summer niche
   and outcompete redwood at germination/sapling stages. This is a biotic
   constraint our rule can't directly represent.
4. **Pleistocene refugium / dispersal limitation.** Coast redwood is a
   relictual species. Some studies argue climate would support it further
   north (parts of WA), but it hasn't recolonized since the Pleistocene
   because seed dispersal is short-distance.

## What our current rule would do if we extended the bbox

Estimated for typical OR/WA coastal pixels (anywhere from Brookings to the
mouth of the Columbia):

| variable | binds? | notes |
| --- | --- | --- |
| rainfall ≥ 20" wet-season | no | OR/WA coast is wetter than CA |
| coldest tmin ≥ −3 °C | no, mostly | Coastal OR/WA mean January tmin is typically 0–4 °C — well above the floor |
| hottest tmax ≤ 30 °C | no | Coast stays cool |
| land mask | works | CDL is national |
| **fog-nights ≥ 50** | **maybe** | Empirical question — depends on whether the GOES-16 nighttime BTD signal weakens north of Cape Blanco. Literature says yes; need to compute on extended bbox to verify. |

The fog variable is the only one of ours that has the right *shape* to
match the real-world boundary. Mean tmin doesn't bind because it's a mean,
not the cold tail.

## Why "just bump the tmin floor" is a fudge, not a fix

PRISM 30-yr normals deliver *means* (mean of daily minimums in the coldest
month, averaged across 30 years). Mean January tmin of +1 °C on the
Oregon coast can coexist with a once-per-decade Arctic outbreak hitting
−12 to −15 °C — which is what actually kills redwoods. Pushing our
floor from −3 to 0 or +1 °C would cosmetically exclude Oregon but at the
cost of:

- false negatives in interior Mendocino / Sonoma sites where mean tmin
  is similar but extreme outbreaks don't happen;
- a rule that pretends to be biology when it's actually a latitude
  proxy by another name.

The honest fix is to ask a different variable — one that captures the
**left tail** of the temperature distribution, not the mean.

## Candidate variables for the "extreme cold" axis

Ranked by how much new infrastructure they require.

### Option A — USDA Plant Hardiness Zone Map (PHZM) raster *(recommended)*

USDA's PHZM 2023 release is a published 800 m raster of the
**average annual extreme minimum temperature** for 1991–2020, derived from
PRISM daily data. This is exactly the statistic we want.

- **Source:** https://prism.oregonstate.edu/projects/plant_hardiness_zones.php
  (PRISM Climate Group, who produce it for USDA). Distributed as a GeoTIFF;
  CONUS coverage; same 800 m grid as our other PRISM normals so no
  resampling distortion.
- **Unit:** °F (continuous), with a companion binned zone raster (5 °F bins:
  Zone 7a, 7b, …).
- **Why this is the right statistic:** For each year in 1991–2020, take the
  single coldest daily-minimum temperature; average those 30 yearly extremes.
  That's a much better proxy for "do hard freezes happen here?" than mean
  monthly tmin. It still smooths over the worst event in any given decade,
  but moves the constraint from "mean of monthly means" to "mean of yearly
  extremes" — closer to the biology.
- **Thresholds, sketched:** Native coast redwood range sits in USDA Zones
  9a–10b (avg annual extreme min ≈ −7 to +4 °C / 20 to 40 °F).
  Northernmost native groves (Chetco / Crescent City area) are Zone 9a
  (~−7 to −4 °C). Coastal OR north of Cape Blanco is Zone 9a–9b — not
  cleanly excluded by hardiness alone. Coastal WA tilts toward Zone 8b.
  Inland OR cold pockets drop into Zone 7. So a threshold of
  "avg annual extreme min ≥ −7 °C" rejects interior cold pockets cleanly
  but admits much of the coastal Pacific Northwest — same shape as our
  current mean-tmin floor, but in the right *units*.
- **Effort:** small. One raster download + reproject/resample to the
  study grid; the existing `build_temperature_masks.py` is a near-clone
  template (it's the same shape — PRISM raster → reproject to study grid
  → threshold → AND into `combine()`).
- **Caveat:** PHZM is the *mean of* annual extremes, not the worst-case
  event. A site can have an avg annual extreme min of −5 °C and still
  see −15 °C in a bad year. For our v0/v1 this is still a strong upgrade.

### Option B — DAYMET-derived extreme statistics *(DIY heavier alternative)*

DAYMET v4 publishes daily tmin/tmax for North America at 1 km, 1980–present.
We could download a 30-year tmin archive and compute, per pixel:

- mean annual extreme min (same as PHZM, sanity check)
- count of days per year below 0 °C (frost days)
- count of days per year below −9 °C (the Silvics threshold itself)
- minimum daily tmin over the whole archive (worst-case event)

Most flexible, by far the most work and storage (tens of GB), and not
necessary for a v1 — pick this only if PHZM proves too smoothed.

### Option C — WorldClim bio variables *(weaker, but trivial)*

WorldClim has bio6 = "Min Temperature of Coldest Month." This is the
single coldest *monthly mean tmin* across the 12 months — same shape as
what we already compute from PRISM, just on a different grid. Not an
upgrade over what we have.

### What about "weekly temperature normals"?

PRISM does not publish weekly normals as a standard product. The
relevant aggregations they do publish are:

- monthly normals (what we use today)
- annual normals
- daily data (1981–present, ~few hundred GB for a 30-yr coastal subset)

So the practical answer to "is there something finer than monthly that
captures cold tails" is **either PHZM (one statistic, off-the-shelf) or
derive from daily data ourselves (DAYMET / PRISM daily).** PHZM is the
right starting point.

## Recommendation

Treat the northern limit as **multifactorial**, and own the framing in the
about page:

> "Our heuristic asks 'where could redwoods grow today, climate alone?'
> By that criterion, suitable habitat extends modestly past the documented
> range edge in southern Oregon. Coast redwoods don't occupy that area in
> the wild — partly because the marine fog regime weakens as you move
> north, partly because occasional severe winter freezes there exceed what
> redwood seedlings tolerate, partly because faster-growing species
> (Sitka spruce, western hemlock) already hold the niche. Our suitability
> shows where redwoods *could* persist if those competing forests were
> cleared and given time to recolonize — not where they're growing today."

Concretely:

1. **Add PHZM (Option A) as a 5th rule variable.** Threshold somewhere
   in the −7 to −5 °C range — to be set by sampling at our ground-truth
   points the same way `annotate_ground_truth_points.py` samples the
   others. Native positives should all sit at avg annual extreme min
   ≥ −7 °C with margin; cold-interior negatives (Mt Shasta, Weaverville)
   should fall below. Use the existing `combine()` plumbing.
2. **Extend the bbox** north into Oregon (44°N as a first cut, covering
   most of the Oregon coast through Florence/Newport; or 46°N to reach
   the WA border) once PHZM is wired in. Verify the rule's behavior
   matches expectations on the larger frame.
3. **Update the about page** with the framing above — and link to the
   Silvics manual + the Save the Redwoods League page on range.

## Out of scope for this ticket

- A latitude cap (e.g., "max_lat = 42.2"). Ad hoc, hides the multivariate
  story we want the map to tell.
- Biotic competition modeling (Sitka spruce / western hemlock / Doug-fir
  distributions). Important biology but enormous scope.
- Climate-change projections — this ticket is about current envelope.

## Progress (2026-08-11/12)

Did the recommended steps, in order:

1. **Added PHZM as a 5th rule variable** (`scripts/build_phzm_mask.py`,
   `suitability.combine`). Initial floor: -7 C, the "9a-10b hardiness-zone
   edge" estimate from the original writeup above.
2. **Extended the bbox to 44.0 N** (`scripts/01_process_study_area_rainfall.py`,
   `NORTH_BBOX_OVERRIDE_LAT`) — the "first cut" this doc recommended, roughly
   the OR coast through Florence. Reran the full pipeline (rain, fog, land,
   temp, PHZM all regenerate cleanly on the larger frame — PRISM, CDL, and
   our GOES-16 CONUS-sector downloads already covered the extended area, no
   new downloads needed).
3. **Result: did not end gracefully.** At -7 C, suitable habitat extended
   to the new bbox edge, ballooned up to ~1.8 deg of longitude inland near
   Eugene (vs. ~0.5 deg at the CA/OR border), and was visibly speckled/
   fragmented. Root cause, confirmed by masking each of the 5 criteria
   separately over 41.9-44.0 N: **rain and fog both saturate to 90-100%
   pass north of the border** — they stop discriminating anything, including
   ~40 mi inland where marine fog has no physical mechanism to reach. PHZM
   was the only criterion still doing real work, so the combined layer was
   effectively just PHZM's own noisy threshold zone. The fog finding is
   split out to ticket 37 rather than fixed here, since it's a materially
   different, larger problem (the detector itself, not just the range edge).
4. **Added two negative controls specifically to probe this**: Kloster
   Mountain, OR (43.867 N, inland) and Siuslaw National Forest, OR
   (44.413 N — turned out to sit just past the 44.0 N bbox edge, so it's
   untested, not "correctly rejected"; leaving it in `negative_points.csv`
   for whenever the bbox extends further). Both chosen because they are well
   outside the documented native range (42 09'N, Chetco River, per the USDA
   Silvics Manual) on first-principles grounds, not "historically logged."
5. **At -7 C, Kloster Mountain was a false positive** (passed all 5
   criteria; PHZM -6.5 C). Swept the PHZM floor against all 20 evaluable
   ground-truth + negative-control points
   (`scripts/annotate_ground_truth_points.py` output, rain/fog/temp held as
   measured): every point classifies correctly for any floor in
   (-6.5, -3.83] — that gap is bounded by Kloster (the coldest point that
   must fail) and Humboldt Redwoods (-3.83 C, the coldest point that must
   pass). **Set `PHZM_EXTREME_MIN_FLOOR_C = -5.0`**, roughly centered in
   that gap. Result: PHZM pass rate near Eugene dropped from ~33% to ~9%,
   comparable to the CA/OR border's own rate (~10%), and the suitable area
   pulled back to a narrow coastal ribbon — no more inland ballooning.

**Still open:** the coastal ribbon persists in a thin strip past 44 N rather
than clearly terminating — consistent with this doc's original framing that
the edge is genuinely gradual/multifactorial, not a hard line. Revisit
alongside ticket 37 (fog robustness) and once more OR ground-truth points
exist. -5.0 C is a defensible pick given current data, not a settled
constant — it was chosen from a 20-point gap, which is thin evidence for a
region-wide threshold.
