# Evaluate published fog rasters as a drop-in replacement for our GOES-18 pipeline

**Status:** Phase 2 complete; Phase 3 reframed · **Priority:** medium (was high — see Phase 2 results) · **Created:** 2026-05-14 · **Updated:** 2026-05-14 · **Supersedes (if integrated):** ticket 22 (daytime fog detection), ticket 33 (morning fog window extension) · **Related:** ticket 29 (negative controls — now the higher-priority follow-up), ticket 30 (weighted suitability rule)

## Phase 2 result — TL;DR

Neither published product gives clean positive/negative separation on fog alone, and neither fixes the inland-incursion under-detection. **The fog input is not the bottleneck; cloud-top vs. cloud-base is** (ticket 29 §1). Adopting MODIS is still defensible as a *simpler equivalent* to our GOES-18 pipeline (lighter, externally validated, threshold becomes honest), but it is not a fix. See **Phase 2 findings** and **Revised Phase 3** below.

## Why now

We've spent ticket 22 + ticket 33 building our own daytime fog raster from raw GOES-18 Ch2 (download → albedo threshold → OR-aggregate → extrapolate to 184-day dry season). The current layer still under-detects deep inland-incursion sites: after the ticket-33 morning-window extension, Armstrong (43.8), Humboldt (32.1), and Navarro (42.3) all *moved in the right direction* but still fall below the 50-day threshold. The next step in our own pipeline would be more threshold tuning, possibly a weighted rule (ticket 30), and at some point an IR-based nighttime/cloud-top algorithm (Option C in ticket 22).

Before doing more of that, we should check whether somebody has already published a peer-reviewed coastal-CA fog raster covering exactly our region and use period. If the answer is yes and it agrees with our control points, we'd be replacing several hundred lines of pipeline plus ~10 GB of intermediate GOES files with one downloaded GeoTIFF — same way we use PRISM directly instead of re-deriving precipitation climatology from raw weather-station data.

Two strong candidates exist; both are free, citable, and validated.

## Candidate 1 — Torregrosa et al. 2016 Decadal FLCC (gold standard for our use case)

This is the dataset *from the same paper we've been reading and citing in our pipeline comments*. Authors derived monthly, daytime, nighttime, and decadal-average Fog and Low Cloud Cover (FLCC) rasters from ~26,000 hourly GOES-W images (1999–2009, Jun–Sep).

- **Source:** http://climate.calcommons.org/datasets/summertime-fog (CalCommons hosting) and https://www.sciencebase.gov/catalog/item/59fb6133e4b0531197b164ea (USGS ScienceBase mirror).
- **Format:** 11 ESRI raster grids in a 3.3 MB zip, plus a separate contour shapefile zip. ESRI grids are readable directly by `rasterio` / GDAL (`gdal_translate` to GeoTIFF if needed).
- **Resolution:** **4 km**. Coarser than our other layers (PRISM is 800 m, our current fog layer is at study-area grid resolution) — this is the main caveat.
- **Units:** Average **hours per day** of FLCC (different scale from our current "fog-days per dry season").
- **Coverage:** "North and Central Coastal California." Need to confirm latitude extent covers our full bbox (35.71–42.09 N). Torregrosa's Figure 2 shows the FLCC analysis frame includes Humboldt Bay and Eel River incursion zones at the northern end and extends south past Monterey — likely covers all of our bbox except possibly the northernmost OR-adjacent fringe.
- **Layers in the zip:**
  - 1 decadal summer-season mean (Jun–Sep averaged)
  - 2 statistics layers — standard deviation and coefficient of variance
  - 4 monthly means — June, July, August, September
  - 2 diurnal splits — daytime and nighttime
- **Validation in the paper:** r² = 0.83 vs. Monterey airport ceilings; explicitly developed for "biogeographic and bioclimatic species distribution models" — i.e., exactly our use case.
- **Citation:** Torregrosa, A., C. Combs, and J. Peters (2016), *GOES-derived fog and low cloud indices for coastal north and central California ecological analyses*, Earth and Space Science, 3, doi:10.1002/2015EA000119.

## Candidate 2 — Werner et al. 2022 MODIS Monthly FLCC (longer time series, finer resolution)

A more recent, higher-resolution product. MODIS-derived, validated against Candidate 1 (Torregrosa GOES) at r² = 0.82, so the two products are mutually consistent and either can be used with confidence.

