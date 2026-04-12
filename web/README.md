# Redwood Habitat Suitability Web Visualization

## Quick Start

### Option 1: View in QGIS (Recommended for Prototype)

The fastest way to visualize the results:

```bash
# Install QGIS if not already installed
# On Ubuntu/Debian:
sudo apt-get install qgis

# Launch QGIS
qgis
```

Then in QGIS:
1. **Add the suitability layer:**
   - Layer → Add Layer → Add Raster Layer
   - Navigate to: `outputs/bay_area_redwood_suitable.tif`
   - Style: Use "Paletted/Unique values" with green for suitable (value=1)

2. **Add the ground truth points:**
   - Layer → Add Layer → Add Delimited Text Layer
   - File: `data/redwood_ground_truth_points.csv`
   - Geometry: Point coordinates, X=longitude, Y=latitude
   - Style: Red circles

3. **Add context layers (optional):**
   - `outputs/bay_area_rainfall_total.tif` - Continuous rainfall values
   - `outputs/bay_area_fog_days_estimate.tif` - Fog days estimate
   - Add OpenStreetMap basemap via QuickMapServices plugin

### Option 2: Web Browser (Basic)

View ground truth points on an interactive map:

```bash
# From the redwoods directory
cd web
python3 -m http.server 8000
```

Then open in your browser:
```
http://localhost:8000/
```

**Note:** The current web version shows ground truth points and the study area boundary, but does not yet render the GeoTIFF raster. Viewing rasters in the browser requires converting to tiles (see "Future Enhancements" below).

## Files

### Outputs (in `../outputs/`)

**Final suitability layer:**
- `bay_area_redwood_suitable.tif` - Binary raster (1=suitable, 0=not suitable)

**Component layers:**
- `bay_area_rainfall_total.tif` - Wet season rainfall (continuous, inches)
- `bay_area_rainfall_20in.tif` - Rainfall threshold (binary, ≥20")
- `bay_area_fog_days_estimate.tif` - Fog days estimate (continuous, MOCK DATA)
- `bay_area_fog_80days.tif` - Fog threshold (binary, ≥80 days)

**Metadata:**
- `bay_area_bbox.json` - Bounding box for study area

### Data Sources

**Ground truth:**
- `../data/redwood_ground_truth_points.csv` - 4 known redwood locations

**Input data:**
- `../data/prism_ppt_us_30s_*` - PRISM monthly precipitation normals

## Validation Results

✓ **All 4 ground truth points validated as suitable habitat**

1. Redwood Regional Park, Tres Sendas bridge (37.8237, -122.1758)
2. Redwood Regional Park, Old Church (37.8111, -122.1561)
3. Muir Woods, Bridge 2 (37.8959, -122.5755)
4. The Elbow Tree (37.4106, -122.3594)

## Summary Statistics

**Suitable habitat area:**
- 5,397 pixels (44.6% of study area)

**Suitable habitat characteristics:**
- Rainfall: 20.0 - 53.0 inches (mean: 27.1")
- Fog days: 80.0 - 140.0 days (mean: 111.9 days)

## Important Notes

### ⚠️ Prototype Limitations

1. **Mock fog data:** The fog layer is based on a simple coastal proximity model, NOT real satellite data. This proves the pipeline works but is not scientifically accurate.

2. **Geographic scope:** Bay Area only (~37.1-38.2°N, ~122.9-121.9°W)

3. **Resolution:** 800m (PRISM native resolution)

4. **Temporal:** Single climatological period (PRISM 1991-2020 normals)

### For Production Use

To create a scientifically rigorous version:

1. **Replace mock fog with GOES-16 data:**
   - Download Ch7 + Ch13 for multiple dry seasons (May-Oct)
   - Calculate BTD (Brightness Temperature Difference)
   - Count actual afternoon fog days
   - Average across 5-10 years for climatology

2. **Expand geographic scope:**
   - Full California coast (north of San Simeon to Oregon border)
   - Requires processing larger PRISM and GOES-16 datasets

3. **Add refinements:**
   - Topography (elevation, slope, aspect)
   - Soil characteristics
   - Distance to streams/watersheds
   - Urban mask (current development)

4. **Generate web tiles:**
   - Convert GeoTIFFs to tile pyramid (zoom levels 8-16)
   - Use gdal2tiles or rio-tiler
   - Host tiles for web map

## Future Enhancements

### Near-term (Complete prototype):
- [ ] Download real GOES-16 sample data
- [ ] Implement BTD fog detection
- [ ] Generate tile pyramid for web display
- [ ] Add layer toggle controls
- [ ] Click to query values at location

### Long-term (Production):
- [ ] Multi-year GOES-16 climatology
- [ ] Full California coastal extent
- [ ] Add topographic refinements
- [ ] Validate against historical redwood maps
- [ ] Implement Layer 1 (current redwood detection)
- [ ] Host on public server

## References

**Heuristic source:**
> "If the place is north of San Simeon, fog currently lasts past noon 80 days/dry season,
> and the place has more than 20 inches/year of rain in the wet season, it had redwoods in 1750."

**Data sources:**
- PRISM Climate Group: https://prism.oregonstate.edu/
- NOAA GOES-16: https://registry.opendata.aws/noaa-goes/
- Ground truth: User-provided redwood locations

## Scripts

All processing scripts are in `../scripts/`:
- `01_process_bay_area_rainfall.py` - Process PRISM wet season rainfall
- `02_download_goes16_sample_days.py` - Download GOES-16 fog data
- `03_create_mock_fog_layer.py` - Create mock fog layer (prototype only)
- `04_combine_suitability.py` - Combine criteria into final layer

Run with:
```bash
uv run python scripts/<script_name>.py
```

See `../tickets/00_end_to_end_prototype.md` for detailed documentation.
