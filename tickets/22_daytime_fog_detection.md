# Daytime Fog Detection for Redwood Habitat Suitability

**PRIORITY: HIGH** - Critical for validating original heuristic

**STATUS UPDATE (2026-04-13):**
Current v0 implementation shows 99.8% of pixels meet fog criterion, making it essentially ineffective as a discriminating factor. Investigation (see `FOG_THRESHOLD_INVESTIGATION.md`) suggests this may be due to nighttime-only sampling capturing pre-dawn marine layer (which is nearly universal along California coast) rather than the ecologically-critical "fog past noon" persistence specified in the original heuristic.

## Objective

Implement daytime fog detection using GOES-16 visible channel reflectance to complement the current nighttime BTD-based fog detection, enabling full 24-hour fog frequency analysis and proper validation of the "fog past noon 80 days/season" criterion.

## Background

**Current limitation:**
- Our current fog detection uses BTD (Brightness Temperature Difference): BT_Ch13 (10.3 µm) - BT_Ch7 (3.9 µm)
- BTD **only works at night** because Ch7 (3.9 µm) contains solar reflection during daytime
- Current implementation samples 06-12 UTC (11pm-5am PST) = nighttime/pre-dawn fog only
- This means we're missing daytime fog, particularly the critical "fog past noon" criterion from the original heuristic

**Why this matters for redwood habitat:**
- Original heuristic specifically mentions "fog past noon" as important
- Coastal redwoods rely on summer fog for moisture during dry season
- Daytime fog persistence (especially afternoon fog) is ecologically significant
- Current nighttime-only detection may underestimate fog importance in some areas

**References:**
- NOAA/CIMSS GOES-16 Fog Detection Best Practices
- "BTD works best at night; daytime requires visible channel analysis"
- Standard operational fog products use different algorithms for day vs night

## Technical Approach

### Daytime Fog Detection Method: Visible Channel Reflectance

**Primary approach:** GOES-16 Channel 2 (0.65 µm visible red)

**How it works:**
- Fog/low clouds have high reflectance in visible channels (appear bright)
- Use reflectance threshold + texture analysis to distinguish fog from higher clouds
- Combine with IR brightness temperature to distinguish fog (cold) from land (warm)
- Time of day: 19-00 UTC (12pm-5pm PST) = afternoon fog window

**Algorithm (simplified):**
```
Daytime fog detected when:
1. Ch2 reflectance > threshold (e.g., 0.4-0.6)
2. BT_Ch13 < threshold (e.g., 280K = low cloud)
3. BT_Ch13 - BT_Ch14 < small (uniform cloud top)
4. Local time 12pm-5pm PST (afternoon fog)
```

**Challenges:**
- Visible channels only available during daytime (need solar illumination)
- Must distinguish fog from other bright surfaces (land, high clouds)
- Threshold tuning required for coastal California conditions
- More complex than nighttime BTD

### Combined Day/Night Fog Frequency

**Integration strategy:**
- Nighttime detection: 06-12 UTC using BTD (current implementation)
- Daytime detection: 19-00 UTC using visible reflectance (this ticket)
- Combine into single fog frequency layer: days with fog detected in either window
- Alternative: separate "nighttime fog days" and "daytime fog days" layers

**Output:**
- Total fog days per dry season (nighttime OR daytime)
- Optional: separate nighttime/daytime fog frequency rasters
- Updated suitability layer using combined fog frequency

## Implementation Tasks

### Task 1: Research and Algorithm Design

- [ ] Review NOAA/CIMSS daytime fog detection algorithms
- [ ] Study operational fog products (NESDIS, GOES-R Algorithm Working Group)
- [ ] Determine optimal visible channel (Ch2 0.65 µm vs Ch3 0.86 µm)
- [ ] Define reflectance and temperature thresholds for coastal CA
- [ ] Design validation approach using ground truth

### Task 2: GOES-16 Visible Channel Data Access

- [ ] Verify Ch2 (0.65 µm) availability in CONUS mesoscale sectors
- [ ] Update download script to include Ch2 alongside Ch7/Ch13
- [ ] Modify download to use daytime hours (19-00 UTC)
- [ ] Estimate additional storage requirements (~1.5x current)

### Task 3: Daytime Fog Detection Implementation

- [ ] Create `scripts/13_process_daytime_fog.py`
- [ ] Implement visible reflectance calculation from raw Ch2 data
- [ ] Implement multi-threshold fog detection algorithm
- [ ] Apply same reprojection and regridding as nighttime detection
- [ ] Output: daytime fog frequency raster (800m, WGS84)

### Task 4: Validation

- [ ] Compare daytime fog detections with webcam images (if available)
- [ ] Cross-reference with NOAA operational fog products
- [ ] Validate against known fog climatology for Bay Area
- [ ] Check consistency: do daytime and nighttime fog overlap spatially?

### Task 5: Integration with Suitability Layer

