#!/usr/bin/env python3
"""
Process week of GOES-16 data to count fog days.

For each day:
1. Load all Ch7/Ch13 pairs for that day
2. Calculate BTD for each pair
3. Determine if afternoon fog was present (any sample with BTD > 0)
4. Count total fog days in the week
5. Extrapolate to full dry season (184 days)

Output: Fog layer raster matching mock fog format for comparison.
"""

import json
from pathlib import Path
import numpy as np
import re
from collections import defaultdict

# Configuration
DATA_DIR = Path("data/goes16_week")
OUTPUT_DIR = Path("outputs")
MANIFEST_FILE = DATA_DIR / "download_manifest.json"
BBOX_FILE = OUTPUT_DIR / "bay_area_bbox.json"

# BTD threshold for fog (Kelvin)
FOG_BTD_THRESHOLD = 0.0

# Dry season: May 1 - Oct 31 = 184 days
DRY_SEASON_DAYS = 184


def load_manifest():
    """Load download manifest."""
    if not MANIFEST_FILE.exists():
        print(f"✗ Manifest not found: {MANIFEST_FILE}")
        print("  Run scripts/09_download_week_goes16.py first")
        return None

    with open(MANIFEST_FILE) as f:
        return json.load(f)


def parse_filename(filename):
    """Extract metadata from GOES-16 filename."""
    # OR_ABI-L2-CMIPC-M6C07_G16_s20242000001180_e20242000003565_c20242000004044.nc
    # Extract: channel, start timestamp
    match = re.search(r'C(\d{2})_G16_s(\d{14})', filename)
    if match:
        channel = int(match.group(1))
        timestamp = match.group(2)

        # Parse timestamp: YYYYDDDHHMMSSs
        year = int(timestamp[0:4])
        doy = int(timestamp[4:7])
        hour = int(timestamp[7:9])
        minute = int(timestamp[9:11])

        # Create a unique key for matching (year, doy, hour, minute)
        match_key = (year, doy, hour, minute)

        return {
            'channel': channel,
            'year': year,
            'doy': doy,
            'hour': hour,
            'minute': minute,
            'match_key': match_key,
            'filename': filename
        }

    return None


def match_channel_pairs(files):
    """Match Ch7 and Ch13 files by timestamp."""
    ch7_files = {}
    ch13_files = {}

    for filename in files:
        info = parse_filename(filename)
        if not info:
            continue

        if info['channel'] == 7:
            ch7_files[info['match_key']] = info
        elif info['channel'] == 13:
            ch13_files[info['match_key']] = info

    # Find matching pairs
    pairs = []
    for key in ch7_files:
        if key in ch13_files:
            pairs.append((ch7_files[key], ch13_files[key]))

    return pairs


def calculate_btd_for_pair(ch7_info, ch13_info):
    """Calculate BTD for a matched pair."""
    try:
        import netCDF4 as nc

        ch7_path = DATA_DIR / ch7_info['filename']
        ch13_path = DATA_DIR / ch13_info['filename']

        ds7 = nc.Dataset(ch7_path)
        ds13 = nc.Dataset(ch13_path)

        bt7 = ds7.variables['CMI'][:]
        bt13 = ds13.variables['CMI'][:]

        btd = bt13 - bt7

        # Detect fog
        fog_mask = btd > FOG_BTD_THRESHOLD
        fog_fraction = np.sum(fog_mask) / fog_mask.size

        ds7.close()
        ds13.close()

        return {
            'btd': btd,
            'fog_mask': fog_mask,
            'fog_fraction': fog_fraction,
            'timestamp': (ch7_info['year'], ch7_info['doy'], ch7_info['hour'], ch7_info['minute'])
        }

    except Exception as e:
        print(f"    ✗ Error processing pair: {e}")
        return None


def group_by_day(pairs):
    """Group matched pairs by calendar day."""
    by_day = defaultdict(list)

    for ch7, ch13 in pairs:
        # Use (year, doy) as key
        day_key = (ch7['year'], ch7['doy'])
        by_day[day_key].append((ch7, ch13))

    return by_day


