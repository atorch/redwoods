#!/usr/bin/env python3
"""
Build a binary land mask on the study-area grid, from USDA CDL.

The suitability raster otherwise leaks green into the Pacific and SF Bay
wherever ocean/inland-water pixels happen to satisfy the rain + fog criteria.
This step adds the third AND in the rule: `suitable AND is_land`.

Strategy: resample the 10m national CDL to the coarser study grid using
"mode" (dominant class per output cell), then classify each class as
land or water. Ocean is outside the CDL footprint; reproject fills those
cells with `dst_nodata=0`, which we treat as water.

Water/not-land classes:
  0    Background / NoData (offshore or unclassified)
  83   Aquaculture
  111  Open Water
  112  Perennial Ice/Snow
  190  Woody Wetlands
  195  Herbaceous Wetlands

Output:
  outputs/study_area_land_mask.tif — uint8, 1 = land, 0 = water
"""

from pathlib import Path

import numpy as np
import rasterio
from rasterio.warp import Resampling, reproject

DATA_DIR = Path("data")
OUTPUT_DIR = Path("outputs")

CDL_FILE = DATA_DIR / "2025_10m_cdls" / "2025_10m_cdls.tif"
TEMPLATE_FILE = OUTPUT_DIR / "study_area_rainfall_20in.tif"  # defines the target grid
OUTPUT_FILE = OUTPUT_DIR / "study_area_land_mask.tif"

WATER_CLASSES = np.array([0, 83, 111, 112, 190, 195], dtype=np.uint8)


def main():
    print("Building land mask from CDL")
    print("=" * 60)
    print(f"  Source:   {CDL_FILE}")
    print(f"  Template: {TEMPLATE_FILE}")

    if not CDL_FILE.exists():
        raise FileNotFoundError(f"CDL raster not found: {CDL_FILE}")
    if not TEMPLATE_FILE.exists():
        raise FileNotFoundError(
            f"Template raster not found: {TEMPLATE_FILE} "
            f"(run scripts/01_process_study_area_rainfall.py first)"
        )

    with rasterio.open(TEMPLATE_FILE) as tpl:
        dst_shape = (tpl.height, tpl.width)
        dst_transform = tpl.transform
        dst_crs = tpl.crs
        output_meta = tpl.meta.copy()

    cdl_resampled = np.zeros(dst_shape, dtype=np.uint8)

    with rasterio.open(CDL_FILE) as src:
        print(
            f"  Reprojecting {src.width}x{src.height} @10m {src.crs} "
            f"→ {dst_shape[1]}x{dst_shape[0]} {dst_crs} (mode)..."
        )
        reproject(
            source=rasterio.band(src, 1),
            destination=cdl_resampled,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=dst_transform,
            dst_crs=dst_crs,
            dst_nodata=0,  # offshore / outside CDL footprint → 0 → treated as water
            resampling=Resampling.mode,
        )

    water_mask = np.isin(cdl_resampled, WATER_CLASSES)
    land_mask = (~water_mask).astype(np.uint8)

    total = land_mask.size
    land_count = int(land_mask.sum())
    print(
        f"  Land pixels: {land_count:,} / {total:,} "
        f"({100 * land_count / total:.1f}%)"
    )

    output_meta.update({"dtype": "uint8", "nodata": 255, "count": 1})
    print(f"  Writing: {OUTPUT_FILE}")
    with rasterio.open(OUTPUT_FILE, "w", **output_meta) as dst:
        dst.write(land_mask, 1)
        dst.set_band_description(1, "Land mask (1=land, 0=water; CDL-derived)")

    print("✓ Land mask built.")


if __name__ == "__main__":
    main()
