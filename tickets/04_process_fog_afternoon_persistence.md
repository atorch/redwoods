# Process Fog Afternoon Persistence Metrics

## Objective
Create rasters quantifying fog persistence past noon during dry season (May-Oct) to support 80+ days threshold from historical heuristic.

## Tasks
- [ ] Define "afternoon" time window (e.g., 12pm-6pm local time)
- [ ] For each day in dry season (May-Oct), detect fog presence in afternoon hours
- [ ] Aggregate across multiple years to create climatology
- [ ] Generate metrics:
  - **Primary**: Average days per dry season with fog past noon
  - **Secondary**: Average hours/day of fog by month (May-Oct)
- [ ] Create 80+ day threshold layer for heuristic validation

## Outputs
- `fog_afternoon_days_dry_season.tif` - average days/season with afternoon fog
- `fog_hours_per_day_[month].tif` - monthly fog duration (6 rasters for May-Oct)
- `fog_80day_threshold.tif` - binary layer (1 = meets 80+ day criteria)

## Dependencies
- Ticket #03: Acquire GOES-16 fog data
- Ticket #03b: Investigation and decision on fog metric approach

## Notes
- May need to account for satellite artifacts noted in fog.today documentation
- Consider validating against NOAA weather station fog observations
- Dry season defined as May-October (confirm with literature)

## Implementation Notes (2026-04-11)

**Data Processing Pipeline:**
1. Download CMIP Ch7 and Ch13 for May-Oct, afternoon hours (19:00-01:00 UTC)
2. Calculate BTD for each timestep: `BTD = CMI_ch13 - CMI_ch7`
3. Apply fog threshold: `is_fog = BTD > 0` (or tune threshold, e.g., BTD > 2K)
4. Aggregate to daily: `has_afternoon_fog = any(is_fog)` for each day
5. Count fog days: `sum(has_afternoon_fog)` per dry season
6. Multi-year average: Average across 5-10 years of data

**Prototype Shortcut (for Ticket #00):**
- **Minimal sampling approach:** Process 1-2 peak fog months instead of full dry season
- **Recommended months:** July-August 2024 (Bay Area "Fogust")
- **Alternative:** Same month across years (July 2023 + July 2024) to test variation
- **Data volume:** ~18-36GB instead of ~105GB (full dry season) or ~525GB (5-year climatology)
- **Extrapolation:** Scale fog days from sampled month(s) to estimate full dry season total
  - Example: If July has 15 fog days, and July typically represents 20-25% of dry season fog,
    estimate total dry season ≈ 60-75 days
  - Can validate extrapolation against fog.today seasonal patterns or NOAA station data
- **Purpose:** De-risk the GOES-16 processing methodology without full data download
- **Limitation:** Extrapolation introduces uncertainty, acceptable for prototype validation

**Bay Area Geographic Subset:**
- CONUS domain is 2500×1500 pixels
- Bay Area subset: extract region around lat 37-38°N, lon 121-123°W
- Use GOES fixed grid projection variables (`x`, `y`) to identify indices
- Reduces processing and storage significantly

**File Naming Convention:**
- Input: `OR_ABI-L2-CMIPC-M6C07_G16_s<YYYYDDDHHMMSSs>_e<...>_c<...>.nc`
- `YYYY` = year, `DDD` = day of year, `HH` = hour UTC
- Match Ch7 and Ch13 files by timestamp

**Libraries Needed:**
- `netCDF4` - read GOES netCDF files
- `numpy` - array operations for BTD calculation
- `xarray` - optional, easier netCDF handling
- `rasterio` - write output GeoTIFFs
- `pyproj` - GOES projection to lat/lon conversion

**Validation Strategy:**
- Visual inspection: overlay BTD on basemap, compare with fog.today
- Quantitative: compare fog day counts at NOAA station locations
- Sanity check: coastal areas should have high fog counts, inland low

**See Also:**
- `scripts/download_goes16_fog_data.py` - data download example
- `docs/GOES16_FOG_DATA_GUIDE.md` - complete implementation guide
