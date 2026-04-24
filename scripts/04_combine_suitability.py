#!/usr/bin/env python3
"""
Combine rainfall and fog layers into final redwood suitability layer.

This implements the academic heuristic:
"If the place is north of San Simeon, fog currently lasts past noon 80 days/dry season,
and the place has more than 20 inches/year of rain in the wet season, it had redwoods in 1750."

For the northern California study area (Bay Area through Redwood NP):
- Geographic filter: All pixels are north of San Simeon (>= ~37° > 35.6°) - always TRUE
- Rainfall: >= 20 inches Nov-Apr
- Fog: >= 80 days/dry season (GOES-16 satellite BTD detection)

IMPORTANT LIMITATION (v0):
- Current fog layer uses NIGHTTIME-ONLY BTD (Brightness Temperature Difference) detection
- BTD only works at night (06-12 UTC = 11pm-5am PST) due to solar contamination of Ch7 during day
- This represents nighttime/pre-dawn fog frequency, not full 24-hour fog
- Future enhancement needed: daytime fog detection using visible channels (see Ticket #22)
- For v0 web tiles, we accept this limitation and label as "nighttime fog frequency"

Final suitability = rainfall_suitable AND fog_suitable
"""

import numpy as np
import rasterio
from pathlib import Path
import pandas as pd
from rasterio.transform import rowcol

# Configuration
OUTPUT_DIR = Path("outputs")
RAINFALL_FILE = OUTPUT_DIR / "study_area_rainfall_20in.tif"

# GOES-16 fog layer (real satellite data, nighttime BTD detection)
FOG_FILE = OUTPUT_DIR / "study_area_fog_80days_goes16.tif"

OUTPUT_FILE = OUTPUT_DIR / "study_area_redwood_suitable.tif"
GROUND_TRUTH_FILE = Path("web/ground_truth_points.csv")


def combine_layers():
    """Combine rainfall and fog suitability into final layer."""
    print("Combining Suitability Layers")
    print("="*60)

    # Load rainfall suitability
    print("\nLoading rainfall layer...")
    with rasterio.open(RAINFALL_FILE) as src:
        rainfall_suitable = src.read(1)
        meta = src.meta.copy()
        transform = src.transform
        print(f"  Shape: {rainfall_suitable.shape}")
        print(f"  Suitable pixels: {(rainfall_suitable == 1).sum():,}")

    # Load fog suitability
    print("\nLoading fog layer...")
    with rasterio.open(FOG_FILE) as src:
        fog_suitable = src.read(1)
        print(f"  Shape: {fog_suitable.shape}")
        print(f"  Suitable pixels: {(fog_suitable == 1).sum():,}")

    # Check alignment
    if rainfall_suitable.shape != fog_suitable.shape:
        raise ValueError(f"Shape mismatch: rainfall={rainfall_suitable.shape}, fog={fog_suitable.shape}")

    # Combine: both criteria must be met
    print("\nCombining criteria (rainfall AND fog)...")
    combined_suitable = ((rainfall_suitable == 1) & (fog_suitable == 1)).astype(np.uint8)

    # Handle nodata
    rainfall_nodata = (rainfall_suitable == 255)
    fog_nodata = (fog_suitable == 255)
    combined_nodata = rainfall_nodata | fog_nodata
    combined_suitable[combined_nodata] = 255

    suitable_count = (combined_suitable == 1).sum()
    total_count = (combined_suitable < 255).sum()
    suitable_pct = 100 * suitable_count / total_count if total_count > 0 else 0

    print(f"\nFinal suitability:")
    print(f"  Suitable pixels: {suitable_count:,} / {total_count:,} ({suitable_pct:.1f}%)")

    # Save combined layer
    output_meta = meta.copy()
    output_meta.update({
        'dtype': 'uint8',
        'nodata': 255
    })

    print(f"\nSaving combined suitability: {OUTPUT_FILE}")
    with rasterio.open(OUTPUT_FILE, 'w', **output_meta) as dst:
        dst.write(combined_suitable, 1)
        dst.set_band_description(1, "Redwood suitable habitat (1=suitable, 0=not suitable, 255=nodata)")

    return combined_suitable, transform, meta