- [ ] Combine nighttime and daytime fog frequency
- [ ] Update `scripts/04_combine_suitability.py` to use combined fog
- [ ] Regenerate suitability raster with day+night fog
- [ ] Compare with nighttime-only version (how much difference?)

### Task 6: Documentation

- [ ] Document daytime fog algorithm in code comments
- [ ] Update README with day+night fog detection explanation
- [ ] Add visualization comparing nighttime-only vs combined fog
- [ ] Update web interface legend to reflect combined fog data

## Dependencies

### Data
- GOES-16 Channel 2 (0.65 µm) mesoscale sector data
- Existing Ch7/Ch13 nighttime data (already downloaded)
- Same temporal coverage: May, June, July, August, September

### Python Libraries
- Existing: `netCDF4`, `numpy`, `rasterio`, `pyproj`
- May need: additional GOES processing utilities

### Research
- NOAA/CIMSS algorithm documentation
- Coastal California fog climatology literature
- Validation data sources (webcams, surface obs)

## Success Criteria

1. ✓ Daytime fog detection algorithm implemented and documented
2. ✓ Validation shows reasonable agreement with known fog patterns
3. ✓ Combined day+night fog frequency layer generated
4. ✓ Suitability layer updated with combined fog data
5. ✓ Visual comparison shows improvement over nighttime-only
6. ✓ Web interface updated to display combined fog frequency
7. ✓ Documentation clearly explains day vs night detection methods

## Timeline Estimate

**Research and algorithm design:** 4-6 hours
- Literature review
- Algorithm specification
- Threshold determination

**Implementation:** 8-12 hours
- Download visible channel data
- Code daytime detection algorithm
- Validation and tuning
- Integration with existing pipeline

**Total:** ~12-18 hours (3-4 work sessions)

## Outputs

### Files to Create

```
scripts/
  └── 13_process_daytime_fog.py        # Daytime fog detection

outputs/
  ├── bay_area_fog_nighttime.tif       # Nighttime fog (current)
  ├── bay_area_fog_daytime.tif         # Daytime fog (new)
  └── bay_area_fog_combined.tif        # Day+night combined (new)

data/goes16_multi_week_daytime/        # Daytime visible channel data
```

### Updated Files

```
scripts/04_combine_suitability.py      # Use combined fog frequency
scripts/12_download_multi_week_goes16.py  # Add Ch2 download option
README.md                               # Update fog detection explanation
web/index.html                          # Update legend/metadata
```

## Risks & Mitigations

### Risk 1: Daytime Algorithm More Complex
- **Issue:** Visible channel fog detection harder than BTD
- **Mitigation:**
  - Start with simple threshold approach
  - Use existing NOAA algorithms as reference
  - Accept lower accuracy for v1, iterate

### Risk 2: Threshold Tuning Difficult
- **Issue:** Reflectance thresholds may not generalize across region
- **Mitigation:**
  - Test on Bay Area first (known fog climatology)
  - Compare with operational fog products
  - Consider adaptive thresholds by location

### Risk 3: Additional Data Storage
- **Issue:** Visible channel data adds ~50% more storage
- **Mitigation:**
  - Download only Ch2 for daytime hours (not full day)
  - Clean up test data regularly
  - Compress NetCDF files if needed

### Risk 4: Day+Night Integration Unclear
- **Issue:** How to combine nighttime and daytime fog frequencies?
- **Mitigation:**
  - Default: logical OR (fog detected in either window)
  - Alternative: separate layers for different use cases
  - Document assumptions clearly

## References

### NOAA/CIMSS Documentation
- [GOES-R Fog/Low Stratus Algorithm](https://www.star.nesdis.noaa.gov/goesr/documents/ATBDs/Baseline/ATBD_GOES-R_Fog_v2.5_July2012.pdf)
- [Daytime Fog Detection Best Practices](https://cimss.ssec.wisc.edu/satellite-blog/archives/category/fog)

### Scientific Literature
- Bendix et al. (2006): "Ground Fog Detection from Space"
- Cermak & Bendix (2008): "A novel approach to fog/low stratus detection using Meteosat 8 data"
- Ellrod (1995): "Advances in the detection and analysis of fog at night using GOES multispectral infrared imagery"

### Operational Products
- [NOAA GOES Fog Product](https://www.star.nesdis.noaa.gov/goes/index.php)
- [NWS Fog Forecasting](https://www.weather.gov/ajk/FogForecastingChallenges)

## Follow-Up Tickets

After completing this:
- [ ] Expand daytime fog detection to full Pacific Coast
- [ ] Time series analysis: fog trends over multiple years
- [ ] Fog climatology visualization (seasonal patterns)
- [ ] Integration with climate model projections (future fog?)

## Notes

- This ticket addresses the limitation noted in Ticket #21 (Production Web Tiles)
- Current v0 web tiles use nighttime-only fog; this enables v1 with full fog data
- Particularly important for "fog past noon" criterion in original heuristic
- May reveal different spatial patterns than nighttime fog alone
