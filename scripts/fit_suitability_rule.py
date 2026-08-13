#!/usr/bin/env python3
"""
POC: fit a half-plane suitability rule from positive ground truth and negative
control points using logistic regression on (rainfall, fog).

This is ticket 30 stage 2 — the *first cut* 2-variable fit. It doesn't yet
include a fog floor or a dry-season-rainfall variable; both are still in the
ticket as planned refinements.

Run:
  uv run python scripts/fit_suitability_rule.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from sklearn.linear_model import LogisticRegression

sys.path.insert(0, str(Path(__file__).resolve().parent))
from suitability import (
    RAINFALL_THRESHOLD_INCHES,
    FOG_DAYS_THRESHOLD,
    COLDEST_MONTH_TMIN_FLOOR_C,
    HOTTEST_MONTH_TMAX_CEILING_C,
)

ROOT = Path(__file__).resolve().parent.parent
POS_CSV = ROOT / "web" / "ground_truth_points.csv"
NEG_CSV = ROOT / "web" / "negative_points.csv"
RAIN_FILE = ROOT / "outputs" / "study_area_rainfall_total.tif"
FOG_FILE = ROOT / "outputs" / "study_area_fog_days_goes16.tif"
LAND_FILE = ROOT / "outputs" / "study_area_land_mask.tif"
COLDEST_TMIN_FILE = ROOT / "outputs" / "study_area_coldest_month_tmin.tif"
HOTTEST_TMAX_FILE = ROOT / "outputs" / "study_area_hottest_month_tmax.tif"


def sample(path, coords):
    """Sample a raster at (lon, lat) coords; return list of floats, or None
    if the point is out of bounds or hits a nodata pixel."""
    with rasterio.open(path) as src:
        nodata = src.nodata
        bounds = src.bounds
        out = []
        for (lon, lat), vals in zip(coords, src.sample(coords, indexes=1)):
            in_bounds = (bounds.left <= lon <= bounds.right
                         and bounds.bottom <= lat <= bounds.top)
            if not in_bounds:
                out.append(None)
                continue
            v = vals[0]
            if nodata is not None and v == nodata:
                out.append(None)
            else:
                out.append(float(v))
    return out


def load_and_sample(csv_path, label):
    df = pd.read_csv(csv_path, quotechar="'")
    df["label"] = label
    coords = list(zip(df["longitude"], df["latitude"]))
    df["rainfall_inches"] = sample(RAIN_FILE, coords)
    df["fog_days"] = sample(FOG_FILE, coords)
    df["is_land"] = sample(LAND_FILE, coords)
    df["coldest_tmin_c"] = sample(COLDEST_TMIN_FILE, coords)
    df["hottest_tmax_c"] = sample(HOTTEST_TMAX_FILE, coords)
    df["source"] = csv_path.name
    return df


def main():
    pos = load_and_sample(POS_CSV, 1)
    neg = load_and_sample(NEG_CSV, 0)
    print(f"Loaded {len(pos)} positives, {len(neg)} negatives")

    df = pd.concat([pos, neg], ignore_index=True)
    valid_mask = df["rainfall_inches"].notna() & df["fog_days"].notna()
    dropped = df[~valid_mask]
    if len(dropped):
        print(f"\nDropping {len(dropped)} points outside study bbox (no raster value):")
        for _, r in dropped.iterrows():
            print(f"  [{'pos' if r['label']==1 else 'neg'}] "
                  f"{r['notes']:<45}  ({r['latitude']:.3f}, {r['longitude']:.3f})")

    valid = df[valid_mask].copy()
    n_pos = int((valid.label == 1).sum())
    n_neg = int((valid.label == 0).sum())
    print(f"\nFitting on {len(valid)} points ({n_pos} positives, {n_neg} negatives)")

    X = valid[["rainfall_inches", "fog_days"]].to_numpy()
    y = valid["label"].to_numpy()

    model = LogisticRegression(max_iter=2000)
    model.fit(X, y)

    # Logistic: P(suitable) = sigmoid(alpha*rain + beta*fog + b)
    # Decision boundary at P=0.5: alpha*rain + beta*fog + b = 0
    #   => alpha*rain + beta*fog >= -b
    alpha = float(model.coef_[0][0])
    beta = float(model.coef_[0][1])
    W = float(-model.intercept_[0])

    print()
    print(f"Fitted half-plane:")
    print(f"  {alpha:.4f} * rainfall_inches  +  {beta:.4f} * fog_days  >=  {W:.4f}")
    if alpha > 0:
        print(f"  i.e. rainfall_inches  >=  {W/alpha:.2f}  -  {beta/alpha:.3f} * fog_days")
    if beta > 0:
        print(f"  i.e. fog_days         >=  {W/beta:.2f}  -  {alpha/beta:.3f} * rainfall_inches")

    # Distance to boundary in score units (positive = above boundary)
    valid["score_minus_W"] = alpha * valid["rainfall_inches"] + beta * valid["fog_days"] - W
    is_temperate = (
        (valid["coldest_tmin_c"].fillna(-9e9) >= COLDEST_MONTH_TMIN_FLOOR_C)
        & (valid["hottest_tmax_c"].fillna(9e9) <= HOTTEST_MONTH_TMAX_CEILING_C)
    )
    valid["new_pass"] = (valid["score_minus_W"] >= 0) & (valid["is_land"] == 1) & is_temperate
    valid["box_pass"] = ((valid["rainfall_inches"] >= RAINFALL_THRESHOLD_INCHES)
                        & (valid["fog_days"] >= FOG_DAYS_THRESHOLD)
                        & (valid["is_land"] == 1)
                        & is_temperate)

    print()
    print("Per-point classification (sorted by score):")
    show = valid[["label", "notes", "rainfall_inches", "fog_days",
                  "coldest_tmin_c", "hottest_tmax_c",
                  "score_minus_W", "is_land", "box_pass", "new_pass"]].copy()
    show = show.sort_values("score_minus_W", ascending=False)
    show["label"] = show["label"].map({1: "POS", 0: "NEG"})
    show["box_pass"] = show["box_pass"].map({True: "✓", False: "✗"})
    show["new_pass"] = show["new_pass"].map({True: "✓", False: "✗"})
    show["is_land"] = show["is_land"].map({1.0: "✓", 0.0: "✗"})
    print(show.to_string(index=False))

    print()
    pos_v = valid[valid.label == 1]
    neg_v = valid[valid.label == 0]
    pos_box = int(pos_v["box_pass"].sum())
    pos_new = int(pos_v["new_pass"].sum())
    neg_box = int((~neg_v["box_pass"]).sum())
    neg_new = int((~neg_v["new_pass"]).sum())
    print(f"Positives passing: box {pos_box}/{len(pos_v)}   "
          f"new {pos_new}/{len(pos_v)}")
    print(f"Negatives correctly failing: box {neg_box}/{len(neg_v)}   "
          f"new {neg_new}/{len(neg_v)}")


if __name__ == "__main__":
    main()
