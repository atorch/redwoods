# Daytime fog detection — measure "fog past noon" directly

> **Status:** TODO — design firmed up against Torregrosa et al. 2016 (GOES-W fog/low-cloud climatology for coastal CA) and Rastogi et al. 2016 (GOES albedo fog detection for the Channel Islands). **Priority:** high (the v0 nighttime-only signal isn't measuring the ecological criterion).

## Problem

The original heuristic is **"fog past noon ≥ 80 days/season."** Our v0 instead measures *nighttime* low-cloud frequency (06–12 UTC = 11pm–5am PST) using BTD (Ch13 − Ch7). We do this because Ch7 (3.9 µm) is contaminated by solar reflection during the day — a single fixed BTD threshold does not work in daylight.

The ecological gap: marine layer commonly forms after sunset and burns off by mid-morning. A pixel that has nighttime fog at 4am but clears by 8am gives the trees no daytime canopy interception during photosynthetically-active hours — yet our v0 counts it as a "fog day." The Dawson / Johnstone work on canopy interception is about *daytime* fog persistence; that's what we should be measuring.

Note: Torregrosa et al. 2016 shows that for the CA coast, *daytime* FLCC hours/day are actually **higher** than nighttime over the ocean and most coastal land (their Fig. 5/6c). Inland incursion zones tilt nighttime, but the ecologically relevant "in the fog belt during PAR hours" signal is well-resolved at noon-window sampling.

## Recommended scope changes vs. earlier draft

After reading the two CA-specific papers we should change three things:

1. **Switch to GOES-18, not later — now.** Torregrosa et al. used GOES-W (the predecessor to GOES-18) for exactly our study area and found r²=0.83 against airport fog ceilings at Monterey. CA sits at ≈60° satellite zenith from GOES-16; visible-channel and spatial-homogeneity tests both degrade with view angle. Doing the v1 daytime work on GOES-16 means we'd validate against a known-handicapped sensor and migrate later anyway.
2. **Start with a visible-only baseline (Rastogi 2016), not a full multi-test classifier.** Rastogi gets r²=0.74–0.75 against ground insolation using a single threshold (albedo > 0.3) on the 0.65 µm channel, no IR. That's our simplest viable v1 — and it's the one validated for our use case. Add IR tests only if the visible-only output has visible failure modes.
3. **Subset on download.** Full CONUS CMIPC files at 0.5 km (Ch2) are ~50 MB each; our bbox is ~5% of CONUS. Cropping during download reduces per-file size by ~20×, which is what makes a 4-channel daytime archive fit on this disk at all (see "Storage budget" below).

## Time period: 2023–2025

GOES-18 became operational GOES-West on **2023-01-04** (NESDIS announcement). Earlier years would require GOES-17, which had a known loop-heat-pipe anomaly that degraded its IR channels especially during eclipse seasons (Aug–Sep — exactly our window). Ch2 visible was unaffected, so a GOES-17+18 stitch would technically work for Option A — but the simplicity win of staying single-satellite is large.

**Recommend: use dry seasons 2023, 2024, 2025 — three full May–Oct windows.** As of 2026-05-04 the current dry season has just begun; we can't include it as a complete season. Three years is fewer than the 5-year multi-year design in `16_download_multiyear_goes16.py`, but Torregrosa's interannual CV in our coastal target zones is < 0.10 (their Fig. 4b), so 3 years is enough to characterize the climatology for v1. Add 2026 once it completes in October.

## Time window

**19:00–22:00 UTC** (≈ 12:00–15:00 PDT during May–Oct). Slight widening from the earlier 19:00–21:00 proposal to align with Rastogi's "afternoon" window (12:00–15:30 PST = 19:00–22:30 UTC during PDT). Still solidly past morning burn-off; ends before the late-afternoon onshore push.

- GOES CONUS scans run every 5 min, so 3 hours = ~36 scans/day. At our existing 2-scans-per-hour cadence (≈30 min between samples) that's 6 scans/day — enough to denoise against missing scans and brief sun glints, and a "fog day" is a day where any scan in the window classifies as low cloud.
- Timezone trap: GOES filenames are UTC. CA observes PDT (UTC−7) from mid-March through early November. May–Oct is fully PDT. Pick UTC slots directly and document the implied local-time window; don't round-trip through `pytz`.

## Algorithm options

Three options, in order of increasing complexity. Default to **Option A** for v1.

### Option A — Visible-only albedo threshold (Rastogi 2016)

Single test on GOES-18 ABI Channel 2 (0.64 µm visible):

1. Convert Ch2 reflectance to albedo using NESDIS pre/post-launch calibration coefficients.
2. Threshold: **albedo > 0.30** ⇒ cloud. (Rastogi used 0.3 from ISCCP; not sensitive to seasonal solar geometry per their ECDF analysis.)
3. Skip the first/last 30 min around sunrise/sunset to avoid extreme solar-zenith albedo inflation. (Not actually a constraint inside our 12–15 PDT window — flagging for completeness.)
4. Aggregate: a "daytime fog day" = any in-window scan exceeds threshold.

**Why this is enough:** Coastal CA summer clouds are nearly exclusively low marine stratus (Iacobellis & Cayan 2013, cited by Rastogi); high cirrus is <2% of the bbox by hours/day. So we don't actually need the cloud-top temperature filter that papers in mixed-cloud regimes need.

**Why we don't need to worry about non-marine fog types**: the only ecologically relevant signal for redwoods is *marine* stratus touching coastal canopy. The other dry-season cloud/aerosol types over our bbox are either out of season or land far from redwood-suitable terrain:
- **Tule fog** is a winter (Nov–Mar) Central Valley radiation-fog phenomenon. Our May–Oct window won't see it.
- **Wildfire smoke** (Aug–Oct) is the real residual contaminant — thick smoke can have albedo > 0.3 and would mimic fog over inland pixels. Coastal marine air mass is mostly insulated, but the layer should be inspected against CALFIRE perimeters as a sanity check; consider masking heavy-smoke-day pixels in v1.5 if needed.
- **High cirrus** is <2% bbox-hours per Torregrosa, denser at the OR border. Option B's BT > 270 K filter handles it if it shows up.
- **Marine intrusion through Carquinez** into the Delta is *true* marine fog reaching inland — a true positive, not a contaminant.

**Pros:** one channel, simplest pipeline, validated against ground insolation in our exact climate regime. **Cons:** doesn't discriminate occasional summer high cloud (small effect for CA, larger if we extend N into Oregon — bbox edge case worth checking against the layer once produced); no smoke discrimination.

### Option B — Add a warm-cloud-top filter (Rastogi + Ch13)

If visible-only mis-classifies high cloud as fog (we'll see this in the layer):

5. Add Ch13 (10.3 µm long-wave IR) test: keep classification only where brightness temperature > **270 K** (Mahdavi et al. 2020 threshold). High cirrus has cold tops and gets dropped.

Two channels, ~2× IR storage but trivial compared to Ch2.

### Option C — Month-hour matched IR differencing (Torregrosa / Jedlovec & Laws 2003)

The most rigorous option and the one that *could* unify day and night under one pipeline. Per-pixel, per-month-hour, build clear-sky baselines from a multi-year archive:

- LND = largest negative (Ch13 − Ch7) difference seen at this pixel/month-hour
- SPD = smallest positive difference
- WTV = warmest Ch13 brightness temperature

Then classify each scan against those baselines:
- BTD < 0 and |BTD| < |LND − 5.1 K (land) / 4.1 K (ocean)| ⇒ cloud
- Else if (BTD − SPD) > 2.0 K ⇒ cloud
- Then on remaining "clear": if Ch13 BT < WTV − 18.5 K ⇒ cloud (catches missed cold cloud)
- Daytime visible refinement (Reinke 1992): per-pixel month-hour-specific min-albedo background; flag pixels exceeding background + threshold.

This is what makes BTD work in daylight — the *baselines absorb the diurnal solar contamination* of Ch7, so the relative test stays meaningful. But it requires a fully populated month-hour archive (every month-hour bin needs ≥ ~30 clear-sky samples), per-pixel statistics, and is operationally significant work. Defer to v2.

## Storage budget

The constraint: **~38 GB free on disk** as of 2026-05-04. Current GOES-16 archive is 2.9 GB (one season, nighttime Ch7 only). The ticket previously cited "~16 GB" — that's the projected fully-populated multi-year nighttime archive (Ch7 + Ch13, 4 weeks/year × 5 years × 7-hr nighttime window × 2 scans/hr = ~3,920 files × ~4 MB).

Per-channel CMIPC file sizes (full CONUS):

| Channel | Native res | File size |
|---|---|---|
| Ch2 (0.64 µm visible) | 0.5 km | ~50 MB |
| Ch5 (1.6 µm SWIR) | 1 km | ~12 MB |
| Ch7 (3.9 µm) | 2 km | ~4 MB |
| Ch13 (10.3 µm) | 2 km | ~4 MB |

Daytime sample: 4 weeks/year × 7 days × 3 years (2023–2025) × 3-hr window × 2 scans/hr = 504 scans/channel.

| Approach | Channels | Full CONUS | Subset to bbox |
|---|---|---|---|
| Option A (visible-only) | Ch2 | **25 GB** | ~1.3 GB |
| Option B (visible + warm IR) | Ch2 + Ch13 | **27 GB** | ~1.4 GB |
| Option C-day (full multi-test) | Ch2 + Ch5 + Ch7 + Ch13 | **35 GB** | ~1.7 GB |

**Conclusion:** Option A and B fit on disk even without subsetting; C is borderline. Subsetting on download (open with `xarray`/`netCDF4`, crop to `outputs/study_area_bbox.json`, write reduced NetCDF) is still strongly recommended — it future-proofs against extending the archive (e.g., adding 2026 in October, or extending to 5+ years) and speeds up downstream processing. The existing `16_download_multiyear_goes16.py` does *not* subset — that's the script change.

## Validation plan

Two independent ground-truth sources, both used by the reference papers:

1. **CIMIS solar radiation correlation** (Rastogi-style). Pull daily insolation totals from CIMIS stations inside the bbox (e.g., Bodega Bay, Pepperwood-area, Big Sur, Eureka). Cloudy days should anti-correlate with insolation. Rastogi reports r²=0.74–0.75; that's the bar.
2. **Airport ceiling correlation** (Torregrosa-style). Pull METAR cloud-ceiling reports < 400 m for nearby ASOS stations (Arcata, Monterey, Half Moon Bay, Crescent City). Days flagged "fog" by the satellite layer should correlate with ceiling-below-400m hours. Torregrosa reports r²=0.83 at Monterey.

Both pair with ticket 29 (negative control points) — Sacramento, Bakersfield etc. should drop near-zero on the daytime layer. The v0 nighttime layer's miscalls there are the size of the v1 measurement gain.

## Out of scope (and why)

- **Snow discrimination via Ch5 (1.6 µm).** Neither Torregrosa nor Rastogi uses it for CA. Snow contamination is a Sierra/Cascades concern; the 80-day fog criterion already implicitly excludes those zones (FLCC < 1 h/d above ~1000 m per Torregrosa Fig. 9). A simple elevation mask is cheaper than a channel.
- **Spatial homogeneity (5×5 std-dev) tests.** Cermak/Mahdavi developed these for sea-fog over open ocean where stratus-vs-cumulus matters. CA marine stratus is morphologically distinct enough that albedo + warm-cloud filter catches it. Reconsider if Option B has visible false positives over inland summer convection.
- **Cloud-base height / true fog inundation.** Satellite measures cloud *tops*. Rastogi gets to per-pixel fog presence by combining 100-m DEM with airport ceilometer ECDFs of cloud-base height — substantial extra work and only validated for Channel Islands. For v1, "low cloud overlying canopy elevation" is a defensible proxy; flag the gap explicitly when reporting the layer.
- **Cloud-top altitude** (ABI alone can't give this without ancillary data).
- **Fog drip quantity** (needs foliage-interception modeling on top of presence).
- **Switching to MODIS/VIIRS** (finer spatial, much worse temporal — wrong tradeoff for a "hours of fog past noon" criterion).

## Sketch

```
scripts/
  18_download_daytime_goes18.py    # GOES-18, 19-22 UTC, Ch2 (+ Ch13 if Option B), subset on download
  19_create_daytime_fog_layer.py   # albedo > 0.30 (+ optional BT > 270 K), aggregate to days/season

outputs/
  study_area_fog_days_daytime.tif    # daytime fog days per dry season
  study_area_fog_days_combined.tif   # nighttime OR daytime — the original heuristic actually wants daytime-only
```

`04_combine_suitability.py` switches to the daytime layer (the ecological criterion is "fog past noon," not "fog at any time"). Worth a one-time comparison: how much smaller does the suitable area get when we go from nighttime-OR to daytime-only? That delta is the size of the v0 measurement error.

## References

Local PDFs (in repo root, not committed):
- *Earth and Space Science - 2015 - Torregrosa - GOES-derived fog and low cloud indices for coastal north and central.pdf* — directly relevant; uses GOES-W (precursor to GOES-18), month-hour matched algorithm, validated against airport ceilings (r² = 0.83 at Monterey).
- *ei-d-15-0033.1.pdf* (Rastogi et al. 2016) — visible-only albedo > 0.30, validated against ground insolation (r² ≈ 0.75), shows DEM-downscaling path for cloud-base.

Other sources cited in the design above:
- Mahdavi et al. 2020, *A probability-based daytime algorithm for sea fog detection using GOES-16 imagery*, IEEE J-STARS — multi-test classifier; PoD 0.77, FAR 0.09 (over ocean).
- Cermak & Bendix 2008, *A novel approach to fog/low stratus detection using Meteosat 8 data*.
- Jedlovec & Laws 2003 / Lee et al. 2011 — the temporally-continuous month-hour matching technique.
- GOES-R Fog/Low Stratus ATBD (NESDIS, current rev).
- Iacobellis & Cayan 2013 — supports the "CA summer clouds are ~exclusively low marine stratus" assumption that lets us skip cirrus filtering in Option A.
