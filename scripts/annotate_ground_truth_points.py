#!/usr/bin/env python3
"""
Annotate web/ground_truth_points.csv and web/negative_points.csv (in place)
with sampled values from the suitability inputs, plus diagnostic fog
measurements from every fog product we have on disk.

The first block of columns drives the live rule (suitability.combine):
  rainfall_inches    — wet-season total (PRISM)
  fog_days           — GOES-16 nighttime BTD climatology (study_area_fog_days_goes16.tif)
  coldest_tmin_c     — coldest-month mean tmin (PRISM)
  hottest_tmax_c     — hottest-month mean tmax (PRISM)
  is_suitable        — 1/0 by the rule in scripts/suitability.py

The diagnostic block samples additional fog products at the same points so
we can see, per site, which products separate positives from negatives:
  fog_goes18_day     — GOES-18 daytime Ch2 albedo > 0.25 (study_area_fog_days_daytime.tif).
                       Units: fog-days per dry season (same as fog_days).
  fog_modis_dpm      — Werner et al. 2022 MODIS Monthly FLCC, Jun–Sep 2018–2022
                       per-point mean. Units: fog-days per month.
  fog_torre_dec      — Torregrosa 2016 decadal FLCC (Jun–Sep 1999–2009 mean,
                       full diurnal). Units: hours/day.
  fog_torre_day      — Torregrosa daytime FLCC. Units: hours/day.
  fog_torre_night    — Torregrosa nighttime FLCC. Units: hours/day.

After writing the CSVs, print a per-product separation summary:
  positives min..max (mean), negatives min..max (mean), min(pos) − max(neg).
This is the table that tells us which fog product (if any) admits a clean
threshold for the current ground truth set.

Run:
  uv run python scripts/annotate_ground_truth_points.py
"""

import csv
import sys
from pathlib import Path
from statistics import mean

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
FOG_FILE = ROOT / "outputs" / "study_area_fog_days_goes16.tif"
LAND_FILE = ROOT / "outputs" / "study_area_land_mask.tif"
COLDEST_TMIN_FILE = ROOT / "outputs" / "study_area_coldest_month_tmin.tif"
HOTTEST_TMAX_FILE = ROOT / "outputs" / "study_area_hottest_month_tmax.tif"

# Diagnostic fog product inputs (ticket 34 + GOES-18 daytime as the other option).
GOES18_DAY_FILE = ROOT / "outputs" / "study_area_fog_days_daytime.tif"
MODIS_DIR = ROOT / "data" / "MODIS_Monthly_FLCC_Rasters_2000-2022"
TORRE_DIR = ROOT / "data" / "summertime_fog_decadal_rasters" / "decadal_rasters"
MODIS_YEARS = range(2018, 2023)  # recent window, roughly aligned with PRISM 1991–2020 normals
MODIS_MONTHS = (6, 7, 8, 9)

# Both published products encode NoData as float32 -FLT_MAX.
PUBLISHED_NODATA_SENTINEL = -1e30


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


def sample_published(path, coords):
    """Sample a published-fog raster (MODIS or Torregrosa), treating
    -FLT_MAX-ish sentinels as None."""
    with rasterio.open(path) as src:
        out = []
        for vals in src.sample(coords, indexes=1):
            v = float(vals[0])
            out.append(None if v < PUBLISHED_NODATA_SENTINEL else v)
    return out


def sample_modis_mean(coords):
    """Per-point mean fog-days/month across MODIS Jun–Sep 2018–2022 tiles."""
    per_point = [[] for _ in coords]
    for year in MODIS_YEARS:
        for month in MODIS_MONTHS:
            tif = MODIS_DIR / f"{year}-{month:02d}.tif"
            if not tif.exists():
                continue
            vals = sample_published(tif, coords)
            for i, v in enumerate(vals):
                if v is not None:
                    per_point[i].append(v)
    return [mean(vs) if vs else None for vs in per_point]


def annotate(csv_path, label):
    df = pd.read_csv(csv_path, quotechar="'")
    print(f"Loaded {len(df)} {label} from {csv_path.relative_to(ROOT)}")

    coords = list(zip(df["longitude"], df["latitude"]))
    rain = sample(RAINFALL_FILE, coords)
    fog = sample(FOG_FILE, coords)
    land = sample(LAND_FILE, coords)
    coldest = sample(COLDEST_TMIN_FILE, coords)
    hottest = sample(HOTTEST_TMAX_FILE, coords)

    # Diagnostic fog products
    fog_g18d = sample(GOES18_DAY_FILE, coords)
    fog_modis = sample_modis_mean(coords)
    fog_torre_dec = sample_published(TORRE_DIR / "flcc_decadal", coords)
    fog_torre_day = sample_published(TORRE_DIR / "flcc_deca_day", coords)
    fog_torre_night = sample_published(TORRE_DIR / "flcc_deca_nit", coords)

    df["rainfall_inches"] = [round(r, 2) if r is not None else None for r in rain]
    df["fog_days"] = [round(f, 1) if f is not None else None for f in fog]
    df["coldest_tmin_c"] = [round(c, 2) if c is not None else None for c in coldest]
    df["hottest_tmax_c"] = [round(h, 2) if h is not None else None for h in hottest]
    df["fog_goes18_day"] = [round(v, 1) if v is not None else None for v in fog_g18d]
    df["fog_modis_dpm"] = [round(v, 2) if v is not None else None for v in fog_modis]
    df["fog_torre_dec"] = [round(v, 2) if v is not None else None for v in fog_torre_dec]
    df["fog_torre_day"] = [round(v, 2) if v is not None else None for v in fog_torre_day]
    df["fog_torre_night"] = [round(v, 2) if v is not None else None for v in fog_torre_night]
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


