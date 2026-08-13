#!/usr/bin/env python3
"""
Build a binary frost-hardiness mask on the study-area grid, from the USDA
Plant Hardiness Zone Map 2023 (PRISM Climate Group) average annual extreme
minimum temperature grid (ticket 36).

Unlike the coldest-month *mean* tmin in build_temperature_masks.py, PHZM is
the mean, across 1991-2020, of each year's single coldest daily-minimum
temperature. That makes it a proxy for "do hard freezes happen here?" rather
than "what's a typical cold day like?" — closer to the biology of what kills
redwood seedlings at the range edge.

Source: https://prism.oregonstate.edu/phzm/ (data/phzm_us_grid_2023.zip).
ESRI BIL, Float32, degrees F, NAD83 geographic, 0.00833deg (~800 m) grid —
same native resolution as the other PRISM normals already in this pipeline.

Resampling: bilinear onto the rainfall template grid, same pattern as
build_temperature_masks.py.

Outputs:
  outputs/study_area_phzm_extreme_min_c.tif — float32 C (continuous diagnostic)
  outputs/study_area_phzm_mask.tif          — uint8, 1 = pass, 0 = fail
"""

from pathlib import Path

import numpy as np
import rasterio
from rasterio.warp import Resampling, reproject

import suitability

DATA_DIR = Path("data")
OUTPUT_DIR = Path("outputs")
TEMPLATE_FILE = OUTPUT_DIR / "study_area_rainfall_20in.tif"

PHZM_BIL = DATA_DIR / "phzm_us_grid_2023" / "phzm_us_grid_2023.bil"

OUT_EXTREME_MIN_C = OUTPUT_DIR / "study_area_phzm_extreme_min_c.tif"
OUT_MASK = OUTPUT_DIR / "study_area_phzm_mask.tif"

CONT_NODATA = np.float32(-9999.0)


def reproject_onto_template(src_path, dst_shape, dst_transform, dst_crs):
    out = np.full(dst_shape, CONT_NODATA, dtype=np.float32)
    with rasterio.open(src_path) as src:
        reproject(
            source=rasterio.band(src, 1),
            destination=out,
            src_transform=src.transform,
            src_crs=src.crs,
            src_nodata=src.nodata,
            dst_transform=dst_transform,
            dst_crs=dst_crs,
            dst_nodata=CONT_NODATA,
            resampling=Resampling.bilinear,
        )
    return out


def main():
    print("Building PHZM frost-hardiness mask (avg annual extreme min temp)")
    print("=" * 60)

    if not TEMPLATE_FILE.exists():
        raise FileNotFoundError(
            f"template not found: {TEMPLATE_FILE} "
            "(run scripts/01_process_study_area_rainfall.py first)"
        )
    if not PHZM_BIL.exists():
        raise FileNotFoundError(
            f"missing PHZM grid: {PHZM_BIL} "
            "(unzip data/phzm_us_grid_2023.zip to data/phzm_us_grid_2023/)"
        )

    with rasterio.open(TEMPLATE_FILE) as tpl:
        dst_shape = (tpl.height, tpl.width)
        dst_transform = tpl.transform
        dst_crs = tpl.crs
        meta = tpl.meta.copy()

    print(f"  template: {dst_shape[1]}x{dst_shape[0]} {dst_crs}")
    print(f"  reprojecting {PHZM_BIL.name} onto template grid")
    extreme_min_f = reproject_onto_template(PHZM_BIL, dst_shape, dst_transform, dst_crs)

    nodata_mask = extreme_min_f == CONT_NODATA
    extreme_min_c = np.where(
        nodata_mask, CONT_NODATA, (extreme_min_f - 32.0) * (5.0 / 9.0)
    ).astype(np.float32)

    valid = extreme_min_c[~nodata_mask]
    print(
        f"\n  avg annual extreme min: {valid.min():.1f} ... {valid.max():.1f} C "
        f"(mean {valid.mean():.1f})"
    )

    print(f"\n  writing {OUT_EXTREME_MIN_C}")
    cont_meta = meta.copy()
    cont_meta.update({"dtype": "float32", "nodata": float(CONT_NODATA), "count": 1})
    with rasterio.open(OUT_EXTREME_MIN_C, "w", **cont_meta) as dst:
        dst.write(extreme_min_c, 1)
        dst.set_band_description(
            1, "Avg annual extreme min temp, 1991-2020 (C, USDA PHZM 2023 / PRISM)"
        )

    floor = suitability.PHZM_EXTREME_MIN_FLOOR_C
    print(f"\n  threshold: avg_annual_extreme_min_c >= {floor} C")
    pass_mask = extreme_min_c >= floor
    out = pass_mask.astype(np.uint8)
    out[nodata_mask] = int(suitability.NODATA)

    valid_pixels = int((out != int(suitability.NODATA)).sum())
    passing = int((out == 1).sum())
    pct = 100 * passing / valid_pixels if valid_pixels else 0.0
    print(f"  passing: {passing:,} / {valid_pixels:,} ({pct:.1f}%)")

    mask_meta = meta.copy()
    mask_meta.update({"dtype": "uint8", "nodata": int(suitability.NODATA), "count": 1})
    print(f"  writing {OUT_MASK}")
    with rasterio.open(OUT_MASK, "w", **mask_meta) as dst:
        dst.write(out, 1)
        dst.set_band_description(1, f"Frost-hardy (avg_annual_extreme_min_c>={floor})")

    print("\nPHZM mask built.")


if __name__ == "__main__":
    main()
