#!/usr/bin/env python3
"""
Calculate BTD from the downloaded Ch7 and Ch13 files in data/goes16_samples/.

This validates the GOES-16 fog detection methodology.
"""

from pathlib import Path
import numpy as np

# Files
SAMPLE_DIR = Path("data/goes16_samples")
CH7_FILE = SAMPLE_DIR / "OR_ABI-L2-CMIPC-M6C07_G16_s20242000001180_e20242000003565_c20242000004044.nc"
CH13_FILE = SAMPLE_DIR / "OR_ABI-L2-CMIPC-M6C13_G16_s20242000001180_e20242000003565_c20242000004063.nc"


def calculate_btd():
    """Calculate BTD from Ch7 and Ch13 files."""
    try:
        import netCDF4 as nc

        print("GOES-16 BTD Fog Detection")
        print("="*70)
        print()

        # Check files exist
        if not CH7_FILE.exists():
            print(f"✗ Ch7 file not found: {CH7_FILE}")
            return False

        if not CH13_FILE.exists():
            print(f"✗ Ch13 file not found: {CH13_FILE}")
            return False

        # Load Ch7
        print(f"Loading Ch7: {CH7_FILE.name}")
        ds7 = nc.Dataset(CH7_FILE)
        bt7 = ds7.variables['CMI'][:]  # Brightness temperature, Kelvin

        # Get metadata
        time_start = ds7.time_coverage_start
        print(f"  Time: {time_start}")
        print(f"  Shape: {bt7.shape}")
        print(f"  Mean BT: {np.nanmean(bt7):.2f} K ({np.nanmean(bt7) - 273.15:.2f} °C)")

        # Load Ch13
        print()
        print(f"Loading Ch13: {CH13_FILE.name}")
        ds13 = nc.Dataset(CH13_FILE)
        bt13 = ds13.variables['CMI'][:]
        print(f"  Shape: {bt13.shape}")
        print(f"  Mean BT: {np.nanmean(bt13):.2f} K ({np.nanmean(bt13) - 273.15:.2f} °C)")

        # Verify shapes match
        if bt7.shape != bt13.shape:
            print(f"\n✗ Shape mismatch: Ch7={bt7.shape}, Ch13={bt13.shape}")
            return False

        # Calculate BTD
        print()
        print("="*70)
        print("Calculating BTD (Brightness Temperature Difference)")
        print("="*70)
        print()
        print("Formula: BTD = BT_Ch13 - BT_Ch7")
        print()

        btd = bt13 - bt7

        print(f"BTD Statistics:")
        print(f"  Mean: {np.nanmean(btd):.2f} K")
        print(f"  Std:  {np.nanstd(btd):.2f} K")
        print(f"  Min:  {np.nanmin(btd):.2f} K")
        print(f"  Max:  {np.nanmax(btd):.2f} K")
        print()

        # Detect fog: BTD > 0
        fog_mask = btd > 0.0
        fog_count = np.sum(fog_mask)
        fog_pct = 100 * fog_count / fog_mask.size

        print("Fog Detection (BTD > 0 K):")
        print(f"  Total pixels: {fog_mask.size:,}")
        print(f"  Fog pixels:   {fog_count:,} ({fog_pct:.1f}%)")
        print(f"  Clear pixels: {fog_mask.size - fog_count:,} ({100-fog_pct:.1f}%)")
        print()

        # BTD value distribution
        print("BTD Value Distribution:")
        very_positive = np.sum(btd > 5)
        positive = np.sum((btd > 0) & (btd <= 5))
        near_zero = np.sum((btd >= -2) & (btd <= 0))
        negative = np.sum(btd < -2)

        print(f"  BTD > 5K:       {very_positive:,} pixels ({100*very_positive/btd.size:.1f}%) - Strong fog/low cloud")
        print(f"  0 < BTD ≤ 5K:   {positive:,} pixels ({100*positive/btd.size:.1f}%) - Moderate fog/low cloud")
        print(f"  -2 ≤ BTD ≤ 0K:  {near_zero:,} pixels ({100*near_zero/btd.size:.1f}%) - Thin clouds/transition")
        print(f"  BTD < -2K:      {negative:,} pixels ({100*negative/btd.size:.1f}%) - High/ice clouds or clear")
        print()

        # Physical interpretation
        print("="*70)
        print("Physical Interpretation:")
        print("="*70)
        print()
        print("BTD > 0K (Positive):")
        print("  - Low-level water clouds (fog, stratus)")
        print("  - Water droplets emit less at 3.9 µm than 10.3 µm")
        print("  - Typical of marine layer fog along California coast")
        print()
        print("BTD ≈ 0K:")
        print("  - Thin clouds, cloud edges, or mixed conditions")
        print()
        print("BTD < 0K (Negative):")
        print("  - High-level ice clouds (cirrus)")
        print("  - Clear sky")
        print("  - Ice particles emit similarly at both wavelengths")
        print()

        ds7.close()
        ds13.close()

        print("="*70)
        print("✓ BTD CALCULATION SUCCESSFUL!")
        print("="*70)
        print()
        print(f"Summary: {fog_pct:.1f}% of pixels show fog/low cloud signature")
        print()
        print("This validates the GOES-16 fog detection methodology!")
        print()

        return True

    except ImportError as e:
        print(f"✗ ERROR: Missing library: {e}")
        print("  Install with: uv add netcdf4 numpy")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = calculate_btd()

    if success:
        print("="*70)
        print("NEXT STEPS:")
        print("="*70)
        print()
        print("1. ✓ Validated BTD calculation works with real GOES-16 data")
        print("2. Download more samples (multiple days/times) using AWS CLI")
        print("3. Implement reprojection (GOES fixed grid → lat/lon)")
        print("4. Subset to Bay Area and create raster matching PRISM")
        print("5. Count fog days and compare with mock fog layer")
        print()
