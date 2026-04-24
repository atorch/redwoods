#!/usr/bin/env python3
"""
Process PRISM wet season rainfall for the redwood study area.

The study-area bounding box is derived from the ground-truth points CSV
(plus a margin), so the same pipeline works whether the points cover the
Bay Area, the full northern California coast, or the entire redwood range.

This script:
1. Loads ground truth points to define bounding box
2. Loads PRISM monthly precipitation (Nov-Apr)
3. Crops to study-area bounding box with margin
4. Sums 6 months to get wet season total
5. Creates binary threshold layer (>= 20 inches)

Output:
- study_area_rainfall_total.tif - wet season total (inches)
- study_area_rainfall_20in.tif - binary threshold (1 = suitable, 0 = not)
"""

import pandas as pd
import rasterio
from rasterio.mask import mask
from rasterio.warp import calculate_default_transform, reproject, Resampling
import numpy as np
from pathlib import Path
import json
from shapely.geometry import box

from suitability import RAINFALL_THRESHOLD_INCHES

# Configuration
DATA_DIR = Path("data")
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

GROUND_TRUTH_FILE = Path("web/ground_truth_points.csv")
PRISM_MONTHS = {
    11: "prism_ppt_us_30s_202011_avg_30y",  # November
    12: "prism_ppt_us_30s_202012_avg_30y",  # December
    1: "prism_ppt_us_30s_202001_avg_30y",   # January
    2: "prism_ppt_us_30s_202002_avg_30y",   # February
    3: "prism_ppt_us_30s_202003_avg_30y",   # March
    4: "prism_ppt_us_30s_202004_avg_30y",   # April
}

# Bounding box margin (degrees)
BBOX_MARGIN = 0.3  # ~30km at this latitude


def load_ground_truth_points():
    """Load ground truth points and compute bounding box."""
    print("Loading ground truth points...")
    df = pd.read_csv(GROUND_TRUTH_FILE, quotechar="'")

    print(f"Found {len(df)} ground truth points:")
    for idx, row in df.iterrows():
        print(f"  - {row['notes']}: ({row['latitude']:.4f}, {row['longitude']:.4f})")

    # Compute bounding box with margin
    min_lat = df['latitude'].min() - BBOX_MARGIN
    max_lat = df['latitude'].max() + BBOX_MARGIN
    min_lon = df['longitude'].min() - BBOX_MARGIN
    max_lon = df['longitude'].max() + BBOX_MARGIN

    bbox = {
        'min_lat': min_lat,
        'max_lat': max_lat,
        'min_lon': min_lon,
        'max_lon': max_lon
    }

    print(f"\nStudy area bounding box (with {BBOX_MARGIN}° margin):")
    print(f"  Latitude:  {min_lat:.4f} to {max_lat:.4f}")
    print(f"  Longitude: {min_lon:.4f} to {max_lon:.4f}")

    return df, bbox


def crop_raster_to_bbox(src, bbox):
    """Crop raster to bounding box."""
    # Create bounding box geometry (lon, lat order for shapely)
    geom = box(bbox['min_lon'], bbox['min_lat'],
               bbox['max_lon'], bbox['max_lat'])

    # Crop
    out_image, out_transform = mask(src, [geom], crop=True, filled=True)

    return out_image, out_transform


