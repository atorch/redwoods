#!/usr/bin/env python3
"""
Download GOES-16 fog detection data for Bay Area, CA

This script demonstrates how to download GOES-16 ABI-L2-CMIP (Cloud and Moisture Imagery Product)
data from NOAA's AWS S3 bucket for fog detection using the Brightness Temperature Difference method.

Fog Detection Method:
- Uses BTD (Brightness Temperature Difference) between Channel 13 (10.3 µm) and Channel 7 (3.9 µm)
- Formula: BTD = BT_Ch13 - BT_Ch7
- Fog/low stratus shows positive BTD (typically > 0°C)
- High/ice clouds show negative BTD

Data Source: s3://noaa-goes16 (public bucket, no authentication required)
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path
from urllib.request import urlretrieve


def construct_goes16_url(year, day_of_year, hour, channel):
    """
    Construct GOES-16 CMIP file URL for a specific time and channel.

    Args:
        year: Year (e.g., 2024)
        day_of_year: Day of year (1-366)
        hour: Hour (0-23)
        channel: ABI channel number (1-16)

    Returns:
        Base URL pattern (actual filename requires querying the bucket)
    """
    base_url = "https://noaa-goes16.s3.amazonaws.com"
    product = "ABI-L2-CMIPC"  # CONUS (Continental US) domain
    path = f"{base_url}/{product}/{year:04d}/{day_of_year:03d}/{hour:02d}/"
    return path


def download_goes16_fog_channels(date, output_dir="data/goes16_fog", hour=None):
    """
    Download GOES-16 channels needed for fog detection (Ch 7 and Ch 13).

    Args:
        date: datetime object for the date to download
        output_dir: Directory to save downloaded files
        hour: Specific hour to download (0-23), or None for all hours

    Returns:
        List of downloaded file paths
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    year = date.year
    day_of_year = date.timetuple().tm_yday

    # Channels for fog detection
    # Ch 7: 3.9 µm (shortwave IR)
    # Ch 13: 10.3 µm (longwave IR)
    fog_channels = [7, 13]

    print(f"Downloading GOES-16 fog data for {date.strftime('%Y-%m-%d')}")
    print(f"Day of year: {day_of_year}")
    print(f"Channels: {fog_channels} (for Brightness Temperature Difference)")
    print()

    downloaded_files = []

    # Note: This is a simplified example
    # In practice, you would need to:
    # 1. Query the S3 bucket to find exact filenames (they include timestamps)
    # 2. Use goes2go library for easier access
    # 3. Filter by geographic region if needed

    print("Example file pattern:")
    example_url = construct_goes16_url(year, day_of_year, 0, 7)
    print(f"  {example_url}OR_ABI-L2-CMIPC-M6C07_G16_s<timestamp>_e<timestamp>_c<timestamp>.nc")
    print()
    print("To download actual files, you can:")
    print("1. Use wget/curl with specific URLs from S3 bucket listings")
    print("2. Use the goes2go Python library (recommended)")
    print("3. Use AWS CLI (aws s3 ls/cp --no-sign-request)")

    return downloaded_files


def calculate_fog_btd(ch7_file, ch13_file):
    """
    Calculate Brightness Temperature Difference for fog detection.

    Args:
        ch7_file: Path to Channel 7 (3.9 µm) netCDF file
        ch13_file: Path to Channel 13 (10.3 µm) netCDF file

    Returns:
        BTD array (numpy array)
    """
    try:
        import netCDF4 as nc
        import numpy as np
    except ImportError:
        print("Error: netCDF4 and numpy are required")
        print("Install with: uv add netcdf4 numpy")
        return None

    # Open both files
    ds_ch7 = nc.Dataset(ch7_file)
    ds_ch13 = nc.Dataset(ch13_file)

    # Read brightness temperature data
    # CMI variable contains calibrated brightness temperature in Kelvin
    bt_ch7 = ds_ch7.variables['CMI'][:]
    bt_ch13 = ds_ch13.variables['CMI'][:]

    # Calculate BTD: Ch13 - Ch7
    # Positive values indicate fog/low stratus
    btd = bt_ch13 - bt_ch7

    ds_ch7.close()
    ds_ch13.close()

    print(f"Brightness Temperature Difference statistics:")
    print(f"  Mean: {np.nanmean(btd):.2f} K")
    print(f"  Std: {np.nanstd(btd):.2f} K")
    print(f"  Min: {np.nanmin(btd):.2f} K")
    print(f"  Max: {np.nanmax(btd):.2f} K")
    print()
    print("Interpretation:")
    print("  BTD > 0°C: Likely fog/low stratus (water droplets)")
    print("  BTD < 0°C: Likely ice/high clouds")

    return btd


if __name__ == "__main__":
    # Example: Download fog data for a recent date
    # Using July 18, 2024 as example (Day 200)
    example_date = datetime(2024, 7, 18)

    print("=" * 70)
    print("GOES-16 Fog Data Download Tool for Bay Area")
    print("=" * 70)
    print()

    # Download data
    download_goes16_fog_channels(example_date)

    print()
    print("Next steps:")
    print("1. Install goes2go for easier data access: uv add goes2go")
    print("2. Use goes2go to download specific time ranges")
    print("3. Process BTD to identify fog regions")
    print("4. Aggregate afternoon fog occurrences for the heuristic (80+ days/dry season)")
