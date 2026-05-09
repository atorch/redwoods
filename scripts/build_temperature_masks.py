#!/usr/bin/env python3
"""
Build a binary temperature mask on the study-area grid, from PRISM monthly
tmin and tmax 30-year normals (ticket 32).

Coast redwoods are a maritime species — they don't tolerate prolonged winter
freezes or Central-Valley summer heat. Per the USDA Silvics of North America,
the native range sits between mean annuals of ~10–16 °C with rare drops
below -9 °C and rare highs above 38 °C. Two per-pixel reductions over
the 12 monthly normals capture the envelope:

  coldest_month_tmin = min over 12 months of mean tmin    (°C, continuous)
  hottest_month_tmax = max over 12 months of mean tmax    (°C, continuous)

The mask is the AND of two thresholds drawn from the Silvics range:
  coldest_month_tmin >= COLDEST_MONTH_TMIN_FLOOR_C   (default -3 °C)
  hottest_month_tmax <= HOTTEST_MONTH_TMAX_CEILING_C (default 30 °C)

Resampling: bilinear onto the rainfall template grid. PRISM tmin/tmax share
the native grid with PRISM ppt, so this is near-identity in practice — but
going through reproject() guarantees pixel alignment with the other masks.

Outputs:
  outputs/study_area_coldest_month_tmin.tif — float32 °C (continuous diagnostic)
  outputs/study_area_hottest_month_tmax.tif — float32 °C (continuous diagnostic)
  outputs/study_area_temperature_mask.tif   — uint8, 1 = pass both, 0 = fail
"""

from pathlib import Path

import numpy as np
import rasterio
from rasterio.warp import Resampling, reproject

import suitability

DATA_DIR = Path("data")
OUTPUT_DIR = Path("outputs")
TEMPLATE_FILE = OUTPUT_DIR / "study_area_rainfall_20in.tif"

TMIN_FOLDERS = [f"prism_tmin_us_30s_2020{m:02d}_avg_30y" for m in range(1, 13)]
TMAX_FOLDERS = [f"prism_tmax_us_30s_2020{m:02d}_avg_30y" for m in range(1, 13)]

OUT_TMIN = OUTPUT_DIR / "study_area_coldest_month_tmin.tif"
OUT_TMAX = OUTPUT_DIR / "study_area_hottest_month_tmax.tif"
OUT_MASK = OUTPUT_DIR / "study_area_temperature_mask.tif"

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


def stack_extreme(folders, kind, dst_shape, dst_transform, dst_crs):
    """Per-pixel min or max over a list of monthly rasters."""
    if kind not in ("min", "max"):
        raise ValueError(f"kind must be 'min' or 'max', got {kind!r}")

    months = []
    for folder in folders:
        tif = DATA_DIR / folder / f"{folder}.tif"
        if not tif.exists():
            raise FileNotFoundError(f"missing PRISM raster: {tif}")
        print(f"    {folder}")
        months.append(reproject_onto_template(tif, dst_shape, dst_transform, dst_crs))

    stack = np.stack(months, axis=0)
    nodata_any = (stack == CONT_NODATA).any(axis=0)
    sentinel = np.inf if kind == "min" else -np.inf
    stack = np.where(stack == CONT_NODATA, sentinel, stack)
    result = (stack.min(axis=0) if kind == "min" else stack.max(axis=0)).astype(np.float32)
    result[nodata_any] = CONT_NODATA
    return result


def write_continuous(arr, path, meta_template, description):
    meta = meta_template.copy()
    meta.update({"dtype": "float32", "nodata": float(CONT_NODATA), "count": 1})
    with rasterio.open(path, "w", **meta) as dst:
        dst.write(arr.astype(np.float32), 1)
        dst.set_band_description(1, description)


def main():
    print("Building temperature masks (PRISM tmin/tmax monthly normals)")
    print("=" * 60)

    if not TEMPLATE_FILE.exists():
        raise FileNotFoundError(
            f"template not found: {TEMPLATE_FILE} "
            "(run scripts/01_process_study_area_rainfall.py first)"
        )

    with rasterio.open(TEMPLATE_FILE) as tpl:
        dst_shape = (tpl.height, tpl.width)
        dst_transform = tpl.transform
        dst_crs = tpl.crs
        meta = tpl.meta.copy()

    print(f"  template: {dst_shape[1]}x{dst_shape[0]} {dst_crs}")

    print("\n  reducing 12 tmin monthly rasters → coldest-month tmin (per pixel)")
    coldest = stack_extreme(TMIN_FOLDERS, "min", dst_shape, dst_transform, dst_crs)
    print("\n  reducing 12 tmax monthly rasters → hottest-month tmax (per pixel)")
    hottest = stack_extreme(TMAX_FOLDERS, "max", dst_shape, dst_transform, dst_crs)

    valid_cold = coldest[coldest != CONT_NODATA]
    valid_hot = hottest[hottest != CONT_NODATA]
    print(
        f"\n  coldest_month_tmin: {valid_cold.min():.1f} … {valid_cold.max():.1f} °C "
        f"(mean {valid_cold.mean():.1f})"
    )
    print(
        f"  hottest_month_tmax: {valid_hot.min():.1f} … {valid_hot.max():.1f} °C "
        f"(mean {valid_hot.mean():.1f})"
    )

    print(f"\n  writing {OUT_TMIN}")
    write_continuous(
        coldest, OUT_TMIN, meta,
        "Coldest-month mean tmin across Jan–Dec (°C, PRISM 30-yr normals)",
    )
    print(f"  writing {OUT_TMAX}")
    write_continuous(
        hottest, OUT_TMAX, meta,
        "Hottest-month mean tmax across Jan–Dec (°C, PRISM 30-yr normals)",
    )

    cold_floor = suitability.COLDEST_MONTH_TMIN_FLOOR_C
    hot_ceiling = suitability.HOTTEST_MONTH_TMAX_CEILING_C
    print(
        f"\n  thresholds: coldest_month_tmin >= {cold_floor} °C "
        f"AND hottest_month_tmax <= {hot_ceiling} °C"
    )

    nodata_mask = (coldest == CONT_NODATA) | (hottest == CONT_NODATA)
    pass_mask = (coldest >= cold_floor) & (hottest <= hot_ceiling)
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
        dst.set_band_description(
            1,
            f"Temperate envelope (coldest_tmin>={cold_floor} AND hottest_tmax<={hot_ceiling}, °C)",
        )

    print("\n✓ Temperature masks built.")


if __name__ == "__main__":
    main()
