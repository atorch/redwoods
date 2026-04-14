# Production Web Tile Rendering for Redwood Suitability

## Objective

Create a production-quality, browser-based interactive map that renders the redwood habitat suitability layer (Layer 2) as web tiles, initially for the Bay Area with clear path to expand to the full Pacific Coast.

**Key deliverable:** Users can view the "redwoods could grow here" layer in their browser with smooth pan/zoom, without needing QGIS.

## Background

**Current state:**
- ✓ We have GOES-16 validated suitability raster (`bay_area_redwood_suitable.tif`)
- ✓ Basic web interface exists (`web/index.html`) but only shows points, not raster
- ✓ Data processing pipeline complete (rainfall + GOES-16 fog)
- ✗ No tile rendering - can't display raster in browser

**Why this matters:**
- QGIS is powerful but requires installation and GIS knowledge
- Web browser is universally accessible
- Tiles enable smooth pan/zoom at multiple scales
- Foundation for expanding to full Pacific Coast

**IMPORTANT - Fog Detection Limitation (v0):**
- Current fog layer uses **nighttime-only** BTD (Brightness Temperature Difference) detection
- GOES-16 BTD (Ch13 - Ch7) only valid at night (06-12 UTC = 11pm-5am PST)
- During daytime, Ch7 (3.9 µm) contains solar reflection that invalidates BTD signal
- This means current fog frequency represents **nighttime/pre-dawn fog only**
- Future enhancement needed: daytime fog detection using visible channels (0.65 µm reflectance)
- For v0 web tiles, we accept this limitation and clearly label fog data as "nighttime fog frequency"
- See separate ticket for daytime fog detection implementation

## Scope

### Phase 1: Bay Area (Initial Implementation)
- Geographic extent: Current Bay Area bounding box (~37.1-38.2°N, ~122.9-121.9°W)
- Input: `outputs/bay_area_redwood_suitable.tif` (GOES-16 validated)
- Output: Tile pyramid for zoom levels 8-14 (regional to neighborhood scale)

### Phase 2: Pacific Coast Expansion (Future)
- Extend to full coastal range (north of San Simeon to Oregon border)
- Requires processing larger PRISM and GOES-16 datasets
- Tiles for zoom levels 6-14 (state to neighborhood scale)

## Technical Approach

### Tile Generation Method: Raster Tiles

**Chosen approach:** `rio-tiler` + AWS Lambda (or local pre-generation)

**Why raster tiles over vector:**
- Suitability is inherently raster data (continuous → binary)
- Simpler to implement than polygonization
- Better performance for large areas
- Can overlay multiple layers (rainfall, fog) later

**Why rio-tiler over gdal2tiles:**
- Modern Python library (integrates with our stack)
- On-demand tile generation option (scales better)
- COG (Cloud Optimized GeoTIFF) support
- Active development, better documentation

**Alternative considered:** `gdal2tiles.py`
- Simpler, widely used
- Pre-generates all tiles (larger storage)
- Good fallback if rio-tiler has issues

### Map Library: Mapbox GL JS

**Chosen approach:** Mapbox GL JS

**Why Mapbox GL JS:**
- Modern, GPU-accelerated rendering
- Excellent performance with raster tiles
- Better styling control than Leaflet
- Vector basemap support (better than OSM raster)
- Free tier: 50,000 map loads/month (sufficient for prototype)

**Alternative considered:** Leaflet.js
- Simpler API, what we're using now
- Good fallback if Mapbox quota issues
- Current basic implementation uses this

### Tile Format

**Format:** XYZ raster tiles (PNG)
- 256×256 pixels per tile
- Transparency for non-suitable areas
- Green color for suitable habitat

**Optimization:**
- Use Web Mercator (EPSG:3857) for tiles
- Reproject from WGS84 (EPSG:4269) once
- Compress PNG tiles (pngquant or similar)
- Serve with appropriate cache headers

## Implementation Tasks

### Task 1: Convert Suitability Raster to COG

