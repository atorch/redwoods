# Elevation / high-terrain mask

**Status:** open · **Priority:** medium · **Created:** 2026-05-05

## Why

The 2-variable POC fit (`scripts/fit_suitability_rule.py`) put **Mount Shasta as the highest-scoring pixel in the entire dataset** — 94" "rainfall" and 133 "fog days" — even though Shasta is a 4,300 m volcano with no redwoods. Both inputs are misleading at high elevation:

- PRISM "rainfall" includes **snow water equivalent**, so the Cascade and Trinity high country comes in wetter than the coast.
- The GOES-18 Ch2 albedo > 0.25 fog detector can't tell **snow on alpine peaks** or **summer cumulus over high terrain** from marine stratus. Both look like bright cloud from space.

A coast redwood's native elevation ceiling is around 800–1000 m (per the USDA SRS fact sheet and conifers.org; redwoods are coastal-fog-belt trees, not subalpine). So a simple terrain filter that masks pixels above ~1000 m removes Mt Shasta, the Trinity Alps interior, and the high Klamath Range — which is exactly the Shasta-Trinity false-positive zone visible on the current map.

Conceptually this is the same shape as the water mask we already have (`scripts/17_build_land_mask.py` + `outputs/study_area_land_mask.tif`): one binary raster on the study grid, AND-ed into the suitability rule.

## What to build

1. **Download a DEM** covering the study bbox. Options:
   - USGS 3DEP 1 arc-second (~30 m) via the [National Map downloader](https://apps.nationalmap.gov/downloader/) — authoritative US source.
   - NASADEM / SRTM 30 m via OpenTopography (`https://opentopography.org`) — easy programmatic download.
   - Either is fine — we resample to the 800 m PRISM grid anyway.
   - Stash the raw DEM under `data/dem/` (gitignore — same as PRISM and CDL).
2. **New script** `scripts/build_elevation_mask.py`, modeled directly on `17_build_land_mask.py`:
   - Reproject + resample DEM onto the PRISM template grid (same as `study_area_rainfall_20in.tif`).
   - Use **mean** resampling (continuous variable, not categorical).
   - Threshold: `elevation < 1000 m ⇒ keep (1); elevation ≥ 1000 m ⇒ exclude (0)`.
   - Output `outputs/study_area_elevation_mask.tif` (uint8, 1 = below threshold, 0 = above).
3. **Wire into the rule.** Extend `scripts/suitability.py`'s `combine()` to take a fourth mask (`is_below_elevation`) and AND it in. Update `scripts/04_combine_suitability.py` to load and pass it. Same plumbing as the land mask.
4. **Update `web/about.html`** to mention the constraint: "places above ~1000 m are excluded — coast redwoods are a coastal-fog-belt species and don't grow at subalpine elevations."

## Threshold choice

Start at **1000 m**. Comfortably above the highest known redwood groves (Big Sur Santa Lucia Range tops at ~1500 m but redwoods are in the canyons below ~700 m; some Mendocino sites at ~900 m). Below the elevations where snow albedo and orographic cumulus regularly bias both PRISM and GOES-18.

If Mt Shasta or the Trinity Alps still leak through after the mask is applied, drop to 800 m and inspect. If we lose any positive ground truth point, raise the threshold or move the floor to a different mask. Run `scripts/annotate_ground_truth_points.py` after wiring this in to confirm no positives get newly excluded.

## Success criteria

- Mt Shasta and Trinity Alps high country come out gray (excluded) on the suitability map.
- All 12 ground truth positives remain in-bounds (`is_suitable` unchanged for them).
- The Shasta-Trinity artifact area you flagged earlier is visibly reduced.

## Out of scope

- Per-pixel snow detection from satellite (ABI Ch5 1.6 µm, etc.). Elevation is a much simpler proxy and addresses the same bias. Reconsider only if the elevation mask doesn't catch the problem.
- Aspect / slope filtering (e.g. excluding north-facing high-elevation slopes). Defer until elevation alone is shown insufficient.
- Replacing PRISM with a snow-corrected precipitation product. Same logic — elevation mask is the cheap fix.