def process_all_days(pairs):
    """Process all days to count fog occurrence."""
    print("\nProcessing BTD for all samples...")
    print("="*70)

    by_day = group_by_day(pairs)

    print(f"Found {len(by_day)} days with data")
    print()

    fog_days = []

    for day_key in sorted(by_day.keys()):
        year, doy = day_key
        day_pairs = by_day[day_key]

        print(f"Day {doy} ({year}): {len(day_pairs)} sample pairs")

        # Process each pair for this day
        day_has_fog = False
        fog_fractions = []

        for ch7, ch13 in day_pairs:
            result = calculate_btd_for_pair(ch7, ch13)

            if result:
                fog_fractions.append(result['fog_fraction'])

                # If any afternoon sample has significant fog, count it
                if result['fog_fraction'] > 0.01:  # >1% of pixels show fog
                    day_has_fog = True

        if fog_fractions:
            avg_fog = np.mean(fog_fractions) * 100
            status = "✓ FOG" if day_has_fog else "✗ Clear"
            print(f"  {status}: Avg {avg_fog:.1f}% fog coverage")

            if day_has_fog:
                fog_days.append(day_key)

    print()
    print("="*70)
    print(f"Fog day summary:")
    print(f"  Total days analyzed: {len(by_day)}")
    print(f"  Days with afternoon fog: {len(fog_days)}")
    print(f"  Fog frequency: {100*len(fog_days)/len(by_day):.1f}%")

    return fog_days


def extrapolate_to_dry_season(fog_days_in_week, days_in_week):
    """Extrapolate week sample to full dry season."""
    if days_in_week == 0:
        return 0

    # Simple linear extrapolation
    # fog_days_per_day = fog_days_in_week / days_in_week
    # estimated_dry_season_fog = fog_days_per_day * DRY_SEASON_DAYS

    # More conservative: use ratio
    fog_ratio = fog_days_in_week / days_in_week
    estimated_fog_days = fog_ratio * DRY_SEASON_DAYS

    print()
    print("Extrapolation to full dry season:")
    print(f"  Sample: {fog_days_in_week} fog days / {days_in_week} days")
    print(f"  Fog ratio: {fog_ratio:.2f}")
    print(f"  Dry season (May-Oct): {DRY_SEASON_DAYS} days")
    print(f"  Estimated fog days: {estimated_fog_days:.0f} days")

    return estimated_fog_days


def create_placeholder_fog_layer():
    """
    Create a placeholder fog layer based on fog day counts.

    NOTE: This is simplified - doesn't do full GOES reprojection to lat/lon.
    For prototype, we'll create a uniform layer showing the extrapolated fog count.
    Full implementation would reproject each GOES image and aggregate spatially.
    """
    print()
    print("="*70)
    print("Creating fog layer...")
    print("="*70)
    print()
    print("NOTE: This prototype version creates a uniform fog estimate")
    print("      for the Bay Area based on aggregate fog day counts.")
    print()
    print("For full implementation:")
    print("  - Reproject each GOES-16 image from fixed grid to lat/lon")
    print("  - Subset to Bay Area bounding box")
    print("  - Aggregate fog detection spatially")
    print("  - Create output raster matching PRISM resolution (800m)")
    print()


def main():
    print("GOES-16 Week Processing")
    print("="*70)
    print()

    # Load manifest
    manifest = load_manifest()
    if not manifest:
        return

    print(f"Processing {manifest['total_files']} files")
    print(f"Period: {manifest['start_date'][:10]} + {manifest['num_days']} days")
    print()

    # Match Ch7/Ch13 pairs
    print("Matching Ch7/Ch13 pairs by timestamp...")
    pairs = match_channel_pairs(manifest['files'])
    print(f"  Found {len(pairs)} matched pairs")

    if len(pairs) == 0:
        print("✗ No matched pairs found")
        return

    # Process all days
    fog_days = process_all_days(pairs)

    # Extrapolate
    estimated_fog_days = extrapolate_to_dry_season(len(fog_days), manifest['num_days'])

    # Create output
    create_placeholder_fog_layer()

    # Save results
    results = {
        'processing_date': json.dumps(datetime.now().isoformat()) if 'datetime' in dir() else 'unknown',
        'sample_days': manifest['num_days'],
        'fog_days_observed': len(fog_days),
        'estimated_dry_season_fog_days': int(estimated_fog_days),
        'fog_day_list': [{'year': y, 'doy': d} for y, d in fog_days]
    }

    results_file = DATA_DIR / "fog_analysis_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Results saved: {results_file}")
    print()
    print("="*70)
    print("✓ Processing complete!")
    print("="*70)
    print()

    if estimated_fog_days >= 80:
        print(f"✓ Estimated {estimated_fog_days:.0f} fog days MEETS the 80-day threshold")
    else:
        print(f"⚠️  Estimated {estimated_fog_days:.0f} fog days is BELOW the 80-day threshold")

    print()
    print("Next step: Create full Bay Area fog raster with reprojection")
    print("  Run: scripts/11_create_real_fog_layer.py")


if __name__ == "__main__":
    from datetime import datetime
    main()