- [ ] Install rio-cogeo: `uv add rio-cogeo`
- [ ] Convert `bay_area_redwood_suitable.tif` to Cloud Optimized GeoTIFF
- [ ] Validate with `rio info` and `gdalinfo`
- [ ] Output: `bay_area_redwood_suitable_cog.tif`

**Why COG:** Enables efficient tile extraction without reading entire file

### Task 2: Set Up rio-tiler Tile Server

**Option A: On-demand (development):**
- [ ] Install: `uv add rio-tiler fastapi uvicorn`
- [ ] Create simple FastAPI server serving tiles from COG
- [ ] Test endpoint: `GET /tiles/{z}/{x}/{y}.png`
- [ ] Verify tiles render correctly

**Option B: Pre-generate (production):**
- [ ] Create script using rio-tiler to generate full tile pyramid
- [ ] Generate zoom levels 8-14 for Bay Area
- [ ] Save to `tiles/` directory (XYZ structure)
- [ ] Estimated size: ~50-200 MB for Bay Area

**Decision:** Start with Option B (pre-generate) for simplicity

### Task 3: Update Web Interface

- [ ] Replace current `web/index.html` with Mapbox GL JS version
- [ ] Set up Mapbox account (free tier)
- [ ] Add Mapbox access token (document in README, use env var)
- [ ] Load tiles from local server or `tiles/` directory
- [ ] Style: Green fill for suitable areas, transparency elsewhere

**Map features:**
- [ ] Basemap: Mapbox Outdoors or Satellite
- [ ] Suitability layer toggle (on/off)
- [ ] Ground truth points (existing implementation)
- [ ] Zoom to Bay Area extent on load
- [ ] Legend with data sources

### Task 4: Styling & Polish

