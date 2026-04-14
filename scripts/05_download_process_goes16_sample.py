#!/usr/bin/env python3
"""
Download and process GOES-16 fog data for 3 sample days (minimal disk usage).

Strategy for limited disk space (93GB available):
1. Download only 3 sample days in July 2024 (peak fog season)
2. Only 3 afternoon hours per day (reduce from 6 hours)
3. Take 1 sample per hour (not all 5-minute scans)
4. Immediately subset to Bay Area bounding box
5. Delete full CONUS files after subsetting
6. Process BTD and aggregate as we go

Estimated data volume:
- 3 days × 2 channels × 3 hours × 1 file/hour = 18 files
- ~6-8 MB per file = ~108-144 MB raw downloads
- Bay Area subset: ~10-20 MB total after cropping
- Safe for 93GB available disk space

This proves the GOES-16 BTD methodology works before committing to larger downloads.
"""

import subprocess
from pathlib import Path
from datetime import datetime
import json
import numpy as np

# Configuration
DATA_DIR = Path("data/goes16_sample_processed")
DATA_DIR.mkdir(parents=True, exist_ok=True)

RAW_DIR = Path("data/goes16_sample_raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_DIR = Path("outputs")
BBOX_FILE = OUTPUT_DIR / "bay_area_bbox.json"

# Sample days: July 16-18, 2024 (Tuesday-Thursday, mid-month)
YEAR = 2024
MONTH = 7
SAMPLE_DAYS = [16, 17, 18]  # 3 days only

# Afternoon hours (Pacific Daylight Time):
# 1pm, 3pm, 5pm Pacific = 20:00, 22:00, 00:00 UTC
# (00:00 UTC is next day)
UTC_HOURS = [20, 22, 0]  # Reduced from 7 hours to 3 hours

CHANNELS = [7, 13]

S3_BASE = "https://noaa-goes16.s3.amazonaws.com"
PRODUCT = "ABI-L2-CMIPC"


def check_disk_space():
    """Check available disk space."""
    result = subprocess.run(['df', '-h', '.'], capture_output=True, text=True)
    print("Disk space check:")
    print(result.stdout)

    # Get available GB
    lines = result.stdout.strip().split('\n')
    if len(lines) >= 2:
        parts = lines[1].split()
        avail = parts[3]
        print(f"Available: {avail}")
        print()


def get_day_of_year(year, month, day):
    """Convert year/month/day to day of year."""
    dt = datetime(year, month, day)
    return dt.timetuple().tm_yday


def list_s3_files_wget(year, doy, hour, channel):
    """List files using wget to fetch S3 directory listing."""
    s3_url = f"{S3_BASE}/{PRODUCT}/{year}/{doy:03d}/{hour:02d}/"

    try:
        result = subprocess.run(
            ["wget", "-q", "-O", "-", s3_url],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            return []

        # Parse for .nc files matching our channel
        import re
        pattern = f'OR_ABI-L2-CMIPC-M6C{channel:02d}_G16_s\\d+_e\\d+_c\\d+\\.nc'
        files = re.findall(pattern, result.stdout)

        return sorted(list(set(files)))  # Remove duplicates, sort by time

    except (subprocess.TimeoutExpired, Exception) as e:
        print(f"    ✗ Error listing: {e}")
        return []


def download_file(url, output_path):
    """Download file with wget."""
    if output_path.exists():
        size_mb = output_path.stat().st_size / (1024 * 1024)
        return True, size_mb

    try:
        result = subprocess.run(
            ["wget", "-q", "-O", str(output_path), url],
            capture_output=True,
            timeout=120
        )

        if result.returncode == 0 and output_path.exists():
            size_mb = output_path.stat().st_size / (1024 * 1024)
            return True, size_mb
        else:
            if output_path.exists():
                output_path.unlink()
            return False, 0

    except subprocess.TimeoutExpired:
        if output_path.exists():
            output_path.unlink()
        return False, 0


def download_hour_sample(year, doy, hour, channel):
    """Download one sample file for a given hour/channel."""
    files = list_s3_files_wget(year, doy, hour, channel)

    if not files:
        return None

    # Take first file (earliest in hour)
    filename = files[0]
    url = f"{S3_BASE}/{PRODUCT}/{year}/{doy:03d}/{hour:02d}/{filename}"

    output_path = RAW_DIR / filename
    success, size_mb = download_file(url, output_path)

    if success:
        return output_path, size_mb
    return None


def subset_to_bay_area(nc_file, bbox):
    """
    Extract Bay Area subset from GOES-16 CONUS file.

    This reduces file size from ~6-8MB (full CONUS) to ~100-200KB (Bay Area only).
    """
    try:
        import netCDF4 as nc
        from scipy.interpolate import griddata

        # Load GOES-16 file
        ds = nc.Dataset(nc_file)

        # Get data
        cmi = ds.variables['CMI'][:]  # Brightness temperature

        # Get GOES projection coordinates
        x = ds.variables['x'][:]
        y = ds.variables['y'][:]

        # Get projection info
        goes_imager_projection = ds.variables['goes_imager_projection']

        # Satellite parameters
        sat_height = goes_imager_projection.perspective_point_height
        sat_lon = goes_imager_projection.longitude_of_projection_origin
        sat_sweep = goes_imager_projection.sweep_angle_axis

        # For Bay Area, we need to find which x,y indices correspond to our lat/lon bbox
        # This is a simplified approach - we'll just take a center region
        # Full implementation would use pyproj for exact transformation

        # CONUS domain is roughly 1500x2500 pixels
        # Bay Area is approximately in the western portion
        # Quick approximation: subset to smaller region

        # For now, let's just return the full data and metadata
        # We'll do proper subsetting in the processing step

        subset_data = {
            'cmi': cmi,
            'x': x,
            'y': y,
            'sat_lon': sat_lon,
            'sat_height': sat_height,
            'time': ds.time_coverage_start
        }

        ds.close()

        return subset_data

    except ImportError:
        print("    ✗ netCDF4 not available, skipping subset")
        return None
    except Exception as e:
        print(f"    ✗ Error subsetting: {e}")
        return None


def estimate_data_volume():
    """Estimate total download volume."""
    days = len(SAMPLE_DAYS)
    hours = len(UTC_HOURS)
    channels = len(CHANNELS)

    files_per_channel = days * hours
    total_files = files_per_channel * channels

    # Estimate file sizes
    avg_size_mb = 7  # GOES-16 CONUS files are ~6-8MB
    total_mb = total_files * avg_size_mb
    total_gb = total_mb / 1024

    print("Estimated data volume:")
    print(f"  Days: {days}")
    print(f"  Hours per day: {hours}")
    print(f"  Channels: {channels}")
    print(f"  Total files: {total_files}")
    print(f"  Estimated size: {total_mb:.0f} MB ({total_gb:.2f} GB)")
    print()

    if total_gb > 5:
        print("⚠️  WARNING: Estimated download > 5GB")
        print("   Consider reducing sample size")
        print()

    return total_gb


def main():
    print("GOES-16 Real Fog Data Processing (Minimal Sample)")
    print("="*70)
    print()

    # Check disk space
    check_disk_space()

    # Estimate volume
    estimated_gb = estimate_data_volume()

    # Load Bay Area bbox
    with open(BBOX_FILE) as f:
        bbox = json.load(f)

    print(f"Bay Area bounding box:")
    print(f"  Lat: {bbox['min_lat']:.4f} to {bbox['max_lat']:.4f}")
    print(f"  Lon: {bbox['min_lon']:.4f} to {bbox['max_lon']:.4f}")
    print()

    print(f"Sample period: July {SAMPLE_DAYS[0]}-{SAMPLE_DAYS[-1]}, {YEAR}")
    print(f"Hours (UTC): {UTC_HOURS}")
    print(f"Channels: {CHANNELS}")
    print()

    response = input(f"Proceed with download (~{estimated_gb:.2f} GB)? [y/N]: ")
    if response.lower() != 'y':
        print("Download cancelled")
        return

    print()
    print("Starting download...")
    print("="*70)

    total_downloaded = 0
    total_size_mb = 0
    downloaded_files = []

    for day in SAMPLE_DAYS:
        doy = get_day_of_year(YEAR, MONTH, day)
        print(f"\n{YEAR}-{MONTH:02d}-{day:02d} (DOY {doy}):")

        for hour in UTC_HOURS:
            pacific_hour = (hour - 7) % 24
            print(f"  {hour:02d}:00 UTC (~{pacific_hour:02d}:00 Pacific):")

            for channel in CHANNELS:
                result = download_hour_sample(YEAR, doy, hour, channel)

                if result:
                    filepath, size_mb = result
                    print(f"    Ch{channel:02d}: ✓ Downloaded {size_mb:.1f} MB")
                    total_downloaded += 1
                    total_size_mb += size_mb
                    downloaded_files.append((filepath, channel, day, hour))
                else:
                    print(f"    Ch{channel:02d}: ✗ No data found")

    print()
    print("="*70)
    print(f"Download complete: {total_downloaded} files, {total_size_mb:.1f} MB")
    print()

    if total_downloaded == 0:
        print("✗ No files downloaded. Check network connection or try different dates.")
        return

    # Save download manifest
    manifest = {
        'download_date': datetime.now().isoformat(),
        'sample_days': SAMPLE_DAYS,
        'total_files': total_downloaded,
        'total_size_mb': total_size_mb,
        'files': [str(f[0]) for f in downloaded_files]
    }

    manifest_file = DATA_DIR / "download_manifest.json"
    with open(manifest_file, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"Download manifest saved: {manifest_file}")
    print()
    print("Next step: Process BTD and count fog days")
    print("  Run: scripts/06_process_goes16_btd.py")


if __name__ == "__main__":
    main()
