#!/usr/bin/env python3
"""
Create the daytime fog layer from GOES-18 ABI Channel 2 subsets.

Method (Ticket 22 Option A — Rastogi et al. 2016, threshold tuned vs ground truth):
  1. For each scan in 17–21 UTC (10 AM – 2 PM PDT), threshold the Ch2
     reflectance: albedo > 0.25 ⇒ low cloud / fog. Window covers late-morning
     marine layer through early-afternoon burnoff.
  2. A "daytime fog day" at a pixel = any in-window scan that day classifies
     low cloud at that pixel.
  3. Aggregate sample-period fog days; extrapolate to the 184-day dry season.

Outputs:
  outputs/study_area_fog_days_daytime.tif      — float32 fog days/season
  outputs/study_area_fog_threshold_daytime.tif — uint8 binary >= FOG_DAYS_THRESHOLD

Reprojection: GOES-18 fixed-grid → WGS84 → PRISM grid via nearest-neighbor
KDTree mapping precomputed once and reused for every scan.
"""

import json
import re
from collections import defaultdict
from pathlib import Path

import netCDF4 as nc
import numpy as np
import rasterio
from pyproj import Transformer
from scipy.spatial import cKDTree

from suitability import FOG_DAYS_THRESHOLD

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "goes18_daytime"
OUTPUT_DIR = ROOT / "outputs"
BBOX_FILE = OUTPUT_DIR / "study_area_bbox.json"
REFERENCE_FILE = OUTPUT_DIR / "study_area_rainfall_20in.tif"

FOG_REFLECTANCE_THRESHOLD = 0.25
DRY_SEASON_DAYS = 184

GOES18_LON = -137.0
GOES18_HEIGHT = 35786023.0
GOES18_PROJ = (
    f"+proj=geos +lon_0={GOES18_LON} +h={GOES18_HEIGHT} "
    "+a=6378137.0 +b=6356752.31414 +sweep=x +units=m +no_defs"
)
WGS84 = "+proj=longlat +datum=WGS84 +no_defs"

SANITY_POINTS = [
    # Known-good redwood sites (should have many fog days)
    ("Muir Woods",            37.8959, -122.5755),
    ("Humboldt Redwoods",     40.3147, -123.9780),
    ("Redwood Regional Park", 37.8237, -122.1758),
    # Known-dry inland controls (should have few)
    ("Sacramento",            38.5816, -121.4944),
    ("Davis",                 38.5449, -121.7405),
    ("Ukiah (interior)",      39.1502, -123.2078),
]


def parse_filename(fn):
    m = re.search(r"C02_G18_s(\d{14})", fn)
    if not m:
        return None
    s = m.group(1)
    return {
        "year": int(s[0:4]),
        "doy": int(s[4:7]),
        "hour": int(s[7:9]),
        "minute": int(s[9:11]),
    }


def load_bbox():
    with open(BBOX_FILE) as f:
        return json.load(f)


def goes_xy_to_lonlat(x_rad, y_rad):
    """Project GOES-18 fixed-grid radians → WGS84 lon/lat."""
    xx, yy = np.meshgrid(x_rad * GOES18_HEIGHT, y_rad * GOES18_HEIGHT)
    fwd = Transformer.from_crs(GOES18_PROJ, WGS84, always_xy=True)
    lons, lats = fwd.transform(xx.ravel(), yy.ravel())
    return lons.reshape(xx.shape), lats.reshape(xx.shape)


def build_output_grid():
    with rasterio.open(REFERENCE_FILE) as src:
        meta = src.meta.copy()
        transform = src.transform
        h, w = src.shape
    rows, cols = np.mgrid[0:h, 0:w]
    lons = transform.c + (cols + 0.5) * transform.a
    lats = transform.f + (rows + 0.5) * transform.e
    return {"shape": (h, w), "meta": meta, "transform": transform,
            "lons": lons, "lats": lats}


def precompute_goes_to_output_mapping(sample_file, output_grid, bbox):
    """KDTree-based nearest-GOES-pixel index for every output cell."""
    ds = nc.Dataset(sample_file, "r")
    x_rad = ds.variables["x"][:].astype(np.float64)
    y_rad = ds.variables["y"][:].astype(np.float64)
    ds.close()

    goes_lons, goes_lats = goes_xy_to_lonlat(x_rad, y_rad)
    valid = (
        (goes_lats >= bbox["min_lat"]) & (goes_lats <= bbox["max_lat"]) &
        (goes_lons >= bbox["min_lon"]) & (goes_lons <= bbox["max_lon"])
    )
    valid_idx = np.flatnonzero(valid.ravel())
    if valid_idx.size == 0:
        raise RuntimeError("No GOES pixels fall inside study bbox.")

    pts = np.column_stack([goes_lons.ravel()[valid_idx],
                           goes_lats.ravel()[valid_idx]])
    tree = cKDTree(pts)

    out_pts = np.column_stack([output_grid["lons"].ravel(),
                               output_grid["lats"].ravel()])
    _, neighbor = tree.query(out_pts, k=1)
    # neighbor indexes into valid_idx -> back to flat GOES index
    flat_indices = valid_idx[neighbor]
    return {
        "goes_shape": goes_lons.shape,
        "flat_indices": flat_indices,
        "x_rad": x_rad,
        "y_rad": y_rad,
    }


