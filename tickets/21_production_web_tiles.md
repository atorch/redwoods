# Production Web Tile Rendering for Redwood Suitability

## Objective

Create a production-quality, browser-based interactive map that renders the redwood habitat suitability layer (Layer 2) as web tiles, initially for the Bay Area with clear path to expand to the full Pacific Coast.

**Key deliverable:** Users can view the "redwoods could grow here" layer in their browser with smooth pan/zoom, without needing QGIS.

## Background

**Current state (COMPLETED):**
- ✓ We have GOES-16 validated suitability raster (`bay_area_redwood_suitable.tif`)
- ✓ Full web interface with tile rendering (`web/index.html`)
- ✓ Data processing pipeline complete (rainfall + GOES-16 fog)
- ✓ 31,069 PNG tiles generated (12.1 MB, zoom 8-14)
- ✓ Leaflet.js + OpenStreetMap basemap implementation
- ✓ Ground truth points validated (8/8 locations)

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

### Map Library: Leaflet.js (Current Implementation)

**Current implementation:** Leaflet.js + OpenStreetMap

**Why this works well:**
- ✓ Simple, lightweight (40KB library)
- ✓ Zero dependencies - no API keys or accounts needed
- ✓ Free unlimited usage (OSM basemap is community-maintained)
- ✓ Battle-tested, used by millions of sites
- ✓ Works great for current scale and scope
- ✓ Easy to deploy anywhere (no vendor lock-in)

**Future enhancement option: Mapbox GL JS**

Consider upgrading to Mapbox GL JS only if you want:
- **Better basemap aesthetics:** Mapbox styles are more polished than OSM
- **Satellite imagery:** See actual forest/terrain under your data layer
- **GPU acceleration:** Smoother pan/zoom (matters at large scale)
- **Vector basemaps:** Crisp text at all zoom levels, map rotation
- **3D/terrain support:** Add hillshade, elevation profiles

**Trade-offs:**
- Requires Mapbox account + API token (free tier: 50K loads/month, then $5-25/month)
- Larger library size (~500KB vs 40KB)
- Vendor dependency (Mapbox service must be available)
- More complex setup and configuration

**Recommendation:** Stick with Leaflet unless you specifically need satellite basemaps or have performance issues with high traffic.

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

### ✅ COMPLETED - Current Implementation (Leaflet + OSM)

- [x] Convert suitability raster to Cloud Optimized GeoTIFF
- [x] Generate tile pyramid (31,069 tiles, 12.1 MB)
- [x] Zoom levels 8-14 for Bay Area
- [x] Save to `tiles/redwood_suitability/` directory (XYZ structure)
- [x] Create web interface with Leaflet.js
- [x] Add OpenStreetMap basemap
- [x] Load tiles from local server
- [x] Style: Green fill for suitable areas, transparency elsewhere
- [x] Suitability layer toggle (on/off)
- [x] Ground truth points (8 locations)
- [x] Zoom to Northern California coast on load
- [x] Legend with data sources
- [x] Color scheme: Green (rgba(34, 139, 34, 0.8)) for suitable areas
- [x] Info panel: GOES-16 validation status, data sources
- [x] Mobile responsive design
- [x] Document viewing instructions in `CLAUDE.md`
- [x] Document tile regeneration process
- [x] Create script: `scripts/13_generate_web_tiles.py`
- [x] Test in multiple browsers

**Current status:** Fully functional web visualization at `http://localhost:8000/web/`

### Future Enhancement: Mapbox GL JS Upgrade (Optional)

**Only do this if you want satellite basemaps or need better performance.**

- [ ] Set up Mapbox account (free tier: 50K loads/month)
- [ ] Add Mapbox access token to environment variables
- [ ] Create new `web/index-mapbox.html` (keep Leaflet version as backup)
- [ ] Install Mapbox GL JS library
- [ ] Replace OpenStreetMap basemap with Mapbox Satellite or Outdoors
- [ ] Update tile loading for Mapbox GL JS API
- [ ] Test API quota monitoring in Mapbox dashboard
- [ ] Document Mapbox setup in README
- [ ] Add fallback to Leaflet if Mapbox quota exceeded

### Future Enhancement: Interactive Features

- [ ] Hover interaction: Show lat/lon, suitability status
- [ ] Click interaction: Display rainfall and fog values at location
- [ ] Export functionality: Download visible area as GeoJSON
- [ ] Permalink: Share specific map view via URL
- [ ] Time series slider: Compare multiple years of fog data

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

