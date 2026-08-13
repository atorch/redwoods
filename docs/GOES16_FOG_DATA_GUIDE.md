# GOES-16 Fog Data Access Guide

## Summary

**YES, you can download GOES-16 fog data using wget/curl!** The data is publicly available on AWS S3 with no authentication required.

## Key Findings

### 1. Fog/Low Stratus (FLS) Product Status ⚠️

The dedicated **ABI-L2-FLS** (Fog/Low Stratus) product is **NOT available on the public AWS S3 bucket**. It is only available through:
- NOAA CLASS (Comprehensive Large Array-data Stewardship System)
- Requires registration and manual download

### 2. Alternative Approach: Cloud and Moisture Imagery Product (CMIP) ✅

**RECOMMENDED**: Use **ABI-L2-CMIP** (Cloud and Moisture Imagery Product) to derive fog detection yourself.

This product IS available on AWS S3 and can be downloaded programmatically with wget/curl!

## Data Access Methods

### Method 1: Direct wget/curl (Works!)

```bash
# Example: Download Channel 7 (3.9 µm) data
wget https://noaa-goes16.s3.amazonaws.com/ABI-L2-CMIPC/2024/200/00/OR_ABI-L2-CMIPC-M6C07_G16_s20242000001180_e20242000003565_c20242000004044.nc

# Example: Download Channel 13 (10.3 µm) data
wget https://noaa-goes16.s3.amazonaws.com/ABI-L2-CMIPC/2024/200/00/OR_ABI-L2-CMIPC-M6C13_G16_s20242000001180_e20242000003553_c20242000004026.nc
```

**File path structure:**
```
ABI-L2-CMIPC/<YEAR>/<DAY_OF_YEAR>/<HOUR>/OR_ABI-L2-CMIPC-M6C<CHANNEL>_G16_s<timestamp>_e<timestamp>_c<timestamp>.nc
```

**Example:**
- Product: `ABI-L2-CMIPC` (CONUS domain, covers Bay Area)
- Year: `2024`
- Day of year: `200` (July 18)
- Hour: `00` (midnight UTC)
- Channel: `C07` (Channel 7, 3.9 µm)

### Method 2: goes2go Python Library (Recommended for automation)

```bash
# Install
uv add goes2go

# Python usage
from goes2go import GOES

# Download Channel 7 (3.9 µm) for CONUS
G = GOES(satellite=16, product="ABI-L2-CMIP", domain='C')
ds = G.nearesttime('2024-07-18 12:00')

# Download time range
G.timerange(start='2024-07-01 12:00', end='2024-07-01 18:00')
```

### Method 3: AWS CLI

```bash
# List available files
aws s3 ls s3://noaa-goes16/ABI-L2-CMIPC/2024/200/12/ --no-sign-request

# Download
aws s3 cp s3://noaa-goes16/ABI-L2-CMIPC/2024/200/12/OR_ABI-L2-CMIPC-M6C07_G16_<timestamp>.nc . --no-sign-request
```

## Fog Detection Methodology

### Brightness Temperature Difference (BTD) Method

Since the dedicated FLS product is not publicly available, we can derive fog detection using:

**Formula:** BTD = BT_Channel13 - BT_Channel7

**Channels needed:**
- **Channel 7**: 3.9 µm (shortwave infrared)
- **Channel 13**: 10.3 µm (longwave infrared)

**Interpretation:**
- **BTD > 0°C**: Fog/low stratus (water droplets reflect differently at these wavelengths)
- **BTD < 0°C**: Ice clouds/high clouds

**Physical basis:**
- Fog has small water droplets that emit less at 3.9 µm than 11 µm due to emissivity differences
- High clouds (ice) have similar temperatures at both wavelengths

### Alternative: Nighttime Microphysics RGB

For more advanced fog detection:
- **Red**: Channel 15 - Channel 13 (12.3 µm - 10.3 µm) — cloud thickness
- **Green**: Channel 13 - Channel 7 (10.3 µm - 3.9 µm) — ice vs water
- **Blue**: Channel 13 (10.3 µm) — cloud height

Cyan/aqua colors indicate fog/low stratus.

## Data Specifications

