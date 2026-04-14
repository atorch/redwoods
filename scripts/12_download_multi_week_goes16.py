#!/usr/bin/env python3
"""
Download GOES-16 data from multiple weeks across dry season for robust fog analysis.

Strategy:
- Sample 4 additional weeks from May, June, August, September (we already have July)
- Download Ch7 + Ch13 for afternoon hours (12-17 PST = 19-00 UTC)
- 2 samples per hour (30-minute intervals)
- Total: ~4 weeks × 7 days × 6 hours × 2 samples × 2 channels = ~672 files
- Estimated size: ~4.7 GB (manageable within disk budget)

This gives us 5 weeks distributed across the dry season for spatially explicit fog patterns.
"""

import subprocess
from pathlib import Path
from datetime import datetime, timedelta
import json

# Configuration
OUTPUT_DIR = Path("data/goes16_multi_week")
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

# Weeks to download (strategically sampled across dry season)
WEEKS = [
    {
        'name': 'May (early dry season)',
        'year': 2024,
        'start_doy': 127,  # May 6
        'end_doy': 133,    # May 12
        'num_days': 7
    },
    {
        'name': 'June (peak fog)',
        'year': 2024,
        'start_doy': 162,  # June 10
        'end_doy': 168,    # June 16
        'num_days': 7
    },
    {
        'name': 'August (mid fog season)',
        'year': 2024,
        'start_doy': 225,  # Aug 12
        'end_doy': 231,    # Aug 18
        'num_days': 7
    },
    {
        'name': 'September (late dry season)',
        'year': 2024,
        'start_doy': 260,  # Sept 16
        'end_doy': 266,    # Sept 22
        'num_days': 7
    }
]

# IMPORTANT LIMITATION: BTD fog detection only works at NIGHT
# During daytime, Ch7 (3.9 µm) contains solar reflection that invalidates BTD
# See: CIMSS documentation on GOES-16 fog detection best practices
#
# Nighttime hours for BTD: 06-12 UTC = 11pm-5am PST (previous day to current day)
# This captures pre-dawn fog when BTD (Ch13 - Ch7) signal is valid
#
# FUTURE: For daytime "fog past noon" detection, must use visible channels (0.65 µm)
# See ticket for daytime fog detection implementation
NIGHTTIME_HOURS = [6, 7, 8, 9, 10, 11, 12]  # UTC hours (night/early morning in California)

# Channels to download
CHANNELS = [7, 13]

# GOES-16 S3 bucket
BUCKET = "noaa-goes16"
PRODUCT = "ABI-L2-CMIPC"


def format_hour(hour):
    """Format hour for directory structure (handle UTC day rollover)."""
    return f"{hour:02d}"


def download_goes_files(year, doy, hour, channel):
    """
    Download GOES-16 files for specific day/hour/channel.

    Downloads 2 files per hour (at approximately 00-15 and 30-45 minutes).
    """
    # Construct S3 path
    s3_path = f"s3://{BUCKET}/{PRODUCT}/{year}/{doy:03d}/{hour:02d}/"

    print(f"  Listing files for DOY {doy:03d}, hour {hour:02d}, Ch{channel:02d}...")

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
            print(f"    ✗ No files found")
            return []

        # Sort and take first 2 files (approximately 00-15 and 30-45 minutes)
        files.sort()
        files_to_download = files[:2]

        downloaded = []
        for filename in files_to_download:
            output_file = OUTPUT_DIR / filename

            # Skip if already exists
            if output_file.exists():
                print(f"    ✓ Already exists: {filename}")
                downloaded.append(filename)
                continue

            # Download
            s3_file = s3_path + filename
            print(f"    ↓ Downloading: {filename}")

            try:
                subprocess.run(
                    ["aws", "s3", "cp", s3_file, str(output_file), "--no-sign-request"],
                    check=True,
                    capture_output=True
                )
                downloaded.append(filename)
                print(f"      ✓ Downloaded ({output_file.stat().st_size / 1024 / 1024:.1f} MB)")
            except subprocess.CalledProcessError as e:
                print(f"      ✗ Download failed: {e}")

        return downloaded

    except subprocess.CalledProcessError as e:
        print(f"    ✗ Error listing files: {e}")
        return []


