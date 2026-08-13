#!/usr/bin/env python3
"""
Download 1 week of GOES-16 fog data using AWS CLI.

Downloads July 15-21, 2024 (7 days) with afternoon samples only.
Takes 2 samples per afternoon hour to capture fog variability.

Estimated data:
- 7 days × 6 afternoon hours × 2 samples/hour × 2 channels = 168 files
- ~4 MB/file = ~672 MB total (safe for 93GB available disk)
"""

import subprocess
from pathlib import Path
from datetime import datetime, timedelta
import json

# Configuration
DATA_DIR = Path("data/goes16_week")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Week: July 15-21, 2024 (Monday-Sunday, mid-July peak fog season)
START_DATE = datetime(2024, 7, 15)
NUM_DAYS = 7

# Afternoon hours (Pacific): 12pm-5pm = 19:00-00:00 UTC (next day for 00:00)
# Take 2 samples per hour for better coverage
UTC_HOURS = [19, 20, 21, 22, 23, 0]  # 6 hours

CHANNELS = [7, 13]
SAMPLES_PER_HOUR = 2  # Take first 2 files each hour


def get_day_of_year(date):
    """Get day of year from datetime."""
    return date.timetuple().tm_yday


def download_samples_for_hour(year, doy, hour, channel, num_samples=2):
    """Download first N samples for a given hour/channel."""
    print(f"    Ch{channel:02d} {hour:02d}:00 UTC: ", end="", flush=True)

    # List files in S3
    s3_path = f"s3://noaa-goes16/ABI-L2-CMIPC/{year}/{doy:03d}/{hour:02d}/"

    try:
        result = subprocess.run(
            ["uv", "run", "aws", "s3", "ls", s3_path, "--no-sign-request"],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            print("✗ Failed to list")
            return []

        # Parse output for our channel
        files = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            parts = line.split()
            if len(parts) < 4:
                continue
            filename = parts[-1]
            if f'C{channel:02d}_G16' in filename and filename.endswith('.nc'):
                files.append(filename)

        if not files:
            print("No files found")
            return []

        # Sort and take first N
        files = sorted(files)[:num_samples]

        # Download each file
        downloaded = []
        for filename in files:
            output_path = DATA_DIR / filename

            if output_path.exists():
                downloaded.append(output_path)
                continue

            s3_file = f"{s3_path}{filename}"

            result = subprocess.run(
                ["uv", "run", "aws", "s3", "cp", s3_file, str(output_path), "--no-sign-request"],
                capture_output=True,
                timeout=120
            )

            if result.returncode == 0 and output_path.exists():
                downloaded.append(output_path)

        print(f"✓ {len(downloaded)}/{num_samples}")
        return downloaded

    except subprocess.TimeoutExpired:
        print("✗ Timeout")
        return []
    except Exception as e:
        print(f"✗ Error: {e}")
        return []


def main():
    print("GOES-16 Week Download (July 15-21, 2024)")
    print("="*70)
    print()

    # Calculate totals
    total_hours = NUM_DAYS * len(UTC_HOURS)
    total_files = total_hours * len(CHANNELS) * SAMPLES_PER_HOUR
    estimated_mb = total_files * 4
    estimated_gb = estimated_mb / 1024

    print(f"Download plan:")
    print(f"  Dates: {START_DATE.strftime('%Y-%m-%d')} through {(START_DATE + timedelta(days=NUM_DAYS-1)).strftime('%Y-%m-%d')}")
    print(f"  Days: {NUM_DAYS}")
    print(f"  Afternoon hours (UTC): {UTC_HOURS}")
    print(f"  Samples per hour: {SAMPLES_PER_HOUR}")
    print(f"  Channels: {CHANNELS}")
    print(f"  Estimated files: {total_files}")
    print(f"  Estimated size: {estimated_mb:.0f} MB ({estimated_gb:.2f} GB)")
    print()

    # Check disk space
    result = subprocess.run(['df', '-h', '.'], capture_output=True, text=True)
    print("Current disk space:")
    for line in result.stdout.strip().split('\n')[1:]:
        print(f"  {line}")
    print()

    if estimated_gb > 5:
        print(f"⚠️  WARNING: Download will use {estimated_gb:.2f} GB")
        response = input("Proceed? [y/N]: ")
        if response.lower() != 'y':
            print("Cancelled")
            return

    print("Starting download...")
    print("="*70)

    all_files = []

    for day_offset in range(NUM_DAYS):
        date = START_DATE + timedelta(days=day_offset)
        doy = get_day_of_year(date)

        print(f"\n{date.strftime('%Y-%m-%d')} (DOY {doy}):")

        for hour in UTC_HOURS:
            # Handle hour 0 which is next day
            actual_date = date
            if hour == 0:
                actual_date = date + timedelta(days=1)
                actual_doy = get_day_of_year(actual_date)
            else:
                actual_doy = doy

            for channel in CHANNELS:
                files = download_samples_for_hour(
                    actual_date.year, actual_doy, hour, channel,
                    num_samples=SAMPLES_PER_HOUR
                )
                all_files.extend(files)

    print()
    print("="*70)
    print(f"Download complete!")
    print(f"  Files downloaded: {len(all_files)}")

    if len(all_files) > 0:
        total_size = sum(f.stat().st_size for f in all_files) / (1024 * 1024)
        print(f"  Total size: {total_size:.1f} MB")

    # Save manifest
    manifest = {
        'download_date': datetime.now().isoformat(),
        'start_date': START_DATE.isoformat(),
        'num_days': NUM_DAYS,
        'total_files': len(all_files),
        'files': sorted([f.name for f in all_files])
    }

    manifest_file = DATA_DIR / "download_manifest.json"
    with open(manifest_file, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"  Manifest: {manifest_file}")
    print()
    print("Next step: Process BTD and count fog days")
    print("  Run: scripts/10_process_week_btd.py")


if __name__ == "__main__":
    main()