- [ ] Color scheme: Green (#228b22) with 60% opacity for suitable areas
- [ ] Hover interaction: Show lat/lon, suitability status
- [ ] Click interaction: Display rainfall and fog values at location
- [ ] Legend: Clear explanation of criteria
- [ ] Info panel: GOES-16 validation status, data sources
- [ ] Mobile responsive design

### Task 5: Documentation & Deployment

- [ ] Update `web/README.md` with tile generation instructions
- [ ] Document tile regeneration process when data updates
- [ ] Add script: `scripts/12_generate_web_tiles.py`
- [ ] Document Mapbox setup in main README
- [ ] Test in multiple browsers (Chrome, Firefox, Safari)

### Task 6: Performance Testing

- [ ] Test load time for initial view
- [ ] Test pan/zoom performance
- [ ] Check tile cache headers
- [ ] Verify tile size (target <50KB per tile)
- [ ] Profile with browser dev tools

## Outputs

### Files to Create

```
tiles/
  └── redwood_suitability/
      ├── 8/           # Zoom level 8 (regional)
      ├── 9/
      ├── 10/
      ├── 11/
      ├── 12/
      ├── 13/
      └── 14/          # Zoom level 14 (neighborhood)

scripts/
  └── 12_generate_web_tiles.py    # Tile generation script

web/
  ├── index.html (UPDATED)        # Mapbox GL JS version
  ├── style.css (NEW)             # Separated styles
  └── app.js (NEW)                # Separated JavaScript

outputs/
  └── bay_area_redwood_suitable_cog.tif  # Cloud Optimized GeoTIFF
```

### Git Considerations

**Commit tiles?**
- ✗ Don't commit `tiles/` directory to git (too large)
- ✓ Add to `.gitignore`
- ✓ Document regeneration process
- ✓ Consider GitHub LFS if tiles needed in repo

## Dependencies

### Data
- ✓ `outputs/bay_area_redwood_suitable.tif` (GOES-16 validated)
- ✓ `data/redwood_ground_truth_points.csv`
- ⚠️ Mapbox access token (free account needed)

### Python Libraries
- `rio-tiler` - Tile generation
- `rio-cogeo` - COG conversion
- `fastapi` + `uvicorn` - Optional tile server
- `pillow` - Image manipulation

### External Services
- Mapbox account (free tier: 50K loads/month)
- Alternative: MapTiler, Stadia Maps if Mapbox issues

## Success Criteria

1. ✓ Can open `http://localhost:8000/` and see suitability layer
2. ✓ Can pan and zoom smoothly across Bay Area
3. ✓ Tiles load quickly (<1 second for visible tiles)
4. ✓ Ground truth points visible and labeled
5. ✓ Visual confirmation: All 4 points in green suitable zones
6. ✓ Legend clearly explains criteria (rainfall, fog, geographic)
7. ✓ Mobile-friendly (works on phone browser)

## Expansion Path: Bay Area → Pacific Coast

### Current (Bay Area)
- Extent: 37.1-38.2°N, 122.9-121.9°W
- Input raster: ~132×123 pixels at 800m
- Tiles: ~50-200 MB for zoom 8-14

### Future (Pacific Coast)
- Extent: 35.6-42°N (San Simeon to Oregon), ~124.5-121°W
- Input raster: ~800×400 pixels at 800m (estimated)
- Tiles: ~500MB-2GB for zoom 8-14 (estimated)

**Preparation for expansion:**
- [ ] Design tile generation script to accept arbitrary bounding box
- [ ] Make zoom levels configurable
- [ ] Document tile size vs geographic extent trade-offs
- [ ] Consider CDN or cloud storage for larger tile sets

## Timeline Estimate (for scoping)

**Phase 1 (Bay Area tiles):**
- COG conversion + tile generation: 2-4 hours
- Mapbox web interface: 4-6 hours
- Styling and testing: 2-3 hours
- **Total: ~8-13 hours** (2-3 work sessions)

**Phase 2 (Pacific Coast expansion):**
- Depends on completing data processing for larger area
- Tile generation: 4-8 hours (larger dataset)
- Testing and optimization: 2-4 hours
- **Total: ~6-12 hours** (after data ready)

## Risks & Mitigations

### Risk 1: Tile Size Too Large
- **Issue:** Too many tiles or tiles too large = slow loading
- **Mitigation:**
  - Start with zoom 8-13 (skip 14 if needed)
  - Compress PNG tiles
  - Use binary data (suitable/not) not continuous values

### Risk 2: Mapbox Quota
- **Issue:** Free tier 50K loads/month might be exceeded
- **Mitigation:**
  - Use Leaflet + OpenStreetMap as fallback
  - Self-host tiles (no external service dependency)
  - Monitor usage in Mapbox dashboard

### Risk 3: Reprojection Issues
- **Issue:** WGS84 → Web Mercator distortion at high latitudes
- **Mitigation:**
  - California coast is low enough latitude (<42°N) - minimal distortion
  - Validate tile alignment with ground truth points
  - Document any projection artifacts

### Risk 4: Stale Tiles
- **Issue:** When data updates, tiles need regeneration
- **Mitigation:**
  - Document clear regeneration workflow
  - Version tiles (e.g., `tiles/v1/`, `tiles/v2/`)
  - Add timestamp to tile metadata

## References

### Similar Projects
- [fog.today](https://fog.today/) - GOES-16 fog visualization (inspiration)
- [Felt Maps](https://felt.com/) - Modern tile-based mapping
- [Protomaps](https://protomaps.com/) - Modern map tiles

### Technical Docs
- [rio-tiler documentation](https://cogeotiff.github.io/rio-tiler/)
- [Mapbox GL JS docs](https://docs.mapbox.com/mapbox-gl-js/)
- [COG specification](https://www.cogeo.org/)
- [XYZ tile format](https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames)

## Follow-Up Tickets

After completing this:
- [ ] Layer toggle system (show/hide rainfall, fog, suitability separately)
- [ ] Click to query: Show exact rainfall/fog values at cursor
- [ ] Time series: Multiple years of fog data comparison
- [ ] Export functionality: Download suitable areas as GeoJSON
- [ ] Permalink: Share specific map view via URL

## Notes

- This ticket supersedes the incomplete Phase 3 from Ticket #00
- Ticket #20 remains generic placeholder for future Layer 1 + Layer 2 combined view
- Focus is Layer 2 (suitable habitat) only for now
- Layer 1 (current distribution) is future work