- **Source:** https://mountainscholar.org/items/57c1ddb7-a381-420d-95bd-400358e4eb03 (handle `hdl:10217/235754`).
- **Format:** 87 MB zip — file format inside not stated on the landing page; the companion paper (Werner et al. 2022, *Remote Sensing Applications: Society and Environment*) will specify. Expect GeoTIFF or NetCDF.
- **Resolution:** **1 km**. Closer to PRISM's 800 m, so resampling distortion is minimal.
- **Units:** Fog-days per month (per the source description, "summarized into days per month").
- **Coverage:** California + Southern Oregon coast — explicitly includes Big Sur and extends north of our bbox.
- **Temporal coverage:** 2000–2022, June–September. Longer record than Torregrosa (1999–2009) and ends much closer to our 2023–2025 dry seasons.

## Why this approach is consistent with how we already use external data

- We use PRISM directly for rainfall (`scripts/02_compute_wet_season_rainfall.py`) instead of re-deriving precipitation climatology.
- We use PRISM directly for tmin/tmax (`scripts/suitability.py` temperature constraints) instead of re-deriving from raw stations.
- A peer-reviewed, validated, coastal-CA fog raster from the *same paper* we've been citing is the same kind of input. Replicating it in-house was the right move when we didn't know whether such a product existed; now we know.

## Proposed work

### Phase 1 — Acquire and inspect (DONE 2026-05-14)

Acquired both products:
- Torregrosa decadal FLCC: `data/summertime_fog_decadal_rasters/decadal_rasters/` (11 ESRI Arc/Info Binary Grids — `flcc_decadal`, `flcc_deca_day`, `_nit`, monthly `_jun/_jul/_aug/_sep`, and stats `_sd`/`_cv`). NAD83/EPSG:4269, 4 km, Float32, hours/day. **Northern edge 42.022°N** — clips a ~8 km strip off our 42.096°N study-area top. **Inland east of the coastal frame is NoData** — Mt Shasta, Modesto, Stockton, Los Banos all return NoData. rasterio reads the grids by pointing at the directory (no extension).
- Werner MODIS FLCC: `data/MODIS_Monthly_FLCC_Rasters_2000-2022/` (91 monthly GeoTIFFs, Jun–Sep 2000–2022, plus README). WGS84/EPSG:4326, 1 km, Float32, fog-days/month. Bbox 32.42–48.28°N × −125.10 to −115.41°W — **fully covers our study area, all positive and negative control points, and the entire web-tile bbox.**

Both directories are git-ignored under `data/`. No QGIS visual check performed — Phase 2 sampling was decisive enough that visual inspection wasn't needed.

### Phase 2 — Validate at control points (DONE 2026-05-14)

Implemented in `scripts/eval_published_fog_rasters.py` (samples both products at all positive and negative control points; for MODIS averages Jun–Sep across 2018–2022 to produce mean fog-days/month).

**Separation between positive and negative classes:**

| Product | Positives range (mean, n) | Negatives range (mean, n) | min(pos) − max(neg) |
| --- | --- | --- | --- |
| MODIS days/month (Werner) | 2.74–20.63 (8.71, n=12) | 1.00–17.68 (7.80, n=8) | **−14.95** (overlap) |
| Torregrosa decadal hr/day | 1.99–10.36 (5.81, n=12) | 2.28–3.56 (3.01, n=4) | **−1.57** (overlap) |
| Torregrosa daytime hr/day | 1.33–5.37 (2.96, n=12) | 1.47–2.32 (2.08, n=4) | **−0.99** (overlap) |

Torregrosa's "clean-looking" negative range is an artifact of NoData at 4 inland-east negatives (Shasta, Modesto, Stockton, Los Banos). The product's coastal frame simply doesn't extend that far inland.

**Per-site comparison vs. our current GOES-18 layer:**

```
Site                              Our_fog  MODIS  Torre_dec  Torre_day  Expected
Muir Woods                        65.7     10.00    4.80       2.30     high
Redwood Regional Park (Tres S.)   65.7      3.84    4.67       2.34     high
Redwood Regional Park (Old Ch.)   75.9      3.58    4.18       2.06     high
The Elbow Tree                    83.2      8.79    8.83       4.52     high
Grove of Old Trees                52.6      5.32    4.85       2.44     high
Armstrong Redwoods                43.8      2.74    3.19       1.71     high  ← still fails on both
Humboldt Redwoods                 32.1      3.74    7.05       3.16     high  ← still fails on both
Navarro River                     42.3      5.68    8.21       4.21     high  ← still fails on both
Stout Grove                       71.6      9.74    8.49       4.47     high
Redwood National Park             83.2     13.16   10.36       5.37     high
Limekiln State Park               89.1     20.63    1.99       1.33     high
Ewoldsen Trail                    62.8     17.26    3.07       1.56     high
Davis                             21.9      1.00    2.28       1.47     low
Mt Shasta                        132.9     15.79    NoData     NoData   low   ← MODIS does NOT fix
Weaverville                       38.0      6.58    3.56       2.32     low
Modesto                            —        9.32    NoData     NoData   low
Antioch                           17.5     17.68    3.34       2.32     low   ← MODIS scores it as fog
Stockton                          24.8      9.79    NoData     NoData   low
Panoche Hills                      —        1.21    2.87       2.21     low
Los Banos                          —        1.05    NoData     NoData   low
```

