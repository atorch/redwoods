# redwoods

Welcome to the repo for [redwoods.earth](https://redwoods.earth).

This project was largely vibe coded (slop warning; don't take anything here too seriously); that said, if you're here, I hope you'll find it delightful.

Want to help make the repo better, and improve the map? Open an [issue](https://github.com/atorch/redwoods/issues), or send me a PR to add to the list of [ground truth points](web/ground_truth_points.csv).

Compared to the [Wikipedia range map](https://upload.wikimedia.org/wikipedia/commons/5/5f/Sequoia_Sequoiadendron_range_map.png), [redwoods.earth](https://redwoods.earth) is:
- interactive
- answering a different question: instead of "where are redwoods [growing today](https://youtu.be/cYCajfj5AYk?si=ihWj6SN6KaMkGdgS&t=86)?", it asks "where _could_ redwoods grow today, based on fog and rainfall?" -- which is very similar to asking "where _might_ redwoods have existed in the 1700s?"

## Quick Start: Viewing Results

**QGIS (recommended):**
```bash
qgis outputs/study_area_redwood_suitable.tif
```

**Web browser (interactive tiles):**
```bash
cd web
python3 -m http.server 8000
# Open http://localhost:8000/
```

Tiles live under `web/tiles/` so `web/` is a self-contained static site -- it's what I upload to Cloudflare Pages for production.

## Project Goal

An interactive map of **natural suitable redwood habitat** showing where coastal redwoods could grow based on physical conditions (fog, rainfall, temperature, land cover), rather than a survey of where they happen to be growing today.

This represents both historical range (ca. 1750, pre [European settlement](https://www.loc.gov/collections/california-first-person-narratives/articles-and-essays/early-california-history/spanish-california/)) and hypothetical suitable habitat today: the same environmental criteria apply, so if conditions support redwoods naturally, they likely existed there historically and could exist there today absent urban development and invasive species.

Study area: the coastal fog belt from Big Sur, CA to the Oregon border.

## Running Scripts

Scripts can be run using `uv` which automatically manages Python dependencies:

```bash
uv run python scripts/<script_name>.py
```

For scripts needing extra dependencies:
```bash
uv run --with rasterio --with pandas --with shapely python scripts/<script_name>.py
```

### Available Scripts

**Data verification:**
- `scripts/check_prism_precipitation.py` - Sanity check PRISM precipitation data at Oakland, CA

**Active pipeline:**
- `scripts/01_process_study_area_rainfall.py` — PRISM wet-season rainfall, ≥ 20" mask
- `scripts/16_download_multiyear_goes16.py` — fetch GOES-16 Ch7/Ch13 for 06–12 UTC, 4 weeks × 5 years
- `scripts/11_create_real_fog_layer.py` — nighttime BTD (Ch13−Ch7) → fog-nights/season
- `scripts/17_build_land_mask.py` — water/wetland exclusion from USDA CDL
- `scripts/build_temperature_masks.py` — PRISM tmin/tmax → maritime temperature envelope
- `scripts/build_phzm_mask.py` — PRISM PHZM extreme-min-temp → frost-hardiness mask
- `scripts/04_combine_suitability.py` — rain ∧ fog ∧ land ∧ temperate ∧ frost-hardy → suitability raster
- `scripts/13_generate_web_tiles.py` — bake the raster into web map tiles

`scripts/18_download_daytime_goes18.py` + `scripts/19_create_daytime_fog_layer.py`
build the daytime GOES-18 fog layer, kept around as a diagnostic
(`scripts/annotate_ground_truth_points.py` samples it for comparison) but no
longer the live fog input. Other earlier numbered scripts (`02_*`–`15_*`) are
superseded experiments preserved in git history.

## Data Sources

Core environmental data behind the suitability rule (see `scripts/suitability.py` for the exact thresholds):
1. **Fog/coastal moisture**:
   - GOES-16 ABI Channels 7 (3.9 µm) and 13 (10.3 µm) — nighttime
     brightness-temperature difference (Ch13−Ch7) flags low water cloud
     (NESDIS nighttime fog/low-cloud detection method); aggregated to
     fog-nights/season over a 4-week × 5-year (2020–2024) sample
2. **Climate**:
   - PRISM monthly precipitation data — wet-season (Nov–Apr) totals
   - PRISM monthly tmin/tmax normals — coldest-month / hottest-month
     maritime envelope (rejects cold Cascade interior, hot Central Valley)
3. **Land cover**:
   - USDA Cropland Data Layer — drop open-water and wetland pixels
4. **Frost hardiness**:
   - USDA Plant Hardiness Zone Map (PRISM) average annual extreme minimum temperature — rejects high-elevation / far-northern-interior sites that pass the mean coldest-month floor but see real winter cold snaps

**Optional refinements** (future work):
- Topography: USGS 3DEP DEM → slope, aspect, topographic wetness index
- Soil data: SSURGO for soil type preferences
- Invasive species: Eucalyptus mapping via NAIP or Cal-IPC data

## Habitat Suitability Heuristic

Starting point: a simple heuristic for identifying historical (pre-settlement) redwood presence:

> "If the place is north of San Simeon, fog currently lasts past noon 80 days/dry season,
> and the place has more than 20 inches/year of rain in the wet season, it had redwoods in 1750."

The original heuristic uses latitude as a coarse proxy for the cold-interior /
hot-Central-Valley boundary. The shipped rule drops the latitude filter in
favor of a maritime temperature envelope (PRISM tmin/tmax) plus a frost-hardiness
mask (PHZM extreme-min-temp) and a land mask (USDA CDL) -- more principled, and
they reject the same false-positives the 35.6°N cut was meant to catch. See
`scripts/suitability.py` for the exact rule and threshold rationale, and
`tickets/` for the history of how each criterion was tuned against ground truth.
