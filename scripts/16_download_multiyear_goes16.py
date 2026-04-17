#!/usr/bin/env python3
"""
Download GOES-16 data for multiple years (2020-2024) for robust climatology.

This script downloads the same 4 weeks from each year to build a multi-year
fog climatology, reducing temporal sampling bias.

Years: 2020, 2021, 2022, 2023 (we already have 2024)
Weeks per year: May, June, August, September (4 weeks × 7 days = 28 days/year)
Total: 28 days/year × 4 years = 112 additional sample days
Files: ~2,352 files (~10 GB)

This will give us 5-year climatology: 140 total sample days (2020-2024)
"""

import subprocess
from pathlib import Path
from datetime import datetime
import json

# Configuration
OUTPUT_DIR = Path("data/goes16_multiyear")
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

# Years to download (2024 already downloaded)
YEARS = [2020, 2021, 2022, 2023]

# Same weeks as current download, but across multiple years
# Using same calendar weeks for consistency
WEEKS_TEMPLATE = [
    {
        'name': 'May (early dry season)',
        'start_doy': 127,  # ~May 6-7 (varies slightly by leap year)
        'end_doy': 133,    # ~May 12-13
        'num_days': 7
    },
    {
        'name': 'June (peak fog)',
        'start_doy': 162,  # ~June 10-11
        'end_doy': 168,    # ~June 16-17
        'num_days': 7
    },
    {
        'name': 'August (mid fog season)',
        'start_doy': 225,  # ~Aug 12-13
        'end_doy': 231,    # ~Aug 18-19
        'num_days': 7
    },
    {
        'name': 'September (late dry season)',
        'start_doy': 260,  # ~Sept 16-17
        'end_doy': 266,    # ~Sept 22-23
        'num_days': 7
    }
]

# Nighttime hours for BTD fog detection
NIGHTTIME_HOURS = [6, 7, 8, 9, 10, 11, 12]  # UTC (11pm-5am PST)

# Channels
CHANNELS = [7, 13]

# GOES-16 S3 bucket
BUCKET = "noaa-goes16"
PRODUCT = "ABI-L2-CMIPC"


def download_goes_files(year, doy, hour, channel):
    """Download GOES-16 files for specific day/hour/channel."""
    s3_path = f"s3://{BUCKET}/{PRODUCT}/{year}/{doy:03d}/{hour:02d}/"

    try:
        # List files in S3
        result = subprocess.run(
            ["aws", "s3", "ls", s3_path, "--no-sign-request"],
            capture_output=True,
            text=True,
            check=True
        )

        # Parse file list
        lines = result.stdout.strip().split('\n')
        files = []
        for line in lines:
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 4:
                filename = parts[3]
                # Filter for this channel and M6 (mesoscale) CONUS
                if f"C{channel:02d}_G16" in filename and "M6" in filename:
                    files.append(filename)

        if not files:
            return []

        # Sort and take first 2 files per hour
        files.sort()
        files_to_download = files[:2]

        downloaded = []
        for filename in files_to_download:
            output_file = OUTPUT_DIR / filename

            # Skip if already exists
            if output_file.exists():
                downloaded.append(filename)
                continue

            # Download file
            s3_file = f"{s3_path}{filename}"
            subprocess.run(
                ["aws", "s3", "cp", s3_file, str(output_file), "--no-sign-request"],
                check=True,
                capture_output=True
            )
            downloaded.append(filename)

        return downloaded

    except subprocess.CalledProcessError as e:
        print(f"    ✗ Error: {e}")
        return []


def main():
    print("="*70)
    print("MULTI-YEAR GOES-16 DATA DOWNLOAD (2020-2023)")
    print("="*70)
    print()
    print("Downloading nighttime fog data (06-12 UTC = 11pm-5am PST)")
    print("for 4 weeks per year across 4 years")
    print()
    print("Years: 2020, 2021, 2022, 2023")
    print("Weeks per year: May, June, August, September")
    print("Total: 112 sample days (28 days/year × 4 years)")
    print("Files: ~2,352 files (~10 GB)")
    print()

    manifest = {
        'download_date': datetime.now().isoformat(),
        'years': []
    }

    total_files = 0

    for year in YEARS:
        print(f"\n{'='*70}")
        print(f"YEAR {year}")
        print("="*70)

        year_data = {
            'year': year,
            'weeks': []
        }

        for week_template in WEEKS_TEMPLATE:
            week_data = {
                'name': week_template['name'],
                'start_doy': week_template['start_doy'],
                'end_doy': week_template['end_doy'],
                'num_days': week_template['num_days'],
                'files_downloaded': 0
            }

            print(f"\n{week_template['name']} (DOY {week_template['start_doy']}-{week_template['end_doy']})")
            print("-" * 70)

            for doy in range(week_template['start_doy'], week_template['end_doy'] + 1):
                for hour in NIGHTTIME_HOURS:
                    for channel in CHANNELS:
                        downloaded = download_goes_files(year, doy, hour, channel)
                        week_data['files_downloaded'] += len(downloaded)
                        total_files += len(downloaded)

                        if downloaded:
                            print(f"  DOY {doy:03d}, H{hour:02d}, Ch{channel:02d}: {len(downloaded)} files")

            year_data['weeks'].append(week_data)

        manifest['years'].append(year_data)

    # Save manifest
    manifest_file = OUTPUT_DIR / "download_manifest.json"
    with open(manifest_file, 'w') as f:
        json.dump(manifest, f, indent=2)

    print()
    print("="*70)
    print("DOWNLOAD COMPLETE")
    print("="*70)
    print(f"Total files downloaded: {total_files}")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Manifest: {manifest_file}")
    print()
    print("Next step: Combine with 2024 data and reprocess fog layer")
    print("  Run: uv run python scripts/11_create_real_fog_layer.py")
    print()


if __name__ == "__main__":
    main()