def separation_table(positives, negatives):
    """For each fog product column, print min(pos)..max(pos) vs min(neg)..max(neg)
    and the min(pos) − max(neg) gap. Positive gap = clean threshold exists."""
    products = [
        ("fog_days",         "GOES-16 nighttime (days/season)"),
        ("fog_goes18_day",   "GOES-18 daytime (days/season)"),
        ("fog_modis_dpm",    "MODIS Werner (days/month)"),
        ("fog_torre_dec",    "Torregrosa decadal (hr/day)"),
        ("fog_torre_day",    "Torregrosa daytime (hr/day)"),
        ("fog_torre_night",  "Torregrosa nighttime (hr/day)"),
    ]
    print("=" * 78)
    print("Per-product separation between positive and negative control points")
    print("=" * 78)
    print(f"{'Product':35s}  {'Pos n':>5s}  {'Pos range (mean)':>22s}  "
          f"{'Neg n':>5s}  {'Neg range (mean)':>22s}  {'gap':>7s}")
    print("-" * 110)
    for col, label in products:
        pos = positives[col].dropna().tolist()
        neg = negatives[col].dropna().tolist()
        if not pos or not neg:
            print(f"{label:35s}  {len(pos):>5d}  {'(insufficient)':>22s}  "
                  f"{len(neg):>5d}  {'(insufficient)':>22s}  {'—':>7s}")
            continue
        pos_str = f"{min(pos):.2f}–{max(pos):.2f} ({mean(pos):.2f})"
        neg_str = f"{min(neg):.2f}–{max(neg):.2f} ({mean(neg):.2f})"
        gap = min(pos) - max(neg)
        marker = "CLEAN" if gap > 0 else ""
        print(f"{label:35s}  {len(pos):>5d}  {pos_str:>22s}  "
              f"{len(neg):>5d}  {neg_str:>22s}  {gap:>+7.2f}  {marker}")
    print()
    print("Notes:")
    print("  - Units differ per product; compare *within* a row, not across rows.")
    print("  - Gap > 0 means a single threshold cleanly separates pos from neg on")
    print("    this product alone. Gap < 0 means the classes overlap — fog alone")
    print("    can't separate them at any threshold on this product.")
    print("  - Negative points outside a product's footprint (e.g. inland east of")
    print("    Torregrosa's coastal frame) are dropped via NoData, which inflates")
    print("    that product's apparent cleanness. Watch the n column.")
    print()


def per_site_fog_table(positives, negatives):
    """Side-by-side per-site readout of every fog product, sorted by class."""
    print("=" * 78)
    print("Per-site fog values across all products")
    print("=" * 78)
    header = (f"{'site':38s}  {'kind':>4s}  "
              f"{'G16n':>7s}  {'G18d':>7s}  {'MODIS':>7s}  "
              f"{'Tdec':>6s}  {'Tday':>6s}  {'Tnit':>6s}")
    print(header)
    print("-" * len(header))

    def row(r, kind):
        site = (r.get("notes") or "").replace("'", "")
        def f(col, digits):
            v = r.get(col)
            if pd.isna(v):
                return "—"
            return f"{v:.{digits}f}"
        print(f"{site[:38]:38s}  {kind:>4s}  "
              f"{f('fog_days', 1):>7s}  {f('fog_goes18_day', 1):>7s}  "
              f"{f('fog_modis_dpm', 2):>7s}  "
              f"{f('fog_torre_dec', 2):>6s}  {f('fog_torre_day', 2):>6s}  "
              f"{f('fog_torre_night', 2):>6s}")

    for _, r in positives.iterrows():
        row(r, "POS")
    for _, r in negatives.iterrows():
        row(r, "NEG")
    print()


def main():
    print(
        f"Thresholds (live rule): rain ≥ {RAINFALL_THRESHOLD_INCHES} in, "
        f"fog ≥ {FOG_DAYS_THRESHOLD} nights (GOES-16 nighttime BTD), "
        f"coldest tmin ≥ {COLDEST_MONTH_TMIN_FLOOR_C} °C, "
        f"hottest tmax ≤ {HOTTEST_MONTH_TMAX_CEILING_C} °C"
    )
    print()
    pos = annotate(POSITIVES_CSV, "positive ground-truth points")
    neg = annotate(NEGATIVES_CSV, "negative control points")
    per_site_fog_table(pos, neg)
    separation_table(pos, neg)


if __name__ == "__main__":
    main()
