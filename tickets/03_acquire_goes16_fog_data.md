# Acquire GOES-16 Fog Data

## Objective
Obtain GOES-16 satellite data to analyze fog patterns, specifically afternoon fog persistence during dry season (May-Oct).

## Tasks
- [ ] Research GOES-16 data access methods
  - UW-Madison Space Science & Engineering Center's Real Earth project
  - NOAA GOES-16 archives
  - Potentially contact fog.today creator for methodology
- [ ] Identify appropriate GOES-16 product for fog detection
  - Low cloud/fog product or raw channels?
  - Temporal resolution available (hourly?)
- [ ] Determine historical time period needed
  - Multiple years for climatology (5-10 years?)
  - Or use most recent complete dry season?
- [ ] Download sample data for pilot area (e.g., SF Bay Area)
- [ ] Document data format, resolution, and artifacts/limitations

## Outputs
- GOES-16 fog/cloud data for study area
- Documentation of data source, product type, and known limitations
- Sample processing script demonstrating data access

## Dependencies
- Need to define geographic extent and temporal scope

## Notes
- fog.today notes potential artifacts and inaccuracies in satellite data
- May need to validate against ground truth (NOAA weather stations)
- High temporal resolution is key advantage (enables "past noon" filtering)

## Investigation Results (2026-04-11)

**Data Access: ✅ CONFIRMED**
- GOES-16 data IS available on public AWS S3: `s3://noaa-goes16` (no authentication)
- Can download with wget/curl: `wget https://noaa-goes16.s3.amazonaws.com/ABI-L2-CMIPC/...`
- Python library available: `goes2go` for easier programmatic access

**Product Selection: ⚠️ IMPORTANT**
- Dedicated **ABI-L2-FLS** (Fog/Low Stratus) product is NOT on public S3
- FLS only available via NOAA CLASS (requires registration, manual download)
- **RECOMMENDED**: Use **ABI-L2-CMIP** (Cloud and Moisture Imagery Product)
  - Available on public S3
  - Can derive fog detection using Brightness Temperature Difference (BTD)

**Fog Detection Method:**
- Calculate BTD = Channel_13 (10.3 µm) - Channel_7 (3.9 µm)
- BTD > 0°C indicates fog/low stratus (water droplets)
- BTD < 0°C indicates ice/high clouds
- Channels available separately in CMIP product

**Data Specifications:**
- Format: netCDF4
- Resolution: 2 km at nadir (CONUS domain)
- Temporal: 5-15 minute intervals
- Coverage: CONUS domain fully covers Bay Area
- File size: ~4 MB per channel per timestep

**Sample Data Downloaded:**
- See `data/goes16_samples/` for Channel 7 and 13 examples
- See `scripts/download_goes16_fog_data.py` for download tool
- See `docs/GOES16_FOG_DATA_GUIDE.md` for complete guide

**Data Volume Estimate:**
- Per dry season (May-Oct): ~105 GB
- 5-year climatology: ~525 GB
- Optimization: subset to Bay Area bounding box, aggregate to hourly/daily
