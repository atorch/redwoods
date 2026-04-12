# End-to-End Prototype: Redwood Habitat Heuristic Visualization

## Objective

**De-risk the entire project** by building a working end-to-end prototype that:
1. Implements the "redwoods could grow here" heuristic for the Bay Area
2. Generates a web-viewable map tile covering all ground truth points
3. Validates that the heuristic correctly identifies known redwood locations
4. Proves the complete data pipeline works from raw data → processing → web visualization

**Success criteria:** View a map in localhost browser showing:
- "Suitable habitat" layer (where all 3 heuristic criteria are met)
- 4 ground truth points from `data/redwood_ground_truth_points.csv`
- Visual confirmation that all points fall within suitable habitat

## Background

This ticket implements a simplified version of the full project to validate the approach before investing in the complete implementation. We're focusing on the Bay Area region only, covering the 4 known redwood locations:
- Redwood Regional Park (2 points)
- Muir Woods (1 point)
- The Elbow Tree (1 point)

Range: ~37.4°N to 37.9°N, ~122.6°W to 122.2°W

## The Three-Criteria Heuristic

From the academic heuristic (README.md):
> "If the place is north of San Simeon, fog currently lasts past noon 80 days/dry season,
> and the place has more than 20 inches/year of rain in the wet season, it had redwoods in 1750."

For this prototype we implement:
1. ✅ **Geographic filter**: North of San Simeon (~35.6°N) - trivial for Bay Area
2. 🔧 **Wet season rainfall**: ≥20 inches Nov-Apr (PRISM data available, needs processing)
3. ⚠️ **Fog persistence**: ≥80 days/dry season with afternoon fog (needs simplified approach for prototype)

## Tasks

### Phase 1: Data Preparation & Processing

- [ ] **1.1 Define Bay Area bounding box**
  - Extract extent covering all 4 ground truth points + margin
  - Target resolution: 800m (match PRISM native resolution)
  - Output: bounding box coordinates for all subsequent processing

- [ ] **1.2 Process wet season rainfall layer**
  - Load PRISM monthly precipitation (Nov, Dec, Jan, Feb, Mar, Apr)
  - Crop to Bay Area bounding box
  - Sum 6 months → wet season total (inches)
  - Create binary threshold: `rainfall_suitable = total >= 20 inches`
  - Output: `bay_area_rainfall_20in.tif`
  - Reference: Ticket #01 (PRISM data), #02 (wet season processing)

- [ ] **1.3 Create fog suitability layer (PROTOTYPE APPROACH)**

  **Option A - Simple mock layer (fastest):**
  - Create synthetic fog layer based on distance from coast + elevation
  - Assumption: coastal areas <10 miles from ocean = high fog
  - Validate against known fog patterns (coast foggy, Central Valley not foggy)
  - Mark as placeholder for full GOES-16 processing

  **Option B - Limited GOES-16 processing (more realistic):**
  - Download GOES-16 Ch7 + Ch13 for ONE dry season (May-Oct 2024)
  - Process afternoon hours only (12pm-6pm local = 19:00-01:00 UTC)
  - Calculate BTD, count fog days
  - Binary threshold: `fog_suitable = days >= 80`
  - Note: Single year, not multi-year climatology
  - Data volume: ~105GB for 6 months

  **Option C - Minimal GOES-16 sampling (RECOMMENDED for prototype):**
  - Download GOES-16 Ch7 + Ch13 for 1-2 peak fog months only
  - Target: July-August 2024 (Bay Area "Fogust" peak season)
  - Alternative: July 2024 + July 2023 (test year-to-year variation)
  - Process afternoon hours only (12pm-6pm local = 19:00-01:00 UTC)
  - Calculate BTD, count fog days in sampled period
  - **Extrapolate to dry season total:**
    - Count fog days in sampled month(s)
    - Scale up based on typical seasonal patterns (July ≈ 20-25% of dry season fog)
    - Example: 15 fog days in July → estimate ~60-75 days for full dry season
  - Apply threshold with uncertainty margin
  - Data volume: ~18GB per month = 18-36GB total
  - **Advantages:**
    - 3-6× less data than full dry season
    - Still validates real GOES-16 BTD methodology
    - Peak months most representative of fog patterns
    - Fast enough for rapid prototyping
  - **Limitations:**
    - Extrapolation introduces uncertainty
    - May miss seasonal variation (early vs late dry season)
    - Acceptable for prototype/validation, not production

  **Decision point:** Recommend Option C for best balance
  - Mock (A) = fastest, proves pipeline only
  - Minimal sampling (C) = good balance, proves methodology with less data
  - Full dry season (B) = most thorough, but heavy

  Output: `bay_area_fog_80days.tif` (or `bay_area_fog_mock.tif`)
  Reference: Tickets #03, #04 (GOES-16 fog processing)