**Key findings:**

1. **Inland-incursion failure persists across all three products.** Armstrong / Humboldt Redwoods / Navarro — the three positive sites our current GOES-18 layer puts below the 50-day threshold — also sit in the low tail of MODIS (2.74 / 3.74 / 5.68 days/mo) and don't stand out in Torregrosa either. This is the decisive negative result: the ticket's hypothesis was "maybe a peer-reviewed FLCC product fixes the inland-incursion gap." It does not.
2. **Mt Shasta still scores high on MODIS** (15.79 days/mo) — orographic high cloud confuses MODIS the same way it confuses our GOES-18 albedo threshold. Torregrosa side-steps the issue only because the site is outside its coastal frame.
3. **Antioch (negative) scores higher on MODIS than 9 of our 12 positives.** Satellites see Delta fog crossing the sky, but Antioch isn't redwood habitat — confirming the cloud-top vs. cloud-base gap (ticket 29 §1) is the operative constraint, not the quality of the remote-sensing algorithm.
4. **Big Sur (Limekiln, Ewoldsen) shows the 4 km coastal-cell artifact in Torregrosa** (1.99 / 3.07 hr/day, below several negatives) while MODIS is plausible (20.63 / 17.26 days/mo). If we adopt a published product, MODIS is the only viable choice for our geometry.
5. **The published products disagree with each other** by ~2× at Humboldt and Navarro and by an order of magnitude at Limekiln. r² = 0.82 between them globally doesn't mean point-level interchangeability.

**Conclusion against the ticket's decision criterion:** both candidates fail the same way our layer fails. Per the criterion stated in the original Phase 2 ("If both fail the same way our layer fails, that's strong evidence the 'fog seen from space ≠ fog touching canopy' gap is the actual bottleneck"), **the next investigation should move to ticket 29 §1** (cloud-base / ceilometer data, ground-station fog drip, RAWS or similar). Better satellites won't close the gap.

**The rest of the suitability rule covers the negatives.** Even with MODIS as the fog layer, the negative controls fail on other bands: Shasta on tmin (−14.49 °C); Antioch on rainfall (12.45 in); Stockton/Modesto/Davis/Los Banos/Panoche on rainfall; Weaverville is genuinely borderline. So the question for Phase 3 is not "does the negative set still get excluded" (yes, via precip + temp) but "do we want a fog input that's lighter and more honest, given that none of them fix the positives we already miss."

### Phase 3 — Revised: adopt MODIS as a simpler equivalent (not a fix)

Phase 2 did not pick a winner on accuracy — both products and our own layer fail the inland-incursion test the same way. The remaining case for adoption is *engineering*, not accuracy:

- Removes ~10 GB of GOES intermediates + ~30 min of S3 traffic per pipeline regen.
- Removes ~several hundred lines of pipeline (`18_download_daytime_goes18.py`, `19_create_daytime_fog_layer.py`).
- Replaces a threshold we tuned against our own ground truth with an externally validated, peer-reviewed product → the suitability fit becomes honest.
- Acknowledges what the product actually is and isn't: the inland-incursion gap is documented as a citable limitation of cloud-top FLCC, not a suspicion about our own thresholding.

**MODIS over Torregrosa**, because:
- Covers full study-area bbox; Torregrosa cuts off at 42.022°N and is NoData east of its coastal frame.
- 1 km vs 4 km — Big Sur shows clearly that 4 km cells smear the steep coastal canyons.
- 2000–2022 vs 1999–2009 — closer to PRISM 1991–2020 baseline.
- Plain GeoTIFFs vs ESRI Arc/Info grids.

**Proposed integration steps (when picked up):**

1. Add `scripts/20_prepare_published_fog.py`:
   - Reads MODIS Jun–Sep GeoTIFFs (likely 2018–2022 to match the Phase 2 averaging window).
   - Averages per pixel across all (year, month) tiles.
   - Reprojects + resamples to the study-area grid (matching `outputs/study_area_rainfall_total.tif`).
   - Writes `outputs/study_area_fog_modis.tif` (units: mean fog-days per Jun–Sep month).
