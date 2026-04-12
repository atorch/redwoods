#!/usr/bin/env python3
"""
Create a mock fog suitability layer for Bay Area prototype.

For rapid prototyping, this creates a fog layer based on known fog patterns:
- Coastal areas (within ~20km of ocean) = high fog
- Higher elevations near coast (500-1000m) = high fog
- Inland valleys = low fog
- Central Valley = no fog

This validates the pipeline without waiting for GOES-16 data processing.
Later we'll replace with real GOES-16 BTD analysis.
"""

import numpy as np
import rasterio
from rasterio.transform import from_bounds, xy
from pathlib import Path
import json

# Configuration
OUTPUT_DIR = Path("outputs")
BBOX_FILE = OUTPUT_DIR / "bay_area_bbox.json"
RAINFALL_FILE = OUTPUT_DIR / "bay_area_rainfall_20in.tif"

# Mock fog parameters (based on known Bay Area fog patterns)
# These are rough approximations for prototype purposes
MOCK_FOG_PARAMS = {
    'coastal_fog_zone_degrees': 0.2,  # ~20km from coast
    'pacific_coast_lon': -122.5,  # Approximate Pacific coast longitude
    'fog_penetration_inland': 0.6,  # How far fog reaches inland (degrees) - increased to cover East Bay hills
    'base_fog_days': 60,  # Minimum fog days in fog zone
    'max_fog_days': 140,  # Maximum fog days at coast
}


def load_bbox():
    """Load Bay Area bounding box."""
    with open(BBOX_FILE) as f:
        return json.load(f)


def create_mock_fog_layer(bbox, reference_file):
    """
    Create a mock fog layer based on coastal proximity.

    This is a simplified model:
    - Western (coastal) areas get more fog
    - Fog decreases with distance from coast
    - Areas within ~20km of coast exceed 80-day threshold
    """
    print("Creating mock fog layer...")
    print("="*60)

    # Load reference raster to match resolution and extent
    with rasterio.open(reference_file) as src:
        ref_meta = src.meta.copy()
        ref_transform = src.transform
        ref_shape = src.shape
        print(f"Matching reference raster:")
        print(f"  Shape: {ref_shape}")
        print(f"  Resolution: {src.res}")
        print(f"  CRS: {src.crs}")

    # Create coordinate grids for each pixel center
    height, width = ref_shape

    # Create arrays of row and column indices
    rows, cols = np.mgrid[0:height, 0:width]

    # Apply affine transform to get geographic coordinates
    # ref_transform * (col, row) returns (lon, lat)
    xs = ref_transform.c + (cols + 0.5) * ref_transform.a + (rows + 0.5) * ref_transform.b
    ys = ref_transform.f + (cols + 0.5) * ref_transform.d + (rows + 0.5) * ref_transform.e

    lons = xs
    lats = ys

    print(f"\nLongitude range: {lons.min():.4f} to {lons.max():.4f}")
    print(f"Latitude range: {lats.min():.4f} to {lats.max():.4f}")

    # Mock fog model: fog increases as you get closer to Pacific coast
    # Pacific coast is approximately at longitude -122.5
    coast_lon = MOCK_FOG_PARAMS['pacific_coast_lon']
    max_fog_distance = MOCK_FOG_PARAMS['fog_penetration_inland']

    # Distance from coast (in degrees longitude, positive = inland/east)
    distance_from_coast = lons - coast_lon

    # Normalize distance (0 at coast, 1 at max inland fog reach)
    # Clamp to [0, 1]
    normalized_distance = np.clip(distance_from_coast / max_fog_distance, 0, 1)

    # Fog days decrease with distance from coast
    # This is a simplified linear model
    base_fog = MOCK_FOG_PARAMS['base_fog_days']
    max_fog = MOCK_FOG_PARAMS['max_fog_days']
    fog_days_estimate = base_fog + (max_fog - base_fog) * (1 - normalized_distance)

    # Add some north-south variation (fog is more common in central Bay Area)
    # Peak fog around 37.7-37.8 (San Francisco)
    lat_center = 37.75
    lat_falloff = 0.5
    lat_factor = np.exp(-((lats - lat_center) / lat_falloff) ** 2)
    lat_factor = 0.5 + 0.5 * lat_factor  # Range 0.5 to 1.0

    fog_days_estimate = fog_days_estimate * lat_factor

    print(f"\nMock fog days estimate range: {fog_days_estimate.min():.1f} to {fog_days_estimate.max():.1f} days")

    # Create binary threshold: >= 80 days
    fog_threshold = 80
    fog_suitable = (fog_days_estimate >= fog_threshold).astype(np.uint8)

    suitable_pct = 100 * fog_suitable.sum() / fog_suitable.size
    print(f"\nFog suitable pixels: {fog_suitable.sum():,} / {fog_suitable.size:,} ({suitable_pct:.1f}%)")

    # Save continuous fog days estimate
    output_meta = ref_meta.copy()
    output_meta.update({
        'dtype': 'float32',
        'nodata': -9999.0
    })

    output_path = OUTPUT_DIR / "bay_area_fog_days_estimate.tif"
    print(f"\nSaving fog days estimate: {output_path}")
    with rasterio.open(output_path, 'w', **output_meta) as dst:
        dst.write(fog_days_estimate.astype(np.float32), 1)
        dst.set_band_description(1, "Estimated afternoon fog days per dry season (MOCK DATA)")

    # Save binary threshold
    threshold_meta = ref_meta.copy()
    threshold_meta.update({
        'dtype': 'uint8',
        'nodata': 255
    })

    output_path = OUTPUT_DIR / "bay_area_fog_80days.tif"
    print(f"Saving binary threshold: {output_path}")
    with rasterio.open(output_path, 'w', **threshold_meta) as dst:
        dst.write(fog_suitable, 1)
        dst.set_band_description(1, f"Fog >= {fog_threshold} days (1=yes, 0=no) - MOCK DATA")

    print("\n" + "="*60)
    print("NOTE: This is MOCK DATA based on coastal proximity!")
    print("For production, replace with real GOES-16 BTD analysis.")
    print("="*60)

    return fog_days_estimate, fog_suitable