- [ ] **1.4 Apply geographic filter**
  - Create raster: `lat >= 35.6` (always 1 for Bay Area)
  - Can skip for Bay Area prototype (all points north of San Simeon)
  - Document assumption

### Phase 2: Combine Heuristic Layers

- [ ] **2.1 Align all rasters**
  - Ensure identical CRS, extent, resolution (800m)
  - Resample fog layer if needed (GOES-16 is 2km native)
  - Use PRISM resolution as target

- [ ] **2.2 Create combined suitability layer**
  - `suitable = rainfall_suitable AND fog_suitable`
  - Binary raster: 1 = meets all criteria, 0 = does not
  - Output: `bay_area_redwood_suitable.tif`
  - Reference: Ticket #09 (combine layers)

- [ ] **2.3 Validate against ground truth points**
  - Load `data/redwood_ground_truth_points.csv`
  - Extract suitability values at each point location
  - **CRITICAL CHECK**: All 4 points must have `suitable = 1`
  - If any point fails, investigate why (data issue? heuristic issue?)
  - Generate validation report with statistics

### Phase 3: Web Tile Generation & Visualization

- [ ] **3.1 Generate web map tiles**

  **Approach 1 - Simple GeoTIFF overlay (fastest):**
  - Export suitability raster as web-friendly GeoTIFF
  - Use Leaflet.js with georaster-layer-for-leaflet plugin
  - Direct raster rendering in browser

  **Approach 2 - Raster tiles (more scalable):**
  - Use `gdal2tiles.py` or `rio-tiler` to generate tile pyramid
  - Zoom levels 8-13 (Bay Area scale)
  - TMS or XYZ tile format

  **Approach 3 - Vector tiles (cleaner, but more complex):**
  - Polygonize suitability raster
  - Generate vector tiles with `tippecanoe`
  - Cleaner edges, smaller file size

  **Decision point:** Start with Approach 1 (simple), iterate if needed

  Output: Tiles in `tiles/` directory

- [ ] **3.2 Create web map interface**
  - HTML + JavaScript using Leaflet.js
  - Basemap: OpenStreetMap or Stadia Maps
  - Layers:
    - Suitability layer (green overlay where suitable)
    - Ground truth points (red markers with labels)
  - Legend showing criteria
  - Metadata panel with data sources
  - Output: `web/index.html` + supporting files
  - Reference: Ticket #20 (web map interface)

- [ ] **3.3 Set up local web server**
  - Simple Python HTTP server: `python -m http.server 8000`
  - Or `uv run` equivalent
  - Test in browser: `http://localhost:8000/web/`
  - Verify all layers render correctly

### Phase 4: Validation & Documentation

- [ ] **4.1 Visual validation**
  - Zoom to each ground truth point
  - Confirm green overlay (suitable habitat) present at all 4 points
  - Check sanity: coastal areas suitable, Central Valley not suitable
  - Screenshot results for documentation

- [ ] **4.2 Quantitative validation**
  - Extract rainfall and fog values at each ground truth point
  - Generate table showing:
    - Point name
    - Lat/lon
    - Wet season rainfall (inches)
    - Fog days (count)
    - Suitable? (yes/no)
  - All rows should show "yes"

- [ ] **4.3 Document limitations**
  - Note prototype shortcuts (mock fog data, single year, etc.)
  - List what full implementation would require
  - Estimate data volume and processing time for full version

- [ ] **4.4 Identify risks and blockers**
  - Document any issues encountered
  - Note what worked well vs what was challenging
  - Recommendations for full implementation

## Outputs

1. **Processed data layers:**
   - `outputs/bay_area_rainfall_20in.tif` - wet season rainfall threshold
   - `outputs/bay_area_fog_80days.tif` - fog persistence threshold
   - `outputs/bay_area_redwood_suitable.tif` - combined suitability

2. **Web visualization:**
   - `web/index.html` - interactive map
   - `tiles/` - map tiles (if using tiled approach)
   - Screenshot showing all 4 ground truth points in suitable habitat

