#!/usr/bin/env python3
"""
Phase-2 evaluation for ticket 34: sample the two published fog products at our
positive and negative control points and check whether either separates them.

Products evaluated:
  - Werner et al. 2022 MODIS Monthly FLCC (data/MODIS_Monthly_FLCC_Rasters_2000-2022)
      1 km, days-per-month of fog/low cloud, Jun–Sep 2000–2022.
      Averaged across Jun–Sep over a recent window to produce a per-point
      mean "fog-days per dry-season month".
  - Torregrosa et al. 2016 decadal FLCC (data/summertime_fog_decadal_rasters/decadal_rasters)
      4 km, hours-per-day of fog/low cloud, Jun–Sep 1999–2009 climatology.
      `flcc_decadal` = full diurnal mean; `flcc_deca_day` = daytime-only.

Run:
  uv run python scripts/eval_published_fog_rasters.py
"""

import csv
from pathlib import Path
from statistics import mean

import pandas as pd
import rasterio

ROOT = Path(__file__).resolve().parent.parent
POSITIVES_CSV = ROOT / "web" / "ground_truth_points.csv"
NEGATIVES_CSV = ROOT / "web" / "negative_points.csv"

MODIS_DIR = ROOT / "data" / "MODIS_Monthly_FLCC_Rasters_2000-2022"
TORRE_DIR = ROOT / "data" / "summertime_fog_decadal_rasters" / "decadal_rasters"

# Average MODIS across this window to roughly match the PRISM 1991–2020 normals
# we use elsewhere, while still being recent enough to reflect current climatology.
MODIS_YEARS = range(2018, 2023)  # 2018..2022 inclusive
MODIS_MONTHS = (6, 7, 8, 9)

NODATA_SENTINEL = -3.4028234663852886e38  # both products use float32 -FLT_MAX


def is_valid(v):
    return v is not None and v > -1e30


def sample_point(src, lon, lat):
    val = next(src.sample([(lon, lat)], indexes=1))[0]
    return float(val) if is_valid(val) else None


def sample_modis_mean(coords):
    """Mean fog-days/month across all (year, month) MODIS rasters in the window.
    Returns one value per point; None if every tile is NoData at that point."""
    per_point_values = [[] for _ in coords]
    for year in MODIS_YEARS:
        for month in MODIS_MONTHS:
            tif = MODIS_DIR / f"{year}-{month:02d}.tif"
            if not tif.exists():
                continue
            with rasterio.open(tif) as src:
                for i, (lon, lat) in enumerate(coords):
                    v = sample_point(src, lon, lat)
                    if v is not None:
                        per_point_values[i].append(v)
    return [mean(vs) if vs else None for vs in per_point_values]


def sample_torre(coords, grid_name):
    """Sample a Torregrosa ESRI Arc/Info Binary Grid (directory, no extension)."""
    path = TORRE_DIR / grid_name
    with rasterio.open(path) as src:
        return [sample_point(src, lon, lat) for lon, lat in coords]


def load_points(csv_path, kind):
    df = pd.read_csv(csv_path, quotechar="'")
    df["kind"] = kind
    df["site"] = df["notes"].str.replace("'", "", regex=False)
    return df


def fmt(v, digits=2):
    if v is None:
        return "NoData"
    return f"{v:.{digits}f}"


def summarize(label, positives, negatives):
    pos_clean = [v for v in positives if v is not None]
    neg_clean = [v for v in negatives if v is not None]
    if not pos_clean or not neg_clean:
        print(f"  {label}: insufficient data")
        return
    pos_lo = min(pos_clean)
    neg_hi = max(neg_clean)
    gap = pos_lo - neg_hi
    print(
        f"  {label}: "
        f"positives {min(pos_clean):.2f}–{max(pos_clean):.2f} "
        f"(mean {mean(pos_clean):.2f}, n={len(pos_clean)});  "
        f"negatives {min(neg_clean):.2f}–{max(neg_clean):.2f} "
        f"(mean {mean(neg_clean):.2f}, n={len(neg_clean)});  "
        f"min(pos) − max(neg) = {gap:+.2f}  "
        f"{'(clean separation)' if gap > 0 else '(overlap)'}"
    )


