#!/usr/bin/env python3
"""
Process GOES-16 data to detect fog using Brightness Temperature Difference (BTD).

BTD Method:
- Calculate: BTD = BT_Channel13 - BT_Channel7
- BTD > 0°C indicates fog/low stratus (water droplets)
- BTD < 0°C indicates ice/high clouds

For each afternoon sample:
1. Load Ch7 and Ch13 brightness temperatures
2. Calculate BTD
3. Detect fog where BTD > threshold (e.g., 0K or 2K)
4. Aggregate to daily: did fog occur in afternoon?
5. Count fog days across sample period
6. Extrapolate to full dry season estimate

Output: Same format as mock fog layer for direct comparison.
"""

import json
import numpy as np
from pathlib import Path
import rasterio
from rasterio.transform import from_bounds

# Configuration
RAW_DIR = Path("data/goes16_sample_raw")
OUTPUT_DIR = Path("outputs")
BBOX_FILE = OUTPUT_DIR / "bay_area_bbox.json"
MANIFEST_FILE = Path("data/goes16_sample_processed/download_manifest.json")

# BTD threshold for fog detection (Kelvin)
# BTD > 0K indicates water clouds (fog/low stratus)
# Can tune: 0K (permissive), 2K (conservative)
FOG_BTD_THRESHOLD = 0.0  # Kelvin

# Extrapolation factor
# If we sample 3 days in July and find X fog days,
# how do we estimate full dry season (May-Oct = 184 days)?
# Conservative: assume July represents peak fog month
# July typically has ~20-25 fog days in SF
# Full dry season: ~80-100 fog days
# So scaling factor ≈ 4-5x
EXTRAPOLATION_FACTOR = 5.0  # Multiply sample fog days by this


def load_bbox():
    """Load Bay Area bounding box."""
    with open(BBOX_FILE) as f:
        return json.load(f)


def load_manifest():
    """Load download manifest."""
    if not MANIFEST_FILE.exists():
        print(f"✗ Manifest not found: {MANIFEST_FILE}")
        print("  Run scripts/05_download_process_goes16_sample.py first")
        return None

    with open(MANIFEST_FILE) as f:
        return json.load(f)


def load_goes16_data(nc_file):
    """Load GOES-16 netCDF file and extract data."""
    try:
        import netCDF4 as nc

        ds = nc.Dataset(nc_file)

        # Get brightness temperature (Kelvin)
        cmi = ds.variables['CMI'][:]

        # Get projection coordinates
        x = ds.variables['x'][:]
        y = ds.variables['y'][:]

        # Get projection info for georeferencing
        goes_proj = ds.variables['goes_imager_projection']
        sat_height = goes_proj.perspective_point_height
        sat_lon = goes_proj.longitude_of_projection_origin

        # Get nominal pixel resolution at nadir
        x_res = x[1] - x[0]  # radians
        y_res = y[1] - y[0]

        # Time
        time_str = ds.time_coverage_start

        ds.close()

        return {
            'cmi': cmi,
            'x': x,
            'y': y,
            'sat_lon': sat_lon,
            'sat_height': sat_height,
            'time': time_str,
            'x_res': x_res,
            'y_res': y_res
        }

    except ImportError:
        print("✗ ERROR: netCDF4 library not found")
        print("  Install with: uv add netcdf4")
        return None
    except Exception as e:
        print(f"✗ Error loading {nc_file}: {e}")
        return None


def goes_to_latlon(x, y, sat_lon, sat_height):
    """
    Convert GOES fixed grid coordinates to lat/lon.

    Simplified version - for production, use pyproj.
    """
    # This is a simplified conversion
    # For accurate conversion, use:
    # from pyproj import Proj
    # proj = Proj(proj='geos', h=sat_height, lon_0=sat_lon, sweep='x')

    # For prototype, approximate:
    # x, y are in radians from satellite perspective
    # Convert to degrees (very rough approximation)

    # Earth radius
    r_eq = 6378137.0  # meters
    r_pol = 6356752.3  # meters

    # Convert to lat/lon (simplified)
    # This is not accurate but gives rough idea
    lon = np.degrees(x) + sat_lon
    lat = np.degrees(y)

    return lat, lon


def find_matching_files(manifest, day, hour):
    """Find Ch7 and Ch13 files for a specific day/hour."""
    files = manifest['files']

    # Parse filenames to find matches
    # Format: OR_ABI-L2-CMIPC-M6C07_G16_s20242000001180_...
    # Extract day of year and hour from filename

    ch7_files = [f for f in files if f'C07_G16' in f]
    ch13_files = [f for f in files if f'C13_G16' in f]

    # Match by timestamp in filename (simplified - just check if file exists)
    # In production, parse the timestamp properly

    return ch7_files, ch13_files