def download_week(week_info):
    """Download all files for one week."""
    print()
    print("="*70)
    print(f"Downloading: {week_info['name']}")
    print("="*70)
    print(f"Year: {week_info['year']}")
    print(f"DOY range: {week_info['start_doy']}-{week_info['end_doy']}")
    print(f"Days: {week_info['num_days']}")
    print()

    all_files = []

    for doy in range(week_info['start_doy'], week_info['end_doy'] + 1):
        print(f"\nDay {doy:03d}:")

        for hour in NIGHTTIME_HOURS:
            for channel in CHANNELS:
                files = download_goes_files(week_info['year'], doy, hour, channel)
                all_files.extend(files)

    return all_files


def check_disk_space():
    """Check available disk space."""
    result = subprocess.run(
        ["df", "-h", str(OUTPUT_DIR.parent.absolute())],
        capture_output=True,
        text=True
    )
    print("Current disk space:")
    print(result.stdout)


def main():
    import sys

    print("="*70)
    print("GOES-16 Multi-Week Download")
    print("="*70)
    print()
    print("Downloading GOES-16 data from strategic weeks across dry season:")
    for week in WEEKS:
        print(f"  - {week['name']}: DOY {week['start_doy']}-{week['end_doy']}, {week['year']}")
    print()
    print("Channels: Ch7 (3.9 µm), Ch13 (10.3 µm)")
    print("Hours: Nighttime (06-12 UTC = 11pm-5am PST)")
    print("Samples: 2 per hour")
    print()
    print("NOTE: Using nighttime hours because BTD fog detection")
    print("      only works at night (solar reflection invalidates BTD during day)")
    print()

    # Check disk space
    check_disk_space()
    print()

    # Estimate total files
    total_files = sum(week['num_days'] for week in WEEKS) * len(NIGHTTIME_HOURS) * 2 * len(CHANNELS)
    estimated_size_gb = total_files * 7 / 1024  # ~7 MB per file

    print(f"Estimated download:")
    print(f"  Files: ~{total_files}")
    print(f"  Size: ~{estimated_size_gb:.1f} GB")
    print()

    # Confirm (auto-proceed if --yes flag provided)
    if '--yes' in sys.argv or '-y' in sys.argv:
        print("Auto-proceeding with download (--yes flag detected)")
    else:
        try:
            response = input("Proceed with download? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("Download cancelled.")
                return
        except EOFError:
            print("No input available. Use --yes flag to auto-proceed.")
            return

    # Download each week
    manifest = {
        'download_date': datetime.now().isoformat(),
        'weeks': [],
        'total_files': 0
    }

    for week in WEEKS:
        files = download_week(week)
        manifest['weeks'].append({
            'name': week['name'],
            'year': week['year'],
            'start_doy': week['start_doy'],
            'end_doy': week['end_doy'],
            'num_days': week['num_days'],
            'files_downloaded': len(files)
        })
        manifest['total_files'] += len(files)

    # Save manifest
    manifest_file = OUTPUT_DIR / "download_manifest.json"
    with open(manifest_file, 'w') as f:
        json.dump(manifest, f, indent=2)

    print()
    print("="*70)
    print("Download complete!")
    print("="*70)
    print(f"Total files downloaded: {manifest['total_files']}")
    print(f"Manifest saved: {manifest_file}")
    print()

    # Check final disk usage
    total_size = sum(f.stat().st_size for f in OUTPUT_DIR.glob("*.nc"))
    print(f"Total data size: {total_size / 1024 / 1024 / 1024:.2f} GB")
    print()
    check_disk_space()

    print()
    print("Next step: Process multi-week fog data")
    print("  Run: uv run python scripts/13_process_multi_week_fog.py")


if __name__ == "__main__":
    main()