### Data (All Complete)
- ✓ `outputs/bay_area_redwood_suitable.tif` (GOES-16 validated)
- ✓ `outputs/bay_area_redwood_suitable_cog.tif` (Cloud Optimized GeoTIFF)
- ✓ `data/redwood_ground_truth_points.csv` (8 locations)
- ✓ `tiles/redwood_suitability/` (31,069 PNG tiles)

### Python Libraries (All Installed)
- ✓ `rio-tiler` - Tile generation
- ✓ `rio-cogeo` - COG conversion
- ✓ `pillow` - Image manipulation
- ✓ `gdal` - Geospatial processing

### External Services (Current Implementation)
- ✓ **Leaflet.js** - Map library (CDN, no account needed)
- ✓ **OpenStreetMap** - Basemap tiles (free, unlimited)
- ✗ **No vendor accounts required!**

### Optional External Services (Future Enhancement)
- Mapbox account (only if upgrading to Mapbox GL JS for satellite basemap)
  - Free tier: 50K loads/month
  - Alternatives: MapTiler, Stadia Maps

## Success Criteria

**All criteria met! ✅**

1. ✓ Can open `http://localhost:8000/web/` and see suitability layer
2. ✓ Can pan and zoom smoothly across Northern California coast
3. ✓ Tiles load quickly (<1 second for visible tiles)
4. ✓ Ground truth points visible and labeled (8 locations)
5. ✓ Visual confirmation: All 8/8 points in green suitable zones (100% validation)
6. ✓ Legend clearly explains criteria (rainfall, fog, geographic)
7. ✓ Mobile-friendly (works on phone browser)
8. ✓ Layer toggle controls work
9. ✓ Info panel shows validation status and data sources

**Next step:** Deploy to production hosting (see Ticket #23)

## Expansion Path: Bay Area → Pacific Coast

### Current (Bay Area) - COMPLETED
- Extent: 37.1-40.6°N, 122.9-121.9°W (Bay Area to Humboldt)
- Input raster: 132×123 pixels at 800m
- Tiles: 31,069 PNG files, 12.1 MB total for zoom 8-14
- Status: ✓ Deployed locally, ready for production hosting

### Future (Pacific Coast)
- Extent: 35.6-42°N (San Simeon to Oregon), ~124.5-121°W
- Input raster: ~800×400 pixels at 800m (estimated)
- Tiles: ~500MB-2GB for zoom 8-14 (estimated)

**Preparation for expansion:**
- [ ] Design tile generation script to accept arbitrary bounding box
- [ ] Make zoom levels configurable
- [ ] Document tile size vs geographic extent trade-offs
- [ ] Consider CDN or cloud storage for larger tile sets

## Status: COMPLETED ✅

**Phase 1 (Bay Area tiles): DONE**

Actual implementation used Leaflet.js + OpenStreetMap instead of Mapbox GL JS, which simplified the process significantly.

**Phase 2 (Pacific Coast expansion): Ready when data is ready**
- Tile generation script (`scripts/13_generate_web_tiles.py`) accepts arbitrary bounding box
- Zoom levels configurable
- Can reuse existing Leaflet interface
- Estimated tiles for full coast: ~100K-200K files, 40-80 MB

## Risks & Mitigations

### Risk 1: Tile Size Too Large
- **Issue:** Too many tiles or tiles too large = slow loading
- **Mitigation:**
  - Start with zoom 8-13 (skip 14 if needed)
  - Compress PNG tiles
  - Use binary data (suitable/not) not continuous values

### Risk 2: External Service Dependencies
- **Issue:** Reliance on external services (basemap, CDN)
- **Status:** MITIGATED - Current implementation uses free, unlimited services
  - Leaflet.js via CDN (can self-host if needed)
  - OpenStreetMap tiles (free, community-maintained)
  - Self-hosted suitability tiles (no external dependency)
- **Optional:** If upgrading to Mapbox in future, monitor quota in dashboard

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

- **Status:** COMPLETED - Full web visualization working locally
- This ticket supersedes the incomplete Phase 3 from Ticket #00
- Implementation uses Leaflet.js + OpenStreetMap (simpler than originally proposed Mapbox)
- Mapbox GL JS remains an optional future enhancement for satellite basemaps
- Next step: Production hosting (see Ticket #23)
- Ticket #20 remains generic placeholder for future Layer 1 + Layer 2 combined view
- Focus is Layer 2 (suitable habitat) only for now
- Layer 1 (current distribution) is future work

## Related Tickets

- **Ticket #23:** Production hosting and domain setup (redwoods.earth)
- **Ticket #22:** Daytime fog detection enhancement
- **Ticket #00:** Original end-to-end prototype (completed)
