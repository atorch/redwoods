# Redwood Habitat Suitability Web Visualization

## Quick Start - View Interactive Map

### Web Browser (Recommended - Full Visualization) ⭐

View the suitability layer as an interactive web map with tiles:

```bash
# IMPORTANT: Run server from PROJECT ROOT, not from web/ directory
cd /home/adrian/redwoods
python3 -m http.server 8000
```

Then open in your browser:
```
http://localhost:8000/web/
# or
http://0.0.0.0:8000/web/
```

**⚠️ Critical:** The URL must end with `/web/` (not just the root `/`)

**What you'll see:**
- ✅ Green overlay showing suitable redwood habitat (60.6% of Bay Area)
- ✅ 4 ground truth validation points (red markers)
- ✅ Layer toggle control (top-left)
- ✅ Interactive pan/zoom (zoom levels 8-14)
- ⚠️ Warning about v0 nighttime-only fog limitation

**Technical details:**
- Uses 4,125 pre-generated PNG tiles (1.9 MB total)
- Leaflet.js for map rendering
- Tiles served from `../tiles/redwood_suitability/`
- Server must run from project root for relative paths to work

### Alternative: View in QGIS

For detailed analysis and layer inspection:

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

3. **Add component layers (optional):**
   - `outputs/bay_area_rainfall_total.tif` - Continuous rainfall values
   - `outputs/bay_area_fog_days_goes16.tif` - GOES-16 nighttime fog frequency
   - Add OpenStreetMap basemap via QuickMapServices plugin

## Outputs (in `../outputs/`)

### Final suitability layer:
- `bay_area_redwood_suitable.tif` - Binary raster (1=suitable, 0=not suitable)
- `bay_area_redwood_suitable_cog.tif` - Cloud Optimized GeoTIFF for tile generation