def validate_at_ground_truth(fog_suitable, fog_days_estimate, reference_file):
    """Check fog values at ground truth points."""
    import pandas as pd
    from rasterio.transform import rowcol

    print("\n" + "="*60)
    print("Validating mock fog at ground truth points...")
    print("="*60)

    # Load ground truth points
    df = pd.read_csv("data/redwood_ground_truth_points.csv", quotechar="'")

    # Get transform from reference file
    with rasterio.open(reference_file) as src:
        transform = src.transform

    for idx, row in df.iterrows():
        lat, lon = row['latitude'], row['longitude']

        # Convert lat/lon to pixel coordinates
        py, px = rowcol(transform, lon, lat)

        # Check if within bounds
        if 0 <= py < fog_suitable.shape[0] and 0 <= px < fog_suitable.shape[1]:
            suitable = fog_suitable[py, px]
            days = fog_days_estimate[py, px]
            status = "✓ SUITABLE" if suitable == 1 else "✗ NOT SUITABLE"
            print(f"{status}: {row['notes']}")
            print(f"  Estimated fog days: {days:.1f}")
        else:
            print(f"✗ OUT OF BOUNDS: {row['notes']}")

    print("="*60)


def main():
    print("Bay Area Mock Fog Layer Creation")
    print("="*60)
    print()
    print("Creating simplified fog layer based on coastal proximity")
    print("to validate the processing pipeline.")
    print()

    # Load bounding box
    bbox = load_bbox()
    print(f"Bay Area bounding box:")
    print(f"  Lat: {bbox['min_lat']:.4f} to {bbox['max_lat']:.4f}")
    print(f"  Lon: {bbox['min_lon']:.4f} to {bbox['max_lon']:.4f}")
    print()

    # Create mock fog layer
    fog_days, fog_suitable = create_mock_fog_layer(bbox, RAINFALL_FILE)

    # Validate
    validate_at_ground_truth(fog_suitable, fog_days, RAINFALL_FILE)

    print("\n✓ Mock fog layer creation complete!")
    print(f"  Outputs saved to: {OUTPUT_DIR}/")
    print(f"  - bay_area_fog_days_estimate.tif (continuous values)")
    print(f"  - bay_area_fog_80days.tif (binary threshold)")
    print("\nNext step: Combine rainfall + fog into suitability layer")


if __name__ == "__main__":
    main()