def main():
    pos = load_points(POSITIVES_CSV, "positive")
    neg = load_points(NEGATIVES_CSV, "negative")
    all_pts = pd.concat([pos, neg], ignore_index=True)
    coords = list(zip(all_pts["longitude"], all_pts["latitude"]))

    print(
        f"Sampling MODIS (Werner) — {len(list(MODIS_YEARS))} years × "
        f"{len(MODIS_MONTHS)} months, mean fog-days/month..."
    )
    modis_vals = sample_modis_mean(coords)

    print("Sampling Torregrosa decadal (Jun–Sep mean, hours/day)...")
    torre_dec = sample_torre(coords, "flcc_decadal")
    print("Sampling Torregrosa decadal daytime-only (hours/day)...")
    torre_day = sample_torre(coords, "flcc_deca_day")

    all_pts["modis_fog_days_per_month"] = modis_vals
    all_pts["torre_decadal_hr_per_day"] = torre_dec
    all_pts["torre_daytime_hr_per_day"] = torre_day

    # Table
    print()
    print(
        f"{'site':38s} {'kind':>8s} {'our_fog':>8s} {'MODIS':>8s} {'Torre_dec':>10s} {'Torre_day':>10s}"
    )
    print("-" * 90)
    for _, r in all_pts.iterrows():
        our_fog = r.get("fog_days")
        our_fog_str = fmt(our_fog, 1) if pd.notna(our_fog) else "—"
        print(
            f"{r['site'][:38]:38s} {r['kind']:>8s} "
            f"{our_fog_str:>8s} "
            f"{fmt(r['modis_fog_days_per_month']):>8s} "
            f"{fmt(r['torre_decadal_hr_per_day']):>10s} "
            f"{fmt(r['torre_daytime_hr_per_day']):>10s}"
        )

    # Separation summary
    print()
    print("Separation between positive and negative classes:")
    for col, label in [
        ("modis_fog_days_per_month", "MODIS days/month"),
        ("torre_decadal_hr_per_day", "Torregrosa decadal hr/day"),
        ("torre_daytime_hr_per_day", "Torregrosa daytime hr/day"),
    ]:
        pos_vals = all_pts.loc[all_pts["kind"] == "positive", col].dropna().tolist()
        neg_vals = all_pts.loc[all_pts["kind"] == "negative", col].dropna().tolist()
        summarize(label, pos_vals, neg_vals)

    # Inland-incursion failure cases from the ticket
    print()
    print("Inland-incursion sites that fail in our current layer:")
    for site_substr in ("Armstrong", "Humboldt", "Navarro"):
        sub = all_pts[all_pts["site"].str.contains(site_substr, case=False, na=False)]
        for _, r in sub.iterrows():
            print(
                f"  {r['site'][:38]:38s} "
                f"ours={fmt(r['fog_days'], 1)}  "
                f"MODIS={fmt(r['modis_fog_days_per_month'])}  "
                f"Torre_dec={fmt(r['torre_decadal_hr_per_day'])}  "
                f"Torre_day={fmt(r['torre_daytime_hr_per_day'])}"
            )

    print()
    print("False-positive site in our current layer:")
    sub = all_pts[all_pts["site"].str.contains("Shasta", case=False, na=False)]
    for _, r in sub.iterrows():
        print(
            f"  {r['site'][:38]:38s} "
            f"ours={fmt(r['fog_days'], 1)}  "
            f"MODIS={fmt(r['modis_fog_days_per_month'])}  "
            f"Torre_dec={fmt(r['torre_decadal_hr_per_day'])}  "
            f"Torre_day={fmt(r['torre_daytime_hr_per_day'])}"
        )


if __name__ == "__main__":
    main()