### Component layers:
- `bay_area_rainfall_total.tif` - Wet season rainfall (continuous, inches)
- `bay_area_rainfall_20in.tif` - Rainfall threshold (binary, ≥20")
- `bay_area_fog_days_goes16.tif` - Nighttime fog days (continuous, GOES-16 satellite)
- `bay_area_fog_80days_goes16.tif` - Fog threshold (binary, ≥80 days)

### Web tiles:
- `../tiles/redwood_suitability/{z}/{x}/{y}.png` - 4,125 tiles, zoom 8-14

**⚠️ Important:** The `tiles/` directory is excluded from git (see `.gitignore`). Regenerate with:
```bash
uv run python scripts/13_generate_web_tiles.py
```

## Data Sources

**Ground truth:**
- `../data/redwood_ground_truth_points.csv` - 4 known redwood locations

**Input data:**
- `../data/prism_ppt_us_30s_*` - PRISM monthly precipitation normals (1991-2020)
- `../data/goes16_multi_week/*.nc` - GOES-16 satellite data (May-Sep 2024, nighttime)

## Validation Results

✓ **All 4 ground truth points validated as suitable habitat**

1. Redwood Regional Park, Tres Sendas bridge (37.8237, -122.1758)
2. Redwood Regional Park, Old Church (37.8111, -122.1561)
3. Muir Woods, Bridge 2 (37.8959, -122.5755)
4. The Elbow Tree (37.4106, -122.3594)

## Summary Statistics

**Suitable habitat area:**
- 7,334 pixels (60.6% of study area)
- Resolution: 800m

**Suitable habitat characteristics:**
- Rainfall: 20.0 - 56.8 inches (mean: 28.0")
- Nighttime fog: 124.9 - 184.0 days (mean: 169.8 days)

**Fog detection:**
- Method: GOES-16 BTD (Brightness Temperature Difference)
- Channels: Ch13 (10.3 µm) - Ch7 (3.9 µm)
- Time window: Nighttime only (06-12 UTC = 11pm-5am PST)
- Sample period: 4 weeks across dry season (May, June, August, September 2024)
- Total observations: 392 nighttime samples

## Important Notes

### ⚠️ v0 Limitations

1. **Nighttime fog only:**
   - Current fog detection uses BTD which ONLY works at night
   - Ch7 (3.9 µm) contains solar reflection during daytime, invalidating BTD
   - This captures nighttime/pre-dawn fog (11pm-5am PST)
   - **Missing:** Daytime fog, especially "fog past noon" from original heuristic
   - **Future enhancement:** See `tickets/22_daytime_fog_detection.md`

2. **Limited temporal coverage:**
   - 4 weeks sampled from 2024 dry season
   - Extrapolated to full 184-day dry season
   - Production would use multi-year climatology (5-10 years)

3. **Geographic scope:** Bay Area only (~37.1-38.2°N, ~122.9-121.9°W)

4. **Resolution:** 800m (PRISM native resolution)

### Data Quality

✓ **GOES-16 satellite data (real)** - Not mock/estimated
✓ **PRISM climate normals (30-year)** - Authoritative rainfall data
✓ **Proper reprojection** - GOES fixed grid → WGS84 → Web Mercator
✓ **Scientifically validated** - Published BTD fog detection method
⚠️ **Nighttime-only limitation** - See Ticket #22 for daytime enhancement

## Regenerating Web Tiles

If you update the suitability layer and need to regenerate tiles:

```bash
# From project root
uv run python scripts/13_generate_web_tiles.py
```

This will:
1. Convert `outputs/bay_area_redwood_suitable.tif` to COG (if needed)
2. Generate 4,125 PNG tiles for zoom levels 8-14
3. Save to `tiles/redwood_suitability/`

**Note:** Tiles are not committed to git (excluded in `.gitignore`)

## Scripts

All processing scripts are in `../scripts/`:

**Data download and processing:**
- `01_process_bay_area_rainfall.py` - Process PRISM wet season rainfall
- `09_download_week_goes16.py` - Download 1 week GOES-16 sample
- `12_download_multi_week_goes16.py` - Download 4 weeks GOES-16 (nighttime)

**Fog detection:**
- `11_create_real_fog_layer.py` - Process GOES-16 nighttime fog (BTD method)

**Suitability calculation:**
- `04_combine_suitability.py` - Combine criteria into final layer

**Web visualization:**
- `13_generate_web_tiles.py` - Generate web tiles from suitability raster

Run with:
```bash
uv run python scripts/<script_name>.py
```

## Troubleshooting

### Tiles not loading (404 errors)

**Problem:** You started the HTTP server from the `web/` directory
```bash
cd web  # ← WRONG
python3 -m http.server 8000
```

**Solution:** Start from project root
```bash
cd /home/adrian/redwoods  # ← CORRECT
python3 -m http.server 8000
# Then navigate to http://localhost:8000/web/
```

The tiles are at `tiles/redwood_suitability/`, and the HTML uses relative path `../tiles/`. This only works when the server root is the project root.

### Map shows only points, no green overlay

1. Check that tiles exist:
   ```bash
   ls tiles/redwood_suitability/9/
   ```

2. If missing, regenerate:
   ```bash
   uv run python scripts/13_generate_web_tiles.py
   ```

3. Check browser console for tile loading errors

4. Verify you're at `/web/` URL (not just `/`)

## Future Enhancements

### Completed ✓
- [x] Download real GOES-16 satellite data
- [x] Implement BTD fog detection
- [x] Generate tile pyramid for web display
- [x] Add layer toggle controls
- [x] Interactive web visualization

### Near-term:
- [ ] Daytime fog detection using visible channels (Ticket #22)
- [ ] Multi-year GOES-16 climatology
- [ ] Click to query rainfall/fog values at location
- [ ] Export suitable areas as GeoJSON

### Long-term (Production):
- [ ] Full California coastal extent
- [ ] Add topographic refinements (elevation, slope, aspect)
- [ ] Validate against historical redwood maps
- [ ] Implement Layer 1 (current redwood distribution detection)
- [ ] Host on public server with CDN

## References

**Heuristic source:**
> "If the place is north of San Simeon, fog currently lasts past noon 80 days/dry season,
> and the place has more than 20 inches/year of rain in the wet season, it had redwoods in 1750."

**Data sources:**
- PRISM Climate Group: https://prism.oregonstate.edu/
- NOAA GOES-16: https://registry.opendata.aws/noaa-goes/
- GOES-16 BTD Fog Detection: NOAA/CIMSS algorithm documentation
- Ground truth: User-provided redwood locations

**Documentation:**
- See `../tickets/21_production_web_tiles.md` for web tile implementation details
- See `../tickets/22_daytime_fog_detection.md` for future daytime fog enhancement
- See `../GOES16_REAL_FOG_RESULTS.md` for GOES-16 validation results
