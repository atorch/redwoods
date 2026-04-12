#!/usr/bin/env python3
"""
Download GOES-16 data for SAMPLE DAYS in July 2024 (Option C: minimal sampling).

For rapid prototyping, we download just 5 days from mid-July 2024 (peak fog season)
and extrapolate to estimate the full dry season pattern.

Sample days: July 15-19, 2024 (Monday-Friday, mid-month)
Hours: Afternoon only (12pm-6pm Pacific = 19:00-01:00 UTC next day)
Channels: 7 (3.9 µm) and 13 (10.3 µm)

Data volume: ~5GB instead of 18-36GB
"""

import subprocess
from pathlib import Path
from datetime import datetime
import json

# Configuration
DATA_DIR = Path("data/goes16_fog_sample")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Channels needed for BTD
CHANNELS = [7, 13]

# Sample days: July 15-19, 2024 (5 days in mid-July, peak fog season)
YEAR = 2024
MONTH = 7
SAMPLE_DAYS = [15, 16, 17, 18, 19]  # Monday-Friday

# Afternoon hours in UTC (12pm-6pm Pacific = 19:00-01:00 UTC next day)
# For simplicity, we'll download just every 2 hours to reduce data volume
UTC_HOURS = [19, 21, 23]  # Afternoon samples: ~1pm, ~3pm, ~5pm Pacific

# AWS S3 base URL
S3_BASE = "https://noaa-goes16.s3.amazonaws.com"
PRODUCT = "ABI-L2-CMIPC"


def get_day_of_year(year, month, day):
    """Convert year/month/day to day of year."""
    dt = datetime(year, month, day)
    return dt.timetuple().tm_yday


def list_s3_files_wget(year, doy, hour, channel):
    """List files using wget to fetch directory listing."""
    s3_url = f"{S3_BASE}/{PRODUCT}/{year}/{doy:03d}/{hour:02d}/"

    try:
        # Fetch the directory listing
        result = subprocess.run(
            ["wget", "-q", "-O", "-", s3_url],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            return []

        # Parse XML response to find .nc files for our channel
        # Look for pattern: OR_ABI-L2-CMIPC-M6C<channel>_G16_*.nc
        import re
        pattern = f'OR_ABI-L2-CMIPC-M6C{channel:02d}_G16_s\\d+_e\\d+_c\\d+\\.nc'
        files = re.findall(pattern, result.stdout)

        return list(set(files))  # Remove duplicates

    except (subprocess.TimeoutExpired, Exception) as e:
        print(f"    ✗ Error listing directory: {e}")
        return []


def download_file(url, output_path):
    """Download a file using wget."""
    if output_path.exists():
        size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"    ✓ Already exists ({size_mb:.1f} MB): {output_path.name}")
        return True

    print(f"    Downloading: {output_path.name}...", end=" ", flush=True)
    try:
        result = subprocess.run(
            ["wget", "-q", "-O", str(output_path), url],
            capture_output=True,
            timeout=300
        )
        if result.returncode == 0 and output_path.exists():
            size_mb = output_path.stat().st_size / (1024 * 1024)
            print(f"✓ ({size_mb:.1f} MB)")
            return True
        else:
            print(f"✗ Failed")
            if output_path.exists():
                output_path.unlink()
            return False
    except subprocess.TimeoutExpired:
        print(f"✗ Timeout")
        if output_path.exists():
            output_path.unlink()
        return False


def download_sample_day(year, month, day, hours, channels):
    """Download data for one sample day."""
    doy = get_day_of_year(year, month, day)
    print(f"\n{year}-{month:02d}-{day:02d} (DOY {doy}):")

    total_downloaded = 0

    for hour in hours:
        # Handle wrap-around for hours 0-1 UTC (next day)
        display_hour = hour if hour >= 19 else hour + 24
        pacific_hour = hour - 7 if hour >= 7 else hour + 17

        print(f"  {hour:02d}:00 UTC (~{pacific_hour:02d}:00 Pacific):")

        for channel in channels:
            # List available files
            files = list_s3_files_wget(year, doy, hour, channel)

            if not files:
                print(f"    Ch{channel:02d}: No files found")
                continue

            print(f"    Ch{channel:02d}: Found {len(files)} files")

            # Download first file only (GOES produces one file per scan, ~every 5-15 min)
            # For prototype, we just need one sample per hour
            filename = sorted(files)[0]  # Take earliest in hour
            url = f"{S3_BASE}/{PRODUCT}/{year}/{doy:03d}/{hour:02d}/{filename}"

            output_dir = DATA_DIR / f"{year}_{month:02d}_{day:02d}"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / filename

            if download_file(url, output_path):
                total_downloaded += 1

    return total_downloaded


def main():
    print("GOES-16 Sample Days Download (Rapid Prototype)")
    print("="*70)
    print(f"Sample period: July {SAMPLE_DAYS[0]}-{SAMPLE_DAYS[-1]}, {YEAR}")
    print(f"Channels: {CHANNELS} (for BTD fog detection)")
    print(f"Hours (UTC): {UTC_HOURS} (afternoon samples)")
    print(f"Output: {DATA_DIR}")
    print()
    print("This downloads ~5 days of afternoon data to validate methodology")
    print("then extrapolates to full dry season (May-Oct).")
    print()

    total_files = 0

    for day in SAMPLE_DAYS:
        downloaded = download_sample_day(YEAR, MONTH, day, UTC_HOURS, CHANNELS)
        total_files += downloaded

    print("\n" + "="*70)
    print(f"✓ Download complete!")
    print(f"  Total files: {total_files}")
    print(f"  Output: {DATA_DIR}")
    print()

    # Calculate estimated data volume
    if total_files > 0:
        total_size_mb = sum(f.stat().st_size for f in DATA_DIR.rglob("*.nc")) / (1024 * 1024)
        print(f"  Downloaded: {total_size_mb:.1f} MB")
        print()

    print("Next step: Process BTD and count fog days")
    print("  Run: scripts/03_process_fog_btd.py")


if __name__ == "__main__":
    main()