### File Format
- **Format**: netCDF4
- **Resolution**: 2 km at nadir (CONUS domain)
- **Temporal resolution**: 5-15 minutes
- **Coverage**: Continental US (includes Bay Area)

### File Structure
```python
import netCDF4 as nc
ds = nc.Dataset('OR_ABI-L2-CMIPC-M6C07_G16_*.nc')

# Key variable
cmi = ds.variables['CMI']  # Brightness temperature (Kelvin)
# Shape: (1500, 2500) for CONUS
# Units: K (Kelvin)
# Scale and offset applied automatically by netCDF4

# Coordinates
x = ds.variables['x'][:]  # GOES fixed grid x-coordinate
y = ds.variables['y'][:]  # GOES fixed grid y-coordinate
```

## For the Redwoods Project

### Requirements from Heuristic

From `README.md`:
> "Fog lasts past noon 80+ days during dry season (May-Oct)"

### Processing Workflow

1. **Download CMIP data** for May-October (multiple years for climatology)
   - Channels 7 and 13
   - Afternoon hours (12:00-18:00 local time = ~19:00-01:00 UTC)
   - CONUS domain (covers Bay Area)

2. **Calculate BTD** for each timestep
   - BTD = Ch13 - Ch7
   - Threshold: BTD > 0°C indicates fog

3. **Detect afternoon fog** per day
   - Binary: Was fog present after noon on this day?
   - Aggregate by location (pixel)

4. **Count fog days** per dry season
   - Sum fog days for May-October
   - Average across multiple years

5. **Create raster**: "Days per dry season with afternoon fog"
   - Threshold at 80+ days for redwood suitability

### Data Volume Estimate

**Per day** (May-Oct, 6 months = 183 days):
- 2 channels × 6 hours × 12 images/hour = 144 files/day
- File size: ~4 MB each
- Total per day: ~576 MB

**Per year** (May-Oct):
- 183 days × 576 MB = ~105 GB

**For climatology** (5 years):
- 5 years × 105 GB = **~525 GB**

**Optimization strategies:**
- Download only Bay Area bounding box (subset)
- Use daily/hourly aggregates instead of all 5-minute data
- Process and delete raw files after computing BTD

## Bay Area Specific Notes

### Geographic Coverage

GOES-16 CONUS domain covers the entire Bay Area. The Bay Area is at approximately:
- Latitude: 37-38°N
- Longitude: 121-123°W

GOES-16 is positioned at 75.2°W, giving excellent coverage of California coast.

### Validation Resources

- **fog.today** (https://fog.today/): Uses GOES-16/18 data for Bay Area fog
- **bayfog.app**: Another GOES-based Bay Area fog tracker
- NOAA weather stations: Point validation data

## Next Steps

1. ✅ **Confirm data access** (DONE - wget works!)
2. **Test BTD calculation** on sample data
3. **Validate fog detection** against ground truth (NOAA stations, fog.today)
4. **Develop processing pipeline** for multi-year aggregation
5. **Optimize storage/compute** for 500+ GB dataset

## Resources

- [NOAA GOES-16 AWS Registry](https://registry.opendata.aws/noaa-goes/)
- [goes2go Documentation](https://goes2go.readthedocs.io/)
- [AWS Open Data Docs](https://github.com/awslabs/open-data-docs/blob/main/docs/noaa/noaa-goes16/README.md)
- [Fog Detection Using GOES-16](http://cimss.ssec.wisc.edu/goes/blog/archives/23268)
- [CIMSS Night Fog BTD Guide](https://cimss.ssec.wisc.edu/goes/OCLOFactSheetPDFs/ABIQuickGuide_NightFogBTD.pdf)

## Conclusion

**De-risking assessment for fog tickets:**

✅ **CAN download via wget**: Yes! No manual download needed.

✅ **Data availability**: Publicly accessible on AWS S3, no authentication required.

⚠️ **Processing required**: Need to calculate BTD from raw channels (not pre-computed FLS product).

✅ **Bay Area coverage**: Fully covered by CONUS domain.

⚠️ **Data volume**: Large (~500 GB for 5-year climatology), but manageable with subsetting.

**Recommendation**: Proceed with CMIP-based fog detection approach. The main risk is computational/storage, not data access.
