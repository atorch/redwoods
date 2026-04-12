#!/usr/bin/env python3
"""
Download GOES-16 data for July-August 2024 (Option C: minimal sampling).

Downloads afternoon hours only (12pm-6pm Pacific = 19:00-01:00 UTC next day)
for channels 7 (3.9 µm) and 13 (10.3 µm) needed for fog detection.

This script downloads ~18-36 GB of data for July-August 2024.
"""

import subprocess
from pathlib import Path
from datetime import datetime, timedelta
import json

# Configuration
DATA_DIR = Path("data/goes16_fog")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Channels needed for BTD (Brightness Temperature Difference)
CHANNELS = [7, 13]  # Ch7: 3.9µm, Ch13: 10.3µm

# Time period: July-August 2024
YEAR = 2024
MONTHS = [7, 8]  # July, August

# Afternoon hours in UTC (12pm-6pm Pacific = 19:00-01:00 UTC next day)
# Pacific Daylight Time (PDT) is UTC-7
# So 12:00 PDT = 19:00 UTC, 18:00 PDT = 01:00 UTC next day
UTC_HOURS = [19, 20, 21, 22, 23, 0, 1]  # 19:00-01:00 UTC

# AWS S3 base URL
S3_BASE = "https://noaa-goes16.s3.amazonaws.com"
PRODUCT = "ABI-L2-CMIPC"  # CONUS domain, Cloud and Moisture Imagery Product


def get_day_of_year(year, month, day):
    """Convert year/month/day to day of year."""
    dt = datetime(year, month, day)
    return dt.timetuple().tm_yday


def generate_download_urls(year, month, day, hour, channel):
    """Generate URLs for all files in a given hour."""
    doy = get_day_of_year(year, month, day)

    # S3 path structure: ABI-L2-CMIPC/<YEAR>/<DOY>/<HOUR>/
    s3_path = f"{S3_BASE}/{PRODUCT}/{year}/{doy:03d}/{hour:02d}/"

    # We need to list files first - for now, return the directory path
    # We'll use AWS CLI to list files
    return s3_path, doy


def download_file(url, output_path):
    """Download a file using wget."""
    if output_path.exists():
        print(f"  ✓ Already exists: {output_path.name}")
        return True

    print(f"  Downloading: {output_path.name}")
    try:
        result = subprocess.run(
            ["wget", "-q", "-O", str(output_path), url],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout per file
        )
        if result.returncode == 0:
            print(f"  ✓ Downloaded: {output_path.name}")
            return True
        else:
            print(f"  ✗ Failed: {result.stderr}")
            if output_path.exists():
                output_path.unlink()
            return False
    except subprocess.TimeoutExpired:
        print(f"  ✗ Timeout downloading {output_path.name}")
        if output_path.exists():
            output_path.unlink()
        return False


def list_s3_files(s3_path, channel):
    """List files in S3 directory for a specific channel."""
    try:
        # Use AWS CLI without credentials (public bucket)
        result = subprocess.run(
            ["aws", "s3", "ls", s3_path.replace("https://noaa-goes16.s3.amazonaws.com/", "s3://noaa-goes16/"),
             "--no-sign-request"],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            print(f"    ✗ Failed to list S3 directory: {result.stderr}")
            return []

        # Parse output and filter for the channel
        files = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            parts = line.split()
            if len(parts) < 4:
                continue
            filename = parts[-1]
            if f"C{channel:02d}_G16" in filename and filename.endswith('.nc'):
                files.append(filename)

        return files

    except subprocess.TimeoutExpired:
        print(f"    ✗ Timeout listing S3 directory")
        return []
    except FileNotFoundError:
        print("    ✗ AWS CLI not found. Install with: apt-get install awscli")
        return []


def download_for_date_hour(year, month, day, hour, channel):
    """Download all files for a specific date/hour/channel."""
    s3_path, doy = generate_download_urls(year, month, day, hour, channel)

    # List files
    files = list_s3_files(s3_path, channel)

    if not files:
        print(f"    No files found for Ch{channel:02d}")
        return 0

    print(f"    Found {len(files)} files for Ch{channel:02d}")

    # Download files
    downloaded = 0
    for filename in files:
        url = s3_path + filename
        output_path = DATA_DIR / f"{year}_{doy:03d}_{hour:02d}" / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if download_file(url, output_path):
            downloaded += 1

    return downloaded


def main():
    print("GOES-16 Fog Data Download (Option C: July-August 2024)")
    print("="*70)
    print(f"Downloading channels: {CHANNELS}")
    print(f"Months: {MONTHS} (July-August 2024)")
    print(f"Hours (UTC): {UTC_HOURS}")
    print(f"Output directory: {DATA_DIR}")
    print()

    # Check if AWS CLI is available
    try:
        subprocess.run(["aws", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ERROR: AWS CLI not found. Please install:")
        print("  sudo apt-get install awscli")
        print("  or: pip install awscli")
        return

    total_downloaded = 0
    total_files = 0

    for month in MONTHS:
        # Determine days in month
        if month in [1, 3, 5, 7, 8, 10, 12]:
            days = 31
        elif month in [4, 6, 9, 11]:
            days = 30
        else:
            days = 29 if YEAR % 4 == 0 else 28

        print(f"\nProcessing {YEAR}-{month:02d} ({days} days)")
        print("-"*70)

        for day in range(1, days + 1):
            print(f"\n{YEAR}-{month:02d}-{day:02d}:")

            for hour in UTC_HOURS:
                # Handle hour 0 and 1 which are next day UTC
                actual_day = day
                actual_month = month
                actual_year = YEAR

                if hour < 2 and day < days:  # 0 and 1 UTC are next day
                    actual_day = day + 1
                elif hour < 2 and day == days:
                    # Last day of month, next day is next month
                    actual_day = 1
                    actual_month = month + 1 if month < 12 else 1
                    actual_year = YEAR if month < 12 else YEAR + 1

                print(f"  Hour {hour:02d} UTC ({actual_year}-{actual_month:02d}-{actual_day:02d}):")

                for channel in CHANNELS:
                    downloaded = download_for_date_hour(
                        actual_year, actual_month, actual_day, hour, channel
                    )
                    total_downloaded += downloaded
                    total_files += downloaded

    print("\n" + "="*70)
    print(f"✓ Download complete!")
    print(f"  Total files downloaded: {total_downloaded}")
    print(f"  Output directory: {DATA_DIR}")
    print("\nNext step: Process BTD and count fog days")


if __name__ == "__main__":
    main()