def validate_ground_truth(suitable, transform):
    """Validate suitability at ground truth points."""
    print("\n" + "="*60)
    print("VALIDATION: Ground Truth Points")
    print("="*60)

    # Load ground truth
    df = pd.read_csv(GROUND_TRUTH_FILE, quotechar="'")

    print(f"\nChecking {len(df)} ground truth points:")
    print()

    all_suitable = True

    for idx, row in df.iterrows():
        lat, lon = row['latitude'], row['longitude']
        name = row['notes']

        # Convert to pixel coordinates
        py, px = rowcol(transform, lon, lat)

        # Check bounds
        if 0 <= py < suitable.shape[0] and 0 <= px < suitable.shape[1]:
            is_suitable = suitable[py, px] == 1

            if is_suitable:
                print(f"✓ PASS: {name}")
                print(f"   Location: ({lat:.4f}, {lon:.4f})")
            else:
                print(f"✗ FAIL: {name}")
                print(f"   Location: ({lat:.4f}, {lon:.4f})")
                all_suitable = False
        else:
            print(f"✗ OUT OF BOUNDS: {name}")
            all_suitable = False

    print()
    print("="*60)

    if all_suitable:
        print("✓ SUCCESS: All ground truth points are in suitable habitat!")
    else:
        print("✗ WARNING: Some ground truth points failed validation")

    print("="*60)

    return all_suitable


def generate_summary_stats(suitable, rainfall_file, fog_file):
    """Generate summary statistics."""
    print("\n" + "="*60)
    print("SUMMARY STATISTICS")
    print("="*60)

    # Load continuous layers for stats
    with rasterio.open(rainfall_file.replace('_20in.tif', '_total.tif')) as src:
        rainfall_total = src.read(1)

    with rasterio.open(fog_file.replace('_80days_goes16.tif', '_days_goes16.tif')) as src:
        fog_days = src.read(1)

    # Get stats for suitable areas only
    suitable_mask = suitable == 1

    if suitable_mask.sum() > 0:
        print(f"\nFor suitable habitat areas:")
        print(f"  Rainfall range: {rainfall_total[suitable_mask].min():.1f} - {rainfall_total[suitable_mask].max():.1f} inches")
        print(f"  Rainfall mean: {rainfall_total[suitable_mask].mean():.1f} inches")
        print(f"  Fog days range: {fog_days[suitable_mask].min():.1f} - {fog_days[suitable_mask].max():.1f} days")
        print(f"  Fog days mean: {fog_days[suitable_mask].mean():.1f} days")

    print()
    print("="*60)


def main():
    print("\n" + "="*60)
    print("REDWOOD HABITAT SUITABILITY - Final Combination")
    print("="*60)
    print()
    print("Implementing the academic heuristic:")
    print("  1. North of San Simeon (35.6°N) - ✓ ALL study-area pixels qualify")
    print("  2. Wet season rainfall >= 20 inches")
    print("  3. Afternoon fog >= 80 days/dry season")
    print()

    print(f"Fog data source: GOES-16 satellite nighttime BTD analysis")
    print(f"Fog file: {FOG_FILE.name}")
    print(f"Fog detection: Nighttime only (06-12 UTC = 11pm-5am PST)")
    print()

    # Combine layers
    suitable, transform, meta = combine_layers()

    # Validate
    validation_passed = validate_ground_truth(suitable, transform)

    # Summary stats
    generate_summary_stats(suitable, str(RAINFALL_FILE), str(FOG_FILE))

    print("\n✓ Suitability layer creation complete!")
    print(f"\nOutput files:")
    print(f"  - {OUTPUT_FILE}")
    print(f"  - {OUTPUT_DIR}/study_area_rainfall_total.tif")
    print(f"  - {OUTPUT_DIR}/study_area_fog_days_goes16.tif")
    print()
    print("Next step: Generate web tiles for browser visualization")
    print("  Run: See tickets/21_production_web_tiles.md")

    if validation_passed:
        print("\n" + "="*60)
        print("✓ PROTOTYPE VALIDATION: SUCCESS")
        print("="*60)
        print("All ground truth points fall within suitable habitat.")
        print("The heuristic appears to work correctly for known redwood locations.")
        print("="*60)


if __name__ == "__main__":
    main()