def aggregate(files, mapping, output_shape):
    """For each (year, doy), OR-merge fog masks across all scans that day."""
    h, w = output_shape
    flat_idx = mapping["flat_indices"]
    fog_per_day = {}
    skipped = 0

    for i, fp in enumerate(files, 1):
        info = parse_filename(fp.name)
        if info is None:
            skipped += 1
            continue
        ds = nc.Dataset(fp, "r")
        cmi = ds.variables["CMI"][:]
        ds.close()
        if hasattr(cmi, "filled"):
            cmi = cmi.filled(np.nan)
        cmi_flat = np.asarray(cmi, dtype=np.float32).ravel()
        if cmi_flat.size != mapping["goes_shape"][0] * mapping["goes_shape"][1]:
            # Subset shape mismatch — should never happen if all files
            # came from the same download; bail loudly.
            raise RuntimeError(
                f"shape mismatch on {fp.name}: "
                f"got {cmi_flat.size}, expected "
                f"{mapping['goes_shape'][0] * mapping['goes_shape'][1]}"
            )
        fog_goes = (cmi_flat > FOG_REFLECTANCE_THRESHOLD)
        fog_out = fog_goes[flat_idx].reshape(h, w)
        key = (info["year"], info["doy"])
        if key in fog_per_day:
            fog_per_day[key] |= fog_out
        else:
            fog_per_day[key] = fog_out.copy()
        if i % 100 == 0 or i == len(files):
            print(f"  processed {i}/{len(files)} scans  "
                  f"({len(fog_per_day)} unique days so far)")

    if skipped:
        print(f"  skipped {skipped} files (filename parse failed)")
    return fog_per_day


def save_layers(fog_days_grid, output_grid):
    out_meta = output_grid["meta"].copy()
    out_meta.update({"dtype": "float32", "nodata": -9999.0})
    cont_path = OUTPUT_DIR / "study_area_fog_days_daytime.tif"
    with rasterio.open(cont_path, "w", **out_meta) as dst:
        dst.write(fog_days_grid.astype(np.float32), 1)
        dst.set_band_description(
            1, "Daytime fog days per dry season "
               "(GOES-18 Ch2 albedo > 0.30, 19-21 UTC; extrapolated to 184 days)"
        )

    binary = (fog_days_grid >= FOG_DAYS_THRESHOLD).astype(np.uint8)
    binary[fog_days_grid < 0] = 255
    bin_meta = output_grid["meta"].copy()
    bin_meta.update({"dtype": "uint8", "nodata": 255})
    bin_path = OUTPUT_DIR / "study_area_fog_threshold_daytime.tif"
    with rasterio.open(bin_path, "w", **bin_meta) as dst:
        dst.write(binary, 1)
        dst.set_band_description(
            1, f"Daytime fog days >= {FOG_DAYS_THRESHOLD} (GOES-18 Ch2 albedo)"
        )

    return cont_path, bin_path


def print_sanity(fog_days_grid, output_grid):
    transform = output_grid["transform"]
    h, w = output_grid["shape"]
    print()
    print("Sanity check — fog days at known points:")
    for name, lat, lon in SANITY_POINTS:
        col = int((lon - transform.c) / transform.a - 0.5)
        row = int((lat - transform.f) / transform.e - 0.5)
        if 0 <= row < h and 0 <= col < w:
            v = float(fog_days_grid[row, col])
            print(f"  {name:<25} ({lat:6.3f}, {lon:7.3f}): {v:6.1f} fog days")
        else:
            print(f"  {name:<25} (out of grid)")


def main():
    print("=" * 70)
    print("Daytime fog layer (GOES-18 Ch2 albedo > 0.30)")
    print("=" * 70)

    files = sorted(DATA_DIR.glob("OR_ABI-L2-CMIPC-M6C02_G18_*.nc"))
    if not files:
        raise SystemExit(f"No subset files in {DATA_DIR} — run script 18 first.")
    print(f"Subset files: {len(files)}")

    bbox = load_bbox()
    output_grid = build_output_grid()
    print(f"Output grid: {output_grid['shape']}")

    print("Precomputing GOES → output-grid nearest-neighbor map...")
    mapping = precompute_goes_to_output_mapping(files[0], output_grid, bbox)
    print(f"  GOES subset shape: {mapping['goes_shape']}")

    print("\nAggregating fog masks into per-day OR ...")
    fog_per_day = aggregate(files, mapping, output_grid["shape"])
    sample_days = len(fog_per_day)
    print(f"\nUnique sample days: {sample_days}")

    fog_days_count = np.zeros(output_grid["shape"], dtype=np.int32)
    for arr in fog_per_day.values():
        fog_days_count += arr.astype(np.int32)
    print(f"Per-pixel fog-day count range: {int(fog_days_count.min())}–"
          f"{int(fog_days_count.max())}")

    factor = DRY_SEASON_DAYS / sample_days
    fog_days_grid = fog_days_count.astype(np.float32) * factor
    print(f"Extrapolation factor: {factor:.3f}  "
          f"({sample_days} sampled → {DRY_SEASON_DAYS} dry-season days)")
    print(f"Extrapolated fog days range: {fog_days_grid.min():.1f}–"
          f"{fog_days_grid.max():.1f}  (mean {fog_days_grid.mean():.1f})")

    cont, binp = save_layers(fog_days_grid, output_grid)
    print(f"\nWrote:")
    print(f"  {cont}")
    print(f"  {binp}")

    print_sanity(fog_days_grid, output_grid)
    print()
    print("Next: uv run python scripts/04_combine_suitability.py")


if __name__ == "__main__":
    main()
