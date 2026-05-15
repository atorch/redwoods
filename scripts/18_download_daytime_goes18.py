#!/usr/bin/env python3
"""
Download GOES-18 ABI Channel 2 (visible, 0.64 µm) for daytime fog detection.

Per ticket 22 (Option A — Rastogi 2016 albedo threshold):
- 15/16/17/18/19/20/21 UTC (8 AM – 2 PM PDT) — morning marine layer through
  early afternoon. Ticket 33 extended the window earlier from a 17 UTC start
  because Torregrosa et al. 2016 found inland-incursion FLCC "often dissipates
  earlier than 10:30 A.M.", so a 10 AM start under-detects deep canyon sites
  (Eel/Russian River valleys) that depend on morning marine layer.
- 6 weeks per dry season (May / June / mid-July / late-July / Aug / Sept),
  7 days each, 2023-2025. July is the climatological peak coastal-fog month.
- 2 scans/hour = 10 scans/day × 42 days/year × 3 years = 1260 files.

Each CONUS Ch2 file is ~70 MB. We subset to the study-area bbox on download
(~5% of CONUS) and delete the full file, so the persisted archive stays small.

Aborts early if free disk falls below MIN_FREE_GB so we can't fill the disk.
"""

import json
import os
import subprocess
import sys
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import netCDF4 as nc
import numpy as np
from pyproj import Transformer

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "data" / "goes18_daytime"
BBOX_FILE = ROOT / "outputs" / "study_area_bbox.json"

YEARS = [2023, 2024, 2025]
WEEKS = [
    {"name": "May (early dry season)",       "start_doy": 127, "end_doy": 133, "num_days": 7},
    {"name": "June (early peak fog)",        "start_doy": 162, "end_doy": 168, "num_days": 7},
    {"name": "mid-July (peak fog month)",    "start_doy": 190, "end_doy": 196, "num_days": 7},
    {"name": "late-July (peak fog month)",   "start_doy": 205, "end_doy": 211, "num_days": 7},
    {"name": "August (mid fog season)",      "start_doy": 225, "end_doy": 231, "num_days": 7},
    {"name": "September (late dry season)",  "start_doy": 260, "end_doy": 266, "num_days": 7},
]
DAYTIME_HOURS = [15, 16, 17, 18, 19, 20, 21]
CHANNEL = 2
SCANS_PER_HOUR = 2

BUCKET = "noaa-goes18"
PRODUCT = "ABI-L2-CMIPC"

GOES18_LON = -137.0
GOES18_HEIGHT = 35786023.0
GOES18_PROJ = (
    f"+proj=geos +lon_0={GOES18_LON} +h={GOES18_HEIGHT} "
    "+a=6378137.0 +b=6356752.31414 +sweep=x +units=m +no_defs"
)
WGS84 = "+proj=longlat +datum=WGS84 +no_defs"

MIN_FREE_GB = 5.0
MAX_WORKERS = 8
TMP_DIR = OUTPUT_DIR / "_tmp"
_print_lock = threading.Lock()
# libnetCDF4/libhdf5 isn't thread-safe; serialize all reads/writes.
_nc_lock = threading.Lock()


def log(msg):
    with _print_lock:
        print(msg, flush=True)


def free_gb(path):
    s = os.statvfs(path)
    return s.f_bavail * s.f_frsize / (1024**3)


def assert_disk_ok(min_gb=MIN_FREE_GB):
    avail = free_gb(OUTPUT_DIR)
    if avail < min_gb:
        log(f"\n✗ ABORTING: only {avail:.1f} GB free on disk (threshold {min_gb} GB)")
        sys.exit(1)


def load_bbox():
    with open(BBOX_FILE) as f:
        return json.load(f)


def compute_goes_xy_bounds(bbox, pad_deg=0.1):
    """Bounding rectangle of bbox (lat/lon) projected into GOES-18 fixed-grid radians."""
    fwd = Transformer.from_crs(WGS84, GOES18_PROJ, always_xy=True)
    lon_min = bbox["min_lon"] - pad_deg
    lon_max = bbox["max_lon"] + pad_deg
    lat_min = bbox["min_lat"] - pad_deg
    lat_max = bbox["max_lat"] + pad_deg
    lon_mid = (lon_min + lon_max) / 2
    lat_mid = (lat_min + lat_max) / 2
    lons = [lon_min, lon_max, lon_min, lon_max, lon_mid, lon_mid, lon_min, lon_max]
    lats = [lat_min, lat_min, lat_max, lat_max, lat_min, lat_max, lat_mid, lat_mid]
    xm, ym = fwd.transform(lons, lats)
    x_rad = np.array(xm) / GOES18_HEIGHT
    y_rad = np.array(ym) / GOES18_HEIGHT
    return float(x_rad.min()), float(x_rad.max()), float(y_rad.min()), float(y_rad.max())


