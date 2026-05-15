#!/usr/bin/env python3
"""
Annotate web/ground_truth_points.csv and web/negative_points.csv (in place)
with sampled values from the suitability inputs.

Adds columns:
  rainfall_inches    — wet-season total (PRISM, study_area_rainfall_total.tif)
  fog_days           — dry-season fog days (study_area_fog_days_daytime.tif)
  coldest_tmin_c     — coldest-month mean tmin (study_area_coldest_month_tmin.tif)
  hottest_tmax_c     — hottest-month mean tmax (study_area_hottest_month_tmax.tif)
  is_suitable        — 1/0 by the rule from scripts/suitability.py:
                       rain ≥ RAINFALL_THRESHOLD_INCHES
                         AND fog ≥ FOG_DAYS_THRESHOLD
                         AND on land
                         AND coldest_tmin ≥ COLDEST_MONTH_TMIN_FLOOR_C
                         AND hottest_tmax ≤ HOTTEST_MONTH_TMAX_CEILING_C

Suitability is computed point-by-point from the raster values, using the same
constants the pipeline uses — so the column should agree with the binary
study_area_redwood_suitable.tif at each pixel. Negative points are off-range
controls (Central Valley, Mt Shasta, etc.) and should annotate as is_suitable=0.

Run:
  uv run python scripts/annotate_ground_truth_points.py
"""

import csv
import sys
from pathlib import Path

import pandas as pd
import rasterio

sys.path.insert(0, str(Path(__file__).resolve().parent))
from suitability import (
    RAINFALL_THRESHOLD_INCHES,
    FOG_DAYS_THRESHOLD,
    COLDEST_MONTH_TMIN_FLOOR_C,
    HOTTEST_MONTH_TMAX_CEILING_C,
)

ROOT = Path(__file__).resolve().parent.parent
POSITIVES_CSV = ROOT / "web" / "ground_truth_points.csv"
NEGATIVES_CSV = ROOT / "web" / "negative_points.csv"
RAINFALL_FILE = ROOT / "outputs" / "study_area_rainfall_total.tif"
FOG_FILE = ROOT / "outputs" / "study_area_fog_days_daytime.tif"
LAND_FILE = ROOT / "outputs" / "study_area_land_mask.tif"
COLDEST_TMIN_FILE = ROOT / "outputs" / "study_area_coldest_month_tmin.tif"
HOTTEST_TMAX_FILE = ROOT / "outputs" / "study_area_hottest_month_tmax.tif"


def sample(path, coords):
    """Sample a single-band raster at (lon, lat) coords; return list of floats
    (or None where the value matches the raster's nodata)."""
    with rasterio.open(path) as src:
        nodata = src.nodata
        out = []
        for vals in src.sample(coords, indexes=1):
            v = vals[0]
            if nodata is not None and v == nodata:
                out.append(None)
            else:
                out.append(float(v))
    return out


def annotate(csv_path, label):
    df = pd.read_csv(csv_path, quotechar="'")
    print(f"Loaded {len(df)} {label} from {csv_path.relative_to(ROOT)}")

    coords = list(zip(df["longitude"], df["latitude"]))
    rain = sample(RAINFALL_FILE, coords)
    fog = sample(FOG_FILE, coords)
    land = sample(LAND_FILE, coords)
    coldest = sample(COLDEST_TMIN_FILE, coords)
    hottest = sample(HOTTEST_TMAX_FILE, coords)

    df["rainfall_inches"] = [round(r, 2) if r is not None else None for r in rain]
    df["fog_days"] = [round(f, 1) if f is not None else None for f in fog]
    df["coldest_tmin_c"] = [round(c, 2) if c is not None else None for c in coldest]
    df["hottest_tmax_c"] = [round(h, 2) if h is not None else None for h in hottest]
    df["is_suitable"] = [
        int(bool(
            r is not None and f is not None and l is not None
            and c is not None and h is not None
            and r >= RAINFALL_THRESHOLD_INCHES
            and f >= FOG_DAYS_THRESHOLD
            and l == 1
            and c >= COLDEST_MONTH_TMIN_FLOOR_C
            and h <= HOTTEST_MONTH_TMAX_CEILING_C
        ))
        for r, f, l, c, h in zip(rain, fog, land, coldest, hottest)
    ]

    df.to_csv(csv_path, index=False, quotechar="'", quoting=csv.QUOTE_MINIMAL)
    print(f"Wrote annotated CSV in place: {csv_path.relative_to(ROOT)}")
    print()
    print(df.to_string(index=False))
    print()
    return df


def main():
    print(
        f"Thresholds: rain ≥ {RAINFALL_THRESHOLD_INCHES} in, "
        f"fog ≥ {FOG_DAYS_THRESHOLD} days, "
        f"coldest tmin ≥ {COLDEST_MONTH_TMIN_FLOOR_C} °C, "
        f"hottest tmax ≤ {HOTTEST_MONTH_TMAX_CEILING_C} °C"
    )
    print()
    annotate(POSITIVES_CSV, "positive ground-truth points")
    annotate(NEGATIVES_CSV, "negative control points")


if __name__ == "__main__":
    main()