2. Update `scripts/suitability.py`: rename `FOG_DAYS_THRESHOLD` → `FOG_DAYS_PER_MONTH_THRESHOLD` (or similar) and refit the cutoff against the new unit. Expected to land somewhere in the 4–6 days/month range based on Phase 2 positives, knowing this still won't rescue Armstrong/Humboldt/Navarro.
3. Mark `scripts/18_download_daytime_goes18.py` and `scripts/19_create_daytime_fog_layer.py` as superseded via header comment (do not delete — pattern established in `CLAUDE.md` for `03_*`/`05–10_*`).
4. Update `README.md` validation section: fog input changes from "GOES-18 Ch2 albedo threshold, 6-week sample × 3 yrs" to "Werner et al. 2022 MODIS Monthly FLCC, Jun–Sep 2018–2022 mean."
5. Mark tickets 22 and 33 as **superseded**.
6. Open a follow-up ticket against ticket 29 §1 (cloud-top vs cloud-base) as the next real investigation; published rasters confirm the bottleneck lives there.

**Open question before doing this work:** is the engineering simplification worth the churn given that accuracy is unchanged? Possible answer: park Phase 3 until ticket 29 §1 results are in. If ground-station fog drip data shows a different fog signal that actually separates the positives, we'd want to integrate *that* and the MODIS migration becomes irrelevant work.

## What this resolves

- **Inland-incursion under-detection** (the main symptom that motivated ticket 33). If Torregrosa/Werner show Eel and Russian River valleys in their high-FLCC band — which the Torregrosa paper Figure 5c explicitly does — the under-detection problem disappears with the data change.
- **Threshold-tuning circularity.** A published, externally-validated product gives us a fog input that *we did not tune against our own ground truth*, so the suitability threshold becomes an honest fit instead of a circular one.
- **Pipeline weight.** Removes the GOES download + processing burden (~30 min of S3 traffic per regen, ~few GB of intermediate files).

## What this does NOT resolve

- **The cloud-top vs. cloud-base gap** flagged in ticket 29 §1. Both candidate rasters are still derived from satellite-observed cloud tops; neither tells us whether the cloud was actually wetting the canopy. If the Phase-2 validation shows neither product cleanly separates positives from negatives, this is the most likely reason and the right next step is ground-station or LCL/ceilometer data.
- **Temperature- and elevation-driven false positives** (Limekiln, Mt Shasta). Those are addressed by tickets 31 and 32, not by changing the fog input.

## Risks / things to verify before committing

- **Northern bbox extent for Torregrosa.** "North and Central Coastal California" likely stops short of the OR border. If the Torregrosa raster's northern edge cuts off the Smith River / Jedediah Smith Redwoods area (lat ≈ 41.7–42.0 N), we either need to use Werner (which explicitly extends into S. Oregon), mosaic the two, or accept a small NoData band along the northern bbox. Verify in Phase 1 step 4.
- **License / citation.** Torregrosa product is hosted by CalCommons + USGS and is freely distributable with citation. Werner is via Colorado State / Mountain Scholar; the landing page indicates open download but check the page for an explicit license tag during Phase 1.
- **Resolution mismatch.** Torregrosa at 4 km is much coarser than our 800 m–ish study grid. The 4 km cell straddling the coastline will report a single FLCC value that mixes coastal-saturated and immediate-inland pixels. Werner at 1 km is much less affected. Worth keeping both in the comparison even if one is clearly better.
- **Temporal mismatch.** Torregrosa: 1999–2009. Werner: 2000–2022. Our PRISM normals are 1991–2020. The fog climatology in coastal CA has decreased ~33% since 1900 (Johnstone & Dawson 2010), but interannual CV inside Torregrosa's 11-year window is < 0.10 in our target zones (Torregrosa Fig 4b). The decade-old data is fine for a climatology.

## References

- Torregrosa, Combs, Peters 2016, *Earth and Space Science* (in repo root PDF).
- Werner et al. 2022, *Remote Sensing Applications: Society and Environment* — companion paper for the MODIS dataset; DOI: 10.25675/10217/235754 for the dataset itself.
- Pacific Coastal Fog Project landing page: https://www.usgs.gov/centers/western-geographic-science-center/science/pacific-coastal-fog-project
- CalCommons dataset page: http://climate.calcommons.org/datasets/summertime-fog
- USGS ScienceBase mirror: https://www.sciencebase.gov/catalog/item/59fb6133e4b0531197b164ea
- mountainscholar.org Werner dataset: https://mountainscholar.org/items/57c1ddb7-a381-420d-95bd-400358e4eb03