def process_wet_season_rainfall(bbox):
    """Load, crop, and sum PRISM monthly precipitation."""
    print("\n" + "="*60)
    print("Processing PRISM wet season rainfall (Nov-Apr)...")
    print("="*60)

    monthly_data = []
    reference_meta = None

    for month_num, folder_name in PRISM_MONTHS.items():
        tif_path = DATA_DIR / folder_name / f"{folder_name}.tif"

        if not tif_path.exists():
            raise FileNotFoundError(f"Missing PRISM data: {tif_path}")

        print(f"\nProcessing month {month_num:02d}: {folder_name}")

        with rasterio.open(tif_path) as src:
            # Store reference metadata from first raster
            if reference_meta is None:
                reference_meta = src.meta.copy()
                print(f"  CRS: {src.crs}")
                print(f"  Resolution: {src.res}")
                print(f"  Shape: {src.shape}")

            # Crop to study area bbox
            cropped, transform = crop_raster_to_bbox(src, bbox)

            # Get the data (remove band dimension if present)
            if cropped.ndim == 3:
                cropped = cropped[0]

            # Check for nodata
            nodata = src.nodata
            if nodata is not None:
                valid_mask = cropped != nodata
                print(f"  Valid pixels: {valid_mask.sum()}")
                print(f"  Mean rainfall: {cropped[valid_mask].mean():.2f} mm")
            else:
                print(f"  Mean rainfall: {cropped.mean():.2f} mm")

            monthly_data.append(cropped)

    # Sum all months (PRISM is in mm, convert to inches)
    print("\nSumming wet season rainfall...")
    wet_season_total_mm = np.sum(monthly_data, axis=0)
    wet_season_total_inches = wet_season_total_mm / 25.4

    # Handle nodata
    if reference_meta['nodata'] is not None:
        nodata_mask = monthly_data[0] == reference_meta['nodata']
        wet_season_total_inches[nodata_mask] = -9999.0

    print(f"Wet season total range: {wet_season_total_inches[wet_season_total_inches > 0].min():.1f} to {wet_season_total_inches.max():.1f} inches")
    print(f"Wet season total mean: {wet_season_total_inches[wet_season_total_inches > 0].mean():.1f} inches")

    # Create binary threshold layer
    print(f"\nApplying {RAINFALL_THRESHOLD_INCHES} inch threshold...")
    rainfall_suitable = (wet_season_total_inches >= RAINFALL_THRESHOLD_INCHES).astype(np.uint8)

    if reference_meta['nodata'] is not None:
        rainfall_suitable[nodata_mask] = 255  # Use 255 as nodata for uint8

    suitable_pixels = (rainfall_suitable == 1).sum()
    total_pixels = (rainfall_suitable < 255).sum()
    pct_suitable = 100 * suitable_pixels / total_pixels if total_pixels > 0 else 0

    print(f"Suitable pixels: {suitable_pixels:,} / {total_pixels:,} ({pct_suitable:.1f}%)")

    # Update metadata for output
    output_meta = reference_meta.copy()
    output_meta.update({
        'transform': transform,
        'height': wet_season_total_inches.shape[0],
        'width': wet_season_total_inches.shape[1],
        'count': 1,
        'nodata': -9999.0
    })

    # Save wet season total
    output_path = OUTPUT_DIR / "study_area_rainfall_total.tif"
    print(f"\nSaving wet season total: {output_path}")
    with rasterio.open(output_path, 'w', **output_meta) as dst:
        dst.write(wet_season_total_inches, 1)
        dst.set_band_description(1, f"Wet season (Nov-Apr) precipitation total (inches)")

    # Save binary threshold
    threshold_meta = output_meta.copy()
    threshold_meta.update({
        'dtype': 'uint8',
        'nodata': 255
    })
    output_path = OUTPUT_DIR / "study_area_rainfall_20in.tif"
    print(f"Saving binary threshold: {output_path}")
    with rasterio.open(output_path, 'w', **threshold_meta) as dst:
        dst.write(rainfall_suitable, 1)
        dst.set_band_description(1, f"Rainfall >= {RAINFALL_THRESHOLD_INCHES} inches (1=yes, 0=no)")

    return wet_season_total_inches, rainfall_suitable, output_meta


def validate_at_ground_truth(df, rainfall_suitable, meta):
    """Check rainfall values at ground truth points."""
    print("\n" + "="*60)
    print("Validating at ground truth points...")
    print("="*60)

    from rasterio.transform import rowcol

    for idx, row in df.iterrows():
        lat, lon = row['latitude'], row['longitude']

        # Convert lat/lon to pixel coordinates
        py, px = rowcol(meta['transform'], lon, lat)

        # Check if within bounds
        if 0 <= py < rainfall_suitable.shape[0] and 0 <= px < rainfall_suitable.shape[1]:
            suitable = rainfall_suitable[py, px]
            status = "✓ SUITABLE" if suitable == 1 else "✗ NOT SUITABLE"
            print(f"{status}: {row['notes']}")
        else:
            print(f"✗ OUT OF BOUNDS: {row['notes']}")

    print("="*60)


def main():
    print("Study Area Rainfall Processing")
    print("="*60)

    # Load ground truth and define bbox
    df, bbox = load_ground_truth_points()

    # Save bbox for later use
    bbox_path = OUTPUT_DIR / "study_area_bbox.json"
    with open(bbox_path, 'w') as f:
        json.dump(bbox, f, indent=2)
    print(f"\nSaved bounding box to: {bbox_path}")

    # Process rainfall
    wet_season_total, rainfall_suitable, meta = process_wet_season_rainfall(bbox)

    # Validate
    validate_at_ground_truth(df, rainfall_suitable, meta)

    print("\n✓ Rainfall processing complete!")
    print(f"  Outputs saved to: {OUTPUT_DIR}/")
    print(f"  - study_area_rainfall_total.tif (continuous values)")
    print(f"  - study_area_rainfall_20in.tif (binary threshold)")
    print("\nNext step: Process GOES-16 fog data")


if __name__ == "__main__":
    main()
