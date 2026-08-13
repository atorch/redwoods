# Negative control points: expose false positives in the suitability model

**Status:** open · **Priority:** medium · **Created:** 2026-05-04 · **Last updated:** 2026-05-05 · **Unblocks:** ticket 30 (weighted suitability rule)

## Why this matters

Validation is currently one-sided. Every entry in `web/ground_truth_points.csv` is a place we *expect* the model to call suitable, and we've tuned thresholds (the albedo cutoff in `scripts/19_create_daytime_fog_layer.py` and the fog-day count in `scripts/suitability.py`) until those points pass. We have no points where the model is supposed to say "not suitable" — so we have no way to measure false-positive rate, and the validation argument is partly circular.

A second concern that motivates this ticket: satellite cloud detection is a proxy for a proxy. The albedo-threshold algorithm detects *"there is a sufficiently bright cloud somewhere in the column above this pixel during the late-morning-to-early-afternoon window"* — it does **not** detect "fog touching the canopy." A pixel with marine stratus floating 1500 m above ground produces the same albedo signature as fog actually wetting trees at 200–400 m canopy height. Coastal redwoods depend on **canopy interception** — droplets condensing on needles and dripping to the root zone (Dawson 1998; up to ~45% of summer water comes from fog drip). Our model is silent on whether the cloud it sees is interacting with the canopy at all.

Negative controls won't fix that gap, but they're how we'd notice if the gap is hurting us: if Sacramento or Mt Lassen come out green, we know the model is firing on something that isn't redwood-relevant fog (e.g. high-terrain summer cumulus over the Trinity Alps, or bright dry surfaces tripping the albedo threshold).

Adding negatives is also the **prerequisite for ticket 30** (weighted half-plane rule). We can't fit a calibrated linear separator from positives alone — the dry-interior side of the boundary is unconstrained without "no" points to anchor it.

## Proposed control points

All four below have been confirmed as **outside the native range of *Sequoia sempervirens*** in pre-contact / 1700s conditions per the USDA Southern Research Station fact sheet, Wikipedia, and conifers.org. The native range is a 5–47 mi-wide coastal fog belt; the Central Valley interior, Sierra, and Cascades were never coast-redwood habitat.

| Point | Lat | Lon | Why |
|---|---|---|---|
| Sacramento | 38.58 | -121.49 | Sacramento Valley floor; well east of fog belt |
| Modesto | 37.64 | -120.99 | Central Valley; tests inland gradient |
| Bakersfield | 35.37 | -119.02 | Southern Central Valley; south of the San Simeon redwood limit AND inland — *currently outside study bbox, would need bbox expansion or just a hard "outside study area" check* |
| Mineral / Lassen vicinity | 40.35 | -121.59 | Cascade Range, ~1500 m elevation; tests "high inland" failure mode |

Sacramento, Modesto, and Mineral are inside the current study bbox (35.71–42.09 N, -124.38 to -121.22 W) so they'd land directly on the suitability raster. Bakersfield is east and south of the bbox; either expand the bbox eastward or treat that one as a check that the bbox excludes it correctly.

(Note: these are obvious controls. A subtler set would include points along the *inland edge* of the marine layer — Cloverdale, Hopland, parts of Lake County — to test where the model draws its eastern boundary. Defer to a follow-up if the obvious controls all pass.)

## What to build

1. Add `web/negative_control_points.csv` with the same schema as `ground_truth_points.csv` (`latitude,longitude,notes`).
2. In `scripts/04_combine_suitability.py`, add a second validation pass over the negative CSV that **asserts the model returns 0 (not suitable)** at each point. Print a clear pass/fail summary.
3. **Do not surface these on the web map.** Keep them validation-only — part of the repo and the pipeline, not user-facing. The separate CSV (rather than reusing `ground_truth_points.csv`) makes this trivial: `web/index.html` only fetches `ground_truth_points.csv`, so as long as `negative_control_points.csv` is its own file, nothing in the front-end touches it.
4. Update `README.md` validation section (currently one-sided) to describe both positive and negative validation.

## Success criteria

- All 4 negative points return "not suitable" in `04_combine_suitability.py`.
- If any return "suitable," that's a real signal — investigate before suppressing. Likely culprits in the current daytime-albedo pipeline: albedo threshold too low (bright dry surfaces classified as cloud), afternoon cumulus over high terrain (e.g. Trinity Alps in July) classified as marine stratus, or fog-layer nearest-neighbor interpolation bleeding inland from coastal pixels.

## Out of scope (related, deferred)

- Fixing the canopy-interception gap directly — that needs cloud-top altitude or boundary-layer height data; daytime persistence is partly addressed by ticket 22 but cloud-top altitude warrants its own ticket as the model matures.
- A formal confusion matrix with hundreds of points. The 4 controls above are a sanity check, not a statistical evaluation.
- Re-shaping the suitability rule itself (box → half-plane). Tracked in ticket 30; depends on this one.

## References

- Dawson 1998, *Fog in the California redwood forest: ecosystem inputs and use by plants*
- USDA SRS, *Sequoia sempervirens* fact sheet — native range
- Wikipedia, *Sequoia sempervirens* — geographic range
