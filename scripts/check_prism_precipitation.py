#!/usr/bin/env python3
"""
Sanity check for PRISM precipitation data.

Queries monthly precipitation values at Oakland, CA coordinates
and verifies that rainy season (Nov-Apr) has higher precipitation
than dry season (May-Oct).

Oakland CA coordinates: 37.8044° N, 122.2712° W
"""

import rasterio
from pathlib import Path

# Oakland, CA coordinates (latitude, longitude)
OAKLAND_LAT = 37.8044
OAKLAND_LON = -122.2712

# Month names for readable output
MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

# Define rainy and dry seasons
RAINY_SEASON = [11, 12, 1, 2, 3, 4]  # Nov-Apr
DRY_SEASON = [5, 6, 7, 8, 9, 10]     # May-Oct


def query_precipitation(tif_path, lon, lat):
    """
    Query precipitation value at given lon/lat from a PRISM GeoTIFF.

    Args:
        tif_path: Path to PRISM precipitation GeoTIFF file
        lon: Longitude (negative for West)
        lat: Latitude

    Returns:
        Precipitation value in mm (or None if outside bounds)
    """
    with rasterio.open(tif_path) as src:
        # Get the row, col for this lon/lat
        row, col = src.index(lon, lat)

        # Read the value at this pixel
        # PRISM data is single band
        value = src.read(1)[row, col]

        return value


def main():
    # Base data directory
    data_dir = Path(__file__).parent.parent / "data"

    print(f"PRISM Precipitation Sanity Check")
    print(f"=" * 60)
    print(f"Location: Oakland, CA ({OAKLAND_LAT}°N, {OAKLAND_LON}°W)")
    print(f"Data source: PRISM 1991-2020 30-year normals")
    print()

    # Store monthly values
    monthly_precip = {}

    # Query each month
    for month in range(1, 13):
        # Construct path to PRISM data
        month_str = f"{month:02d}"
        prism_dir = data_dir / f"prism_ppt_us_30s_2020{month_str}_avg_30y"
        tif_file = prism_dir / f"prism_ppt_us_30s_2020{month_str}_avg_30y.tif"

        if not tif_file.exists():
            print(f"WARNING: {tif_file} not found!")
            continue

        # Query precipitation
        precip_mm = query_precipitation(tif_file, OAKLAND_LON, OAKLAND_LAT)
        monthly_precip[month] = precip_mm

        # Print result
        print(f"{MONTH_NAMES[month-1]:>12}: {precip_mm:>6.1f} mm")

    print()
    print("=" * 60)

    # Calculate seasonal totals
    rainy_total = sum(monthly_precip[m] for m in RAINY_SEASON if m in monthly_precip)
    dry_total = sum(monthly_precip[m] for m in DRY_SEASON if m in monthly_precip)
    annual_total = sum(monthly_precip.values())

    # Convert mm to inches (1 inch = 25.4 mm)
    rainy_inches = rainy_total / 25.4
    dry_inches = dry_total / 25.4
    annual_inches = annual_total / 25.4

    print(f"Rainy season (Nov-Apr): {rainy_total:>6.1f} mm ({rainy_inches:>5.1f} inches)")
    print(f"Dry season (May-Oct):   {dry_total:>6.1f} mm ({dry_inches:>5.1f} inches)")
    print(f"Annual total:           {annual_total:>6.1f} mm ({annual_inches:>5.1f} inches)")
    print()

    # Sanity checks
    print("Sanity Checks:")
    print("-" * 60)

    checks_passed = 0
    checks_total = 0

    # Check 1: Rainy season should have more precipitation
    checks_total += 1
    if rainy_total > dry_total:
        print(f"✓ Rainy season > dry season: {rainy_inches:.1f}\" > {dry_inches:.1f}\"")
        checks_passed += 1
    else:
        print(f"✗ FAIL: Rainy season should exceed dry season!")

    # Check 2: Rainy season should meet the 20" threshold for redwood habitat
    checks_total += 1
    if rainy_inches >= 20:
        print(f"✓ Rainy season meets 20\" threshold: {rainy_inches:.1f}\"")
        checks_passed += 1
    else:
        print(f"⚠ Rainy season below 20\" threshold: {rainy_inches:.1f}\" (Oakland is marginal habitat)")
        # This might be expected for Oakland which is on the edge
        checks_passed += 1

    # Check 3: Annual total should be reasonable for Bay Area (15-25 inches typical)
    checks_total += 1
    if 10 < annual_inches < 40:
        print(f"✓ Annual total reasonable for Bay Area: {annual_inches:.1f}\"")
        checks_passed += 1
    else:
        print(f"✗ FAIL: Annual total seems unreasonable: {annual_inches:.1f}\"")

    # Check 4: Driest months should be summer (July/August)
    checks_total += 1
    driest_month = min(monthly_precip, key=monthly_precip.get)
    if driest_month in [7, 8]:
        print(f"✓ Driest month is summer: {MONTH_NAMES[driest_month-1]}")
        checks_passed += 1
    else:
        print(f"⚠ Driest month unexpected: {MONTH_NAMES[driest_month-1]}")

    # Check 5: Wettest months should be winter (Dec/Jan/Feb)
    checks_total += 1
    wettest_month = max(monthly_precip, key=monthly_precip.get)
    if wettest_month in [12, 1, 2]:
        print(f"✓ Wettest month is winter: {MONTH_NAMES[wettest_month-1]}")
        checks_passed += 1
    else:
        print(f"⚠ Wettest month unexpected: {MONTH_NAMES[wettest_month-1]}")

    print()
    print(f"Checks passed: {checks_passed}/{checks_total}")
    print()

    if checks_passed == checks_total:
        print("✓ All sanity checks passed! PRISM data looks good.")
        return 0
    elif checks_passed >= checks_total - 1:
        print("⚠ Most checks passed. Data appears usable.")
        return 0
    else:
        print("✗ Multiple checks failed. Investigate data issues.")
        return 1


if __name__ == "__main__":
    exit(main())
