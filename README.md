# redwoods

This is the repo for [redwoods.earth](https://redwoods.earth) — a map of coastal redwoods ([coast redwood ecology and distribution](https://www.savetheredwoods.org/redwoods/coast-redwoods/)).

https://youtu.be/cYCajfj5AYk?si=ihWj6SN6KaMkGdgS&t=86

Compared to the [Wikipedia range map](https://upload.wikimedia.org/wikipedia/commons/5/5f/Sequoia_Sequoiadendron_range_map.png) (a static PNG based on late-1900s survey data), we're aiming for a map that is:
- interactive
- answering a different question: instead of "where are redwoods growing today?", we want to ask "where _could_ redwoods grow today, based on fog and rainfall (and possibly other factors like soil type)?" — which is very similar to asking "where _might_ redwoods have existed in the 1700s?"

-- TODO: Link to nytimes article about world's tallest tree

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

Tiles live under `web/tiles/` so `web/` is a self-contained static site — the same directory is uploaded to Cloudflare Pages for production.

## Project Goal
Create an interactive web-based map showing:
1. **Layer 1**: Where coastal redwoods are growing today (current distribution)
2. **Layer 2**: Natural suitable habitat - where redwoods could grow without modern human impacts

**Key insight**: Layer 2 represents both historical range (ca. 1750, pre-settlement) and hypothetical suitable habitat today. The same environmental criteria apply: if conditions support redwoods naturally, they likely existed there historically and could exist there today absent urban development and invasive species.

Focus area: California Bay Area and Pacific coast

## Technology Stack (Draft)

### Data Processing
- **Python** (managed with `uv`)
- **rasterio** - raster data processing
- **geopandas** - vector data processing
- **shapely** - geometric operations
- **numpy/scipy** - numerical operations
- **scikit-learn** - potential ML for classification/habitat modeling

### Visualization
- **Tile generation**:
  - Vector tiles: `tippecanoe` or `rio-tiler`
  - Raster tiles: `gdal2tiles` or `rio-tiler`
- **Web mapping**: Leaflet.js, Mapbox GL JS, or OpenLayers
- **Basemap**: OpenStreetMap or satellite imagery

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
- `scripts/04_combine_suitability.py` — rain ∧ fog ∧ land ∧ temperate → suitability raster
- `scripts/13_generate_web_tiles.py` — bake the raster into web map tiles

`scripts/18_download_daytime_goes18.py` + `scripts/19_create_daytime_fog_layer.py`
build the daytime GOES-18 fog layer, kept around as a diagnostic
(`scripts/annotate_ground_truth_points.py` samples it for comparison) but no
longer the live fog input. Other earlier numbered scripts (`02_*`–`15_*`) are
superseded experiments preserved in git history.

## Data Sources

### Current Redwood Detection
1. **Ground truth points** (user-provided lat/lon)
2. **NAIP imagery** (1m resolution, 4-band) - for visual/spectral classification
3. **Park boundaries** - State/National parks with known redwood groves (CAL FIRE, NPS data)
4. **Sentinel-2** or **Landsat 8/9** - multispectral for NDVI, vegetation indices
5. Potentially **LiDAR data** (USGS 3DEP) - tree height can help identify tall redwoods

### Natural Suitable Habitat (Layer 2)

**Primary approach**: Academic heuristic defining redwood habitat suitability

Core environmental data needed:
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

**Optional refinements** (future work):
- Topography: USGS 3DEP DEM → slope, aspect, topographic wetness index
- Soil data: SSURGO for soil type preferences
- Land use masking: CDL/NLCD to identify urban areas (for "could grow if not developed" scenarios)
- Invasive species: Eucalyptus mapping via NAIP or Cal-IPC data

### Reference Data
- Historical redwood range maps (Cal Fire, Save the Redwoods League) for validation
- Species distribution models for *Sequoia sempervirens*

## Habitat Suitability Heuristic

Academic heuristic for identifying historical (pre-settlement) redwood presence:

> "If the place is north of San Simeon, fog currently lasts past noon 80 days/dry season,
> and the place has more than 20 inches/year of rain in the wet season, it had redwoods in 1750."

The original heuristic uses latitude as a coarse proxy for the cold-interior /
hot-Central-Valley boundary. In implementation we dropped the latitude filter
in favor of a maritime temperature envelope (PRISM tmin/tmax) plus a land mask
(USDA CDL) — more principled, and they reject the same false-positives that the
35.6°N cut was meant to catch.

### Data Requirements for This Heuristic

1. **Fog persistence**: Fog lasts past noon 80+ days during dry season (May-Oct)
   - **Status**: ⚠️ **CRITICAL DATA GAP** - need time-of-day + seasonal data
   - **Current plan**: MODIS cloud frequency, relative humidity (insufficient)
   - **Gap**: Need time-of-day specificity (past noon) and seasonal aggregation
   - **Recommended dataset**: **GOES-16 satellite data (NOAA)**
     - Used by [fog.today](https://fog.today/) for real-time Bay Area fog visualization
     - Provided by UW-Madison Space Science & Engineering Center's Real Earth project
     - High temporal resolution (hourly or better) enables "past noon" filtering
     - Historical patterns available (see "Fogust" tool on fog.today)
     - **Note**: May have artifacts/inaccuracies, needs validation
   - **Alternative sources**:
     - NOAA weather station fog observations (point data → interpolate to raster)
     - California coastal fog studies (UC Berkeley, USGS fog trend datasets)
   - **Processing needed**:
     - Filter for afternoon hours (12pm-6pm or similar)
     - Aggregate by dry season (May-Oct) to count "fog past noon" days
     - Create raster: "average days/year with afternoon fog" or monthly breakdowns
   - **Question**: Monthly averages likely sufficient vs. daily rasters

2. **Wet season precipitation**: 20+ inches during wet season (Nov-Apr)
   - **Status**: ✓ Covered by PRISM
   - **Current plan**: PRISM monthly precipitation normals
   - **Implementation**: Aggregate Nov-Apr months, create 20" threshold layer
   - **Question**: Is monthly resolution sufficient, or do we need weekly precipitation data?

### Use of This Heuristic

This three-criteria model defines **Layer 2** (natural suitable habitat):
- **Simple and interpretable**: Rule-based approach grounded in academic expertise
- **Historical validity**: Represents pre-settlement (1750) redwood range
- **Modern application**: Also shows where redwoods could grow today given suitable environmental conditions
- **Foundation for refinement**: Can later enhance with ML models, additional variables (soil, topography, etc.)
- **Validation baseline**: Compare against current redwood locations and historical range maps

## High-Level Workflow

### Phase 1: Data Acquisition & Preprocessing
1. Download and mosaic NAIP imagery for study area
2. Acquire DEM, climate data, CDL, park boundaries
3. Process fog/cloud frequency data
4. Standardize all data to common CRS and resolution

### Phase 2: Current Redwood Mapping
1. Start with ground truth points + park boundaries
2. Use NAIP + spectral indices to classify potential redwood areas
3. Possibly train a Random Forest or CNN classifier on known redwood vs non-redwood areas
4. Validate and refine classification
5. Generate "current redwoods" vector/raster layer

### Phase 3: Habitat Suitability Model
1. Create environmental layers stack (climate, fog, elevation, slope, aspect, soil)
2. Use MaxEnt, GLM, or similar species distribution modeling
3. Generate suitability scores for entire region
4. Mask out current urban areas (CDL) to show "could grow here if not urban"
5. Identify areas with eucalyptus/invasive species to exclude/flag

### Phase 4: Tile Generation
1. Convert processed layers to web tiles (zoom levels 8-16?)
2. Optimize for web delivery
3. Host tiles (local server, GitHub Pages, or cloud)

### Phase 5: Web Interface
1. Create interactive map with layer toggles
2. Add legend, metadata, data sources
3. Optional: Click to see environmental variables at a location

## Questions & Considerations

### Technical considerations:
- **Fog is critical**: Coastal redwoods need fog drip. How to best model this?
  - Options: MODIS cloud frequency, proximity to coast + elevation interaction, climate moisture indices
- **Spectral signature**: Redwoods vs other conifers (Douglas fir, etc.) - may need careful classification
- **Scale**: Bay Area alone vs entire coast - affects data size and processing time
- **Temporal**: NAIP imagery year? Should we use most recent only?
- **Competition model**: Modeling eucalyptus removal is complex - just map current eucalyptus areas?

### Additional datasets to consider:
- **Fire history**: Recent fires may have affected redwood distribution
- **Water sources**: Streams, watersheds (redwoods prefer riparian zones)
- **Canopy height models**: Derived from LiDAR to identify tall trees
- **Protected areas**: Not just parks but also conservation easements