3. **Validation report:**
   - Table of ground truth point values
   - Summary statistics (% of Bay Area that's suitable)
   - List of limitations and assumptions

4. **Documentation:**
   - This ticket updated with results
   - Notes on what worked / what didn't
   - Recommendations for full implementation

## Dependencies

### Data (already available):
- ✅ PRISM monthly precipitation (Ticket #01)
- ✅ Ground truth points CSV
- ⚠️ GOES-16 fog data (partial - sample files only, Ticket #03)

### Processing:
- Related to Ticket #02 (wet season rainfall)
- Related to Ticket #04 (fog persistence)
- Related to Ticket #09 (combine layers)
- Related to Ticket #20 (web map)

### Tools needed:
- `rasterio` - raster processing
- `geopandas` - vector data, ground truth points
- `numpy` - array operations
- `gdal` - tile generation (optional)
- `leaflet.js` - web mapping (CDN, no install needed)
- Python HTTP server (built-in)

## Key Risks & Blockers

### 🔴 CRITICAL RISK: Fog Data Volume
- **Issue**: Full GOES-16 climatology = 525GB for 5 years
- **Impact**: Processing time, storage requirements
- **Mitigation options:**
  1. Use mock fog layer for initial prototype (~0GB, fastest)
  2. Process 1-2 peak months + extrapolate (~18-36GB, **RECOMMENDED**)
  3. Process single dry season only (~105GB, thorough)
  4. Use pre-aggregated fog climatology if available (unknown)
- **Decision:** Option C (minimal sampling) recommended for prototype

### ⚠️ MEDIUM RISK: Resolution Mismatch
- **Issue**: PRISM (800m) vs GOES-16 (2km) resolution difference
- **Impact**: Resampling may smooth fog patterns
- **Mitigation:** Resample to 800m using appropriate interpolation

### ⚠️ MEDIUM RISK: Single-Year Fog Data
- **Issue**: If using Option B (1 dry season), not climatology
- **Impact**: May not represent typical fog patterns (2024 could be anomalous)
- **Mitigation:** Document as limitation, note need for multi-year data in full version

### ✅ LOW RISK: Web Tile Generation
- **Issue**: Multiple approaches available, unclear which is best
- **Impact**: May need iteration
- **Mitigation:** Start with simplest (direct GeoTIFF), iterate if needed

### ✅ LOW RISK: Projection Handling
- **Issue**: GOES-16 uses fixed grid projection, PRISM uses lat/lon
- **Impact**: Need to reproject
- **Mitigation:** Well-solved problem, `rasterio` handles this

## Success Metrics

1. ✅ Can view map in browser at `localhost:8000`
2. ✅ All 4 ground truth points visible on map
3. ✅ All 4 points fall within "suitable habitat" area
4. ✅ Map shows reasonable patterns (coast suitable, inland less so)
5. ✅ Processing pipeline is documented and reproducible

## Timeline Estimate (not for scheduling, just scoping)

**Option A - Mock fog:**
- Phase 1-2: 1-2 days (data processing)
- Phase 3: 1 day (web visualization)
- Phase 4: 0.5 days (validation)
- **Total: ~2-3 days**

**Option C - Minimal GOES-16 sampling (RECOMMENDED):**
- Phase 1-2: 2-3 days (includes 1-2 month GOES-16 download + processing)
- Phase 3: 1 day (web visualization)
- Phase 4: 0.5 days (validation)
- **Total: ~3-4 days**

**Option B - Full dry season GOES-16:**
- Phase 1-2: 4-6 days (includes full 6-month download + processing)
- Phase 3: 1 day
- Phase 4: 0.5 days
- **Total: ~5-7 days**

## Notes

- This prototype focuses on **proving the concept** rather than perfect accuracy
- We can iterate on fog data quality in subsequent tickets
- The key is to validate that the entire pipeline (data → processing → visualization) works
- This de-risks the project by identifying issues early before investing in full implementation

## Follow-up Tickets (after this prototype)

If prototype succeeds:
- Full GOES-16 multi-year climatology processing
- Expand to full California coastal range (not just Bay Area)
- Add additional refinements (topography, soil, invasive species)
- Implement current redwood detection (Layer 1)
- Production-ready web hosting

If prototype reveals issues:
- Revise heuristic thresholds based on ground truth validation
- Investigate alternative fog data sources
- Re-evaluate resolution requirements