def list_files(year, doy, hour, channel):
    s3_path = f"s3://{BUCKET}/{PRODUCT}/{year}/{doy:03d}/{hour:02d}/"
    try:
        result = subprocess.run(
            ["aws", "s3", "ls", s3_path, "--no-sign-request"],
            capture_output=True, text=True, check=True,
        )
    except subprocess.CalledProcessError:
        return []
    files = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split()
        if len(parts) >= 4:
            fn = parts[3]
            if f"C{channel:02d}_G18" in fn and "M6" in fn:
                files.append(fn)
    files.sort()
    return files


def download_and_subset(s3_url, subset_path, x_bounds, y_bounds):
    """Download one CMIPC file, slice CMI to the bbox, and write a compact NetCDF.

    Thread-safe: each call writes the raw download to a per-call tmp path under
    TMP_DIR. Uses netCDF4 directly (xarray's HDF5-backed `to_netcdf` segfaults
    in this env).
    """
    assert_disk_ok()
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    tmp_path = TMP_DIR / f"_dl_{uuid.uuid4().hex}.nc"
    subprocess.run(
        ["aws", "s3", "cp", s3_url, str(tmp_path), "--no-sign-request"],
        check=True, capture_output=True,
    )
    try:
        with _nc_lock:
            src = nc.Dataset(tmp_path, "r")
            try:
                x = src.variables["x"][:]
                y = src.variables["y"][:]
                x_min, x_max = x_bounds
                y_min, y_max = y_bounds
                xi = np.where((x >= x_min) & (x <= x_max))[0]
                yi = np.where((y >= y_min) & (y <= y_max))[0]
                if len(xi) == 0 or len(yi) == 0:
                    raise ValueError("subset empty — bbox missed the grid")
                x_slice = slice(int(xi[0]), int(xi[-1]) + 1)
                y_slice = slice(int(yi[0]), int(yi[-1]) + 1)
                cmi = src.variables["CMI"][y_slice, x_slice]
                if hasattr(cmi, "filled"):
                    cmi = cmi.filled(np.nan).astype(np.float32)
                else:
                    cmi = np.asarray(cmi, dtype=np.float32)
                time_coverage_start = getattr(src, "time_coverage_start", "")
                proj_attrs = {}
                if "goes_imager_projection" in src.variables:
                    p = src.variables["goes_imager_projection"]
                    proj_attrs = {a: p.getncattr(a) for a in p.ncattrs()}
                x_sub = np.array(x[x_slice], dtype=np.float64)
                y_sub = np.array(y[y_slice], dtype=np.float64)
            finally:
                src.close()

            if subset_path.exists():
                subset_path.unlink()
            dst = nc.Dataset(subset_path, "w", format="NETCDF4")
            try:
                dst.createDimension("y", len(y_sub))
                dst.createDimension("x", len(x_sub))
                cmi_var = dst.createVariable(
                    "CMI", "f4", ("y", "x"),
                    zlib=True, complevel=4, fill_value=np.float32(np.nan),
                )
                cmi_var[:] = cmi
                cmi_var.long_name = "Cloud and Moisture Imagery reflectance factor"
                cmi_var.units = "1"
                x_var = dst.createVariable("x", "f8", ("x",))
                x_var[:] = x_sub
                x_var.units = "rad"
                x_var.long_name = "GOES fixed grid projection x-coordinate"
                y_var = dst.createVariable("y", "f8", ("y",))
                y_var[:] = y_sub
                y_var.units = "rad"
                y_var.long_name = "GOES fixed grid projection y-coordinate"
                dst.satellite = "GOES-18"
                dst.channel = 2
                dst.time_coverage_start = time_coverage_start
                for a, v in proj_attrs.items():
                    try:
                        dst.setncattr(f"projection_{a}", v)
                    except Exception:
                        pass
            finally:
                dst.close()
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    assert_disk_ok(min_gb=10.0)

    bbox = load_bbox()
    x_min, x_max, y_min, y_max = compute_goes_xy_bounds(bbox)
    log("=" * 70)
    log("GOES-18 daytime Ch2 download (subset on download)")
    log("=" * 70)
    log(f"Bbox lat: [{bbox['min_lat']:.4f}, {bbox['max_lat']:.4f}]  "
        f"lon: [{bbox['min_lon']:.4f}, {bbox['max_lon']:.4f}]")
    log(f"GOES-18 x_rad: [{x_min:.5f}, {x_max:.5f}]   "
        f"y_rad: [{y_min:.5f}, {y_max:.5f}]")
    log(f"Years: {YEARS}")
    log(f"Daytime hours UTC: {DAYTIME_HOURS}")
    log(f"Scans/hour: {SCANS_PER_HOUR}  | Workers: {MAX_WORKERS}")
    log(f"Free disk: {free_gb(OUTPUT_DIR):.1f} GB (abort threshold {MIN_FREE_GB} GB)")
    log("")

    log("Listing S3 keys for all (year, doy, hour) slots...")
    download_jobs = []
    skipped_existing = 0
    for year in YEARS:
        for week in WEEKS:
            for doy in range(week["start_doy"], week["end_doy"] + 1):
                for hour in DAYTIME_HOURS:
                    available = list_files(year, doy, hour, CHANNEL)
                    if not available:
                        log(f"  no S3 files: {year} DOY {doy:03d} H{hour:02d}")
                        continue
                    for fn in available[:SCANS_PER_HOUR]:
                        out = OUTPUT_DIR / fn
                        if out.exists():
                            skipped_existing += 1
                            continue
                        s3_url = (f"s3://{BUCKET}/{PRODUCT}/{year}/"
                                  f"{doy:03d}/{hour:02d}/{fn}")
                        download_jobs.append((s3_url, out))

    log(f"Jobs queued: {len(download_jobs)} (already-present: {skipped_existing})")
    log("")

    manifest = {
        "download_date": datetime.now().isoformat(),
        "bucket": BUCKET, "product": PRODUCT, "channel": CHANNEL,
        "years": YEARS, "weeks": WEEKS,
        "daytime_hours_utc": DAYTIME_HOURS,
        "scans_per_hour": SCANS_PER_HOUR,
        "bbox": bbox,
        "goes18_x_rad_bounds": [x_min, x_max],
        "goes18_y_rad_bounds": [y_min, y_max],
        "files_downloaded": 0,
        "files_skipped_existing": skipped_existing,
        "files_failed": 0,
    }

    counter = {"done": 0}
    counter_lock = threading.Lock()

    def task(job):
        s3_url, out = job
        try:
            download_and_subset(s3_url, out, (x_min, x_max), (y_min, y_max))
            return ("ok", out.name, None)
        except Exception as e:
            return ("err", out.name, repr(e))

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = [ex.submit(task, j) for j in download_jobs]
        for fut in as_completed(futures):
            status, name, err = fut.result()
            with counter_lock:
                counter["done"] += 1
                done = counter["done"]
            if status == "ok":
                manifest["files_downloaded"] += 1
            else:
                manifest["files_failed"] += 1
                log(f"  ✗ {name}: {err}")
            if done % 25 == 0 or done == len(download_jobs):
                log(f"  [{done}/{len(download_jobs)}] downloaded={manifest['files_downloaded']} "
                    f"failed={manifest['files_failed']}  "
                    f"free disk {free_gb(OUTPUT_DIR):.1f} GB")

    # Cleanup tmp dir
    try:
        for p in TMP_DIR.glob("*"):
            p.unlink()
        TMP_DIR.rmdir()
    except Exception:
        pass

    manifest["files_total"] = (manifest["files_downloaded"]
                               + manifest["files_skipped_existing"])
    manifest_path = OUTPUT_DIR / "download_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    log("")
    log("=" * 70)
    log(f"✓ archive: {manifest['files_total']} files  "
        f"(downloaded {manifest['files_downloaded']}, "
        f"skipped {manifest['files_skipped_existing']}, "
        f"failed {manifest['files_failed']})")
    log(f"  Manifest: {manifest_path}")
    log(f"  Free disk: {free_gb(OUTPUT_DIR):.1f} GB")
    log("=" * 70)


if __name__ == "__main__":
    main()