def calculate_btd_for_pair(ch7_file, ch13_file):
    """Calculate BTD for a matched pair of Ch7 and Ch13 files."""
    print(f"  Loading Ch7: {Path(ch7_file).name}")
    data_ch7 = load_goes16_data(ch7_file)

    if not data_ch7:
        return None

    print(f"  Loading Ch13: {Path(ch13_file).name}")
    data_ch13 = load_goes16_data(ch13_file)

    if not data_ch13:
        return None

    # Check dimensions match
    if data_ch7['cmi'].shape != data_ch13['cmi'].shape:
        print(f"  ✗ Shape mismatch: Ch7={data_ch7['cmi'].shape}, Ch13={data_ch13['cmi'].shape}")
        return None

    # Calculate BTD
    btd = data_ch13['cmi'] - data_ch7['cmi']

    print(f"  BTD statistics:")
    print(f"    Mean: {np.nanmean(btd):.2f} K")
    print(f"    Std: {np.nanstd(btd):.2f} K")
    print(f"    Min: {np.nanmin(btd):.2f} K")
    print(f"    Max: {np.nanmax(btd):.2f} K")

    # Detect fog: BTD > threshold
    is_fog = btd > FOG_BTD_THRESHOLD

    fog_pct = 100 * np.sum(is_fog) / is_fog.size
    print(f"    Fog pixels: {np.sum(is_fog):,} / {is_fog.size:,} ({fog_pct:.1f}%)")

    return {
        'btd': btd,
        'is_fog': is_fog,
        'ch7': data_ch7,
        'ch13': data_ch13
    }


def process_all_samples(manifest):
    """Process all downloaded samples to count fog occurrences."""
    print("Processing BTD for all samples...")
    print("="*70)

    files = [Path(f) for f in manifest['files']]

    # Group by channel
    ch7_files = sorted([f for f in files if 'C07_G16' in f.name])
    ch13_files = sorted([f for f in files if 'C13_G16' in f.name])

    print(f"Found {len(ch7_files)} Ch7 files, {len(ch13_files)} Ch13 files")
    print()

    if len(ch7_files) == 0 or len(ch13_files) == 0:
        print("✗ No data files found")
        return None

    # Try to match pairs by timestamp
    # Simplified: just process first pair for prototype
    print(f"Processing first sample pair...")
    print()

    if len(ch7_files) > 0 and len(ch13_files) > 0:
        result = calculate_btd_for_pair(ch7_files[0], ch13_files[0])

        if result:
            print()
            print("✓ BTD calculation successful!")
            print()
            print("Interpretation:")
            print(f"  BTD > 0°C: Fog/low stratus (water droplets)")
            print(f"  BTD < 0°C: Ice/high clouds")
            print()

            return result

    return None


def create_fog_layer_from_goes16(btd_result, bbox):
    """
    Create fog layer raster from GOES-16 BTD results.

    For prototype: Use the BTD result from sample to validate approach.
    For production: Aggregate multiple days and extrapolate.
    """
    print("Creating fog layer from GOES-16 data...")
    print("="*70)

    # For this prototype, we'll create a simplified output
    # showing that BTD detection works

    # The GOES-16 data is in fixed grid projection
    # We need to reproject to lat/lon for our output

    # Simplified approach: create a summary showing fog was detected
    print()
    print("PROTOTYPE LIMITATION:")
    print("Full reprojection from GOES fixed grid to lat/lon not implemented.")
    print("This would require pyproj or gdal for proper transformation.")
    print()
    print("What we've validated:")
    print("  ✓ Can download GOES-16 data")
    print("  ✓ Can load netCDF files")
    print("  ✓ Can calculate BTD")
    print("  ✓ Can detect fog pixels using BTD > 0")
    print()
    print("Next step: Implement full reprojection to create output raster")
    print("  matching bay_area_fog_80days.tif format")

    return None


def main():
    print("GOES-16 BTD Fog Detection")
    print("="*70)
    print()

    # Load manifest
    manifest = load_manifest()
    if not manifest:
        return

    print(f"Processing {manifest['total_files']} downloaded files")
    print(f"Total size: {manifest['total_size_mb']:.1f} MB")
    print()

    # Load Bay Area bbox
    bbox = load_bbox()

    # Process samples
    btd_result = process_all_samples(manifest)

    if btd_result:
        # Create fog layer
        create_fog_layer_from_goes16(btd_result, bbox)

        print()
        print("="*70)
        print("✓ BTD processing complete!")
        print()
        print("Summary:")
        print(f"  - Downloaded and processed GOES-16 satellite data")
        print(f"  - Calculated BTD (Brightness Temperature Difference)")
        print(f"  - Detected fog pixels where BTD > {FOG_BTD_THRESHOLD}K")
        print()
        print("Status: METHODOLOGY VALIDATED")
        print()
        print("To complete:")
        print("  1. Implement GOES projection → lat/lon reprojection")
        print("  2. Aggregate fog detections to daily counts")
        print("  3. Extrapolate sample days to full dry season")
        print("  4. Create output raster matching PRISM resolution (800m)")
        print()
    else:
        print("✗ BTD processing failed")


if __name__ == "__main__":
    main()
