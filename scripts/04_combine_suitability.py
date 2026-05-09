#!/usr/bin/env python3
"""
Combine rainfall, fog, and land layers into the final redwood suitability layer.

The rule itself (sufficient rain AND sufficient fog AND on land) lives in
scripts/suitability.py — this script is just plumbing: load the three binary
masks, call `suitability.combine`, write the result, validate at the ground
truth points, print stats.

Fog input is the daytime ("fog past noon") layer from GOES-18 Ch2 albedo
(see scripts/18 + scripts/19, ticket 22).
"""

from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import rowcol

import suitability

OUTPUT_DIR = Path("outputs")
RAINFALL_FILE = OUTPUT_DIR / "study_area_rainfall_20in.tif"
FOG_FILE = OUTPUT_DIR / "study_area_fog_threshold_daytime.tif"
LAND_FILE = OUTPUT_DIR / "study_area_land_mask.tif"
TEMPERATURE_FILE = OUTPUT_DIR / "study_area_temperature_mask.tif"
OUTPUT_FILE = OUTPUT_DIR / "study_area_redwood_suitable.tif"
GROUND_TRUTH_FILE = Path("web/ground_truth_points.csv")


def load_mask(path, name):
    with rasterio.open(path) as src:
        arr = src.read(1)
        meta = src.meta.copy()
    ones = int((arr == 1).sum())
    print(f"  {name:<8} shape={arr.shape}  1-pixels={ones:,}")
    return arr, meta


def combine_layers():
    print("Combining Suitability Layers")
    print("=" * 60)

    rain, meta = load_mask(RAINFALL_FILE, "rain")
    fog, _ = load_mask(FOG_FILE, "fog")
    land, _ = load_mask(LAND_FILE, "land")
    temp, _ = load_mask(TEMPERATURE_FILE, "temp")

    print("\nApplying rule: rain AND fog AND land AND temperate (scripts/suitability.py)...")
    combined = suitability.combine(rain, fog, land, temp)

    total = int((combined != suitability.NODATA).sum())
    suit = int((combined == 1).sum())
    pct = 100 * suit / total if total > 0 else 0
    print(f"  Suitable: {suit:,} / {total:,} ({pct:.1f}%)")

    output_meta = meta.copy()
    output_meta.update({"dtype": "uint8", "nodata": int(suitability.NODATA)})

    print(f"\nSaving combined suitability: {OUTPUT_FILE}")
    with rasterio.open(OUTPUT_FILE, "w", **output_meta) as dst:
        dst.write(combined, 1)
        dst.set_band_description(
            1, "Redwood suitable habitat (1=suitable, 0=not suitable, 255=nodata)"
        )

    return combined, meta["transform"], meta


def validate_ground_truth(suitable, transform):
    print("\n" + "=" * 60)
    print("VALIDATION: Ground Truth Points")
    print("=" * 60)

    df = pd.read_csv(GROUND_TRUTH_FILE, quotechar="'")
    print(f"\nChecking {len(df)} ground truth points:\n")

    all_suitable = True
    for _, row in df.iterrows():
        lat, lon = row["latitude"], row["longitude"]
        name = row["notes"]

        py, px = rowcol(transform, lon, lat)

        if 0 <= py < suitable.shape[0] and 0 <= px < suitable.shape[1]:
            is_suitable = suitable[py, px] == 1
            if is_suitable:
                print(f"✓ PASS: {name}  ({lat:.4f}, {lon:.4f})")
            else:
                print(f"✗ FAIL: {name}  ({lat:.4f}, {lon:.4f})")
                all_suitable = False
        else:
            print(f"✗ OUT OF BOUNDS: {name}")
            all_suitable = False

    print()
    print("=" * 60)
    if all_suitable:
        print("✓ SUCCESS: All ground truth points are in suitable habitat!")
    else:
        print("✗ WARNING: Some ground truth points failed validation")
    print("=" * 60)

    return all_suitable


def generate_summary_stats(suitable):
    print("\n" + "=" * 60)
    print("SUMMARY STATISTICS")
    print("=" * 60)

    with rasterio.open(OUTPUT_DIR / "study_area_rainfall_total.tif") as src:
        rainfall_total = src.read(1)
    with rasterio.open(OUTPUT_DIR / "study_area_fog_days_daytime.tif") as src:
        fog_days = src.read(1)

    suitable_mask = suitable == 1
    if suitable_mask.sum() > 0:
        print("\nFor suitable habitat areas:")
        print(
            f"  Rainfall: {rainfall_total[suitable_mask].min():.1f} – "
            f"{rainfall_total[suitable_mask].max():.1f} in "
            f"(mean {rainfall_total[suitable_mask].mean():.1f})"
        )
        print(
            f"  Fog days: {fog_days[suitable_mask].min():.1f} – "
            f"{fog_days[suitable_mask].max():.1f} "
            f"(mean {fog_days[suitable_mask].mean():.1f})"
        )
    print("=" * 60)


def main():
    print("\n" + "=" * 60)
    print("REDWOOD HABITAT SUITABILITY — Final Combination")
    print("=" * 60)
    print(f"  Rainfall threshold: >= {suitability.RAINFALL_THRESHOLD_INCHES} inches (Nov–Apr)")
    print(f"  Fog threshold:      >= {suitability.FOG_DAYS_THRESHOLD} days (dry season)")
    print(f"  Land mask:          USDA CDL (water/wetland excluded)")
    print(
        f"  Temperature:        coldest-month tmin >= {suitability.COLDEST_MONTH_TMIN_FLOOR_C} °C "
        f"AND hottest-month tmax <= {suitability.HOTTEST_MONTH_TMAX_CEILING_C} °C"
    )
    print()

    suitable, transform, _ = combine_layers()
    validation_passed = validate_ground_truth(suitable, transform)
    generate_summary_stats(suitable)

    print("\n✓ Suitability layer creation complete!")
    print("\nOutput files:")
    print(f"  - {OUTPUT_FILE}")
    print("\nNext step: regenerate web tiles (scripts/13_generate_web_tiles.py)")

    if validation_passed:
        print("\n" + "=" * 60)
        print("✓ PROTOTYPE VALIDATION: SUCCESS")
        print("=" * 60)


if __name__ == "__main__":
    main()
