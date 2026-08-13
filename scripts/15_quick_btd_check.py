#!/usr/bin/env python3
"""
Quick BTD threshold check - simplified version.

Samples a few GOES-16 pairs and analyzes BTD distribution.
"""

from pathlib import Path
import numpy as np
import netCDF4 as nc
import re

DATA_DIR = Path("data/goes16_multi_week")


def parse_filename(filename):
    """Extract channel and scan time from filename."""
    match = re.match(r'OR_ABI-L2-CMIPC-M6C(\d+)_G16_s(\d{11})', filename)
    if not match:
        return None
    return {
        'channel': int(match.group(1)),
        'scan_time': match.group(2)
    }


def find_one_pair():
    """Find one Ch7/Ch13 pair for analysis."""
    ch7_files = {}
    ch13_files = {}

    for f in DATA_DIR.glob("*.nc"):
        meta = parse_filename(f.name)
        if not meta:
            continue

        if meta['channel'] == 7:
            ch7_files[meta['scan_time']] = f
        elif meta['channel'] == 13:
            ch13_files[meta['scan_time']] = f

    # Find matching pair
    for scan_time in ch7_files:
        if scan_time in ch13_files:
            return ch7_files[scan_time], ch13_files[scan_time]

    return None, None


# Find a pair
ch7_file, ch13_file = find_one_pair()

if not ch7_file:
    print("No Ch7/Ch13 pair found")
    exit(1)

print(f"Analyzing pair:")
print(f"  Ch7:  {ch7_file.name}")
print(f"  Ch13: {ch13_file.name}")
print()

# Load data
with nc.Dataset(ch7_file, 'r') as ds7, nc.Dataset(ch13_file, 'r') as ds13:
    bt7 = ds7.variables['CMI'][:]
    bt13 = ds13.variables['CMI'][:]

    # Calculate BTD
    btd = bt13 - bt7

    # Remove fill values
    valid_mask = (bt7 > 0) & (bt13 > 0) & (bt7 < 400) & (bt13 < 400)
    btd_valid = btd[valid_mask]

    print(f"Valid pixels: {len(btd_valid):,}")
    print()

    print("BTD Statistics:")
    print(f"  Min:    {btd_valid.min():6.2f} K")
    print(f"  Max:    {btd_valid.max():6.2f} K")
    print(f"  Mean:   {btd_valid.mean():6.2f} K")
    print(f"  Median: {np.median(btd_valid):6.2f} K")
    print(f"  Std:    {btd_valid.std():6.2f} K")
    print()

    print("Percentiles:")
    for p in [10, 25, 50, 75, 90, 95, 99]:
        val = np.percentile(btd_valid, p)
        print(f"  {p:2d}th: {val:6.2f} K")
    print()

    print("Fog Detection Rate by Threshold:")
    print("Threshold (K) | % Pixels > Threshold")
    print("-" * 40)

    for threshold in [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]:
        pct = np.sum(btd_valid > threshold) / len(btd_valid) * 100
        print(f"  {threshold:4.1f} K      |  {pct:5.1f}%")

    print()
    print("INTERPRETATION:")
    print("-" * 70)

    pct_0 = np.sum(btd_valid > 0.0) / len(btd_valid) * 100
    pct_2 = np.sum(btd_valid > 2.0) / len(btd_valid) * 100
    pct_3 = np.sum(btd_valid > 3.0) / len(btd_valid) * 100

    print(f"Current threshold (0.0 K): {pct_0:.1f}% detected as fog")
    print(f"CIMSS recommended (2.0 K): {pct_2:.1f}% detected as fog")
    print(f"Conservative (3.0 K):      {pct_3:.1f}% detected as fog")
    print()

    if pct_0 > 80:
        print("⚠️  WARNING: Current 0.0 K threshold is TOO LENIENT")
        print("    Detecting > 80% of pixels as fog (unrealistic)")
        print()

    print("RECOMMENDATION: Use BTD threshold of 2.0-3.0 K")
    print("  - Aligns with CIMSS fog detection standards")
    print("  - Will reduce false positive fog detections")
    print("  - Should show more realistic spatial patterns")
