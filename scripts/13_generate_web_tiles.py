#!/usr/bin/env python3
"""
Generate web tiles from redwood suitability raster.

This script:
1. Converts suitability raster to Cloud Optimized GeoTIFF (COG)
2. Pre-generates XYZ tiles for zoom levels 8-14 (study area)
3. Saves tiles in standard XYZ directory structure for web serving

Tiles are 256x256 PNG images with transparency for non-suitable areas
and green fill for suitable redwood habitat.

Input suitability layer uses GOES-18 daytime fog detection (10 AM – 2 PM PDT,
albedo > 0.25) — ticket 22 / scripts 18 + 19.
"""

import os
import sys
from pathlib import Path
import numpy as np
import rasterio
from rasterio.io import MemoryFile
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.enums import ColorInterp
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles
from rio_tiler.io import Reader
from rio_tiler.models import ImageData
from PIL import Image
import mercantile
import json


# Configuration
INPUT_FILE = Path("outputs/study_area_redwood_suitable.tif")
COG_FILE = Path("outputs/study_area_redwood_suitable_cog.tif")
# Tiles live under web/ so the whole web directory is a self-contained
# deployable unit (Cloudflare Pages uploads web/ as-is).
TILES_DIR = Path("web/tiles/redwood_suitability")
BBOX_FILE = Path("outputs/study_area_bbox.json")

# Zoom levels. We only generate z=8 today — that's the bootstrap tile set
# shipped to Cloudflare Pages (see web/index.html: maxNativeZoom=8 scales
# these for higher user zooms). Higher zooms would blow past Pages' 20k-file
# cap; bump MAX_ZOOM once tiles move to R2 (tickets/24).
MIN_ZOOM = 8
MAX_ZOOM = 8

# Tile size (standard)
TILE_SIZE = 256

# Color scheme for suitability (green for suitable habitat)
SUITABLE_COLOR = (34, 139, 34, 204)  # Green with 80% opacity (RGB: #228B22)
NOT_SUITABLE_COLOR = (0, 0, 0, 0)     # Transparent
NODATA_COLOR = (0, 0, 0, 0)           # Transparent


def convert_to_cog():
    """Convert suitability raster to Cloud Optimized GeoTIFF."""
    print("="*70)
    print("Converting to Cloud Optimized GeoTIFF")
    print("="*70)
    print()

    if COG_FILE.exists():
        print(f"COG already exists: {COG_FILE}")
        print("Skipping conversion...")
        return

    print(f"Input: {INPUT_FILE}")
    print(f"Output: {COG_FILE}")
    print()

    # First, reproject to Web Mercator (EPSG:3857) for efficient tiling
    print("Reprojecting to Web Mercator (EPSG:3857)...")

    with rasterio.open(INPUT_FILE) as src:
        # Calculate transform for Web Mercator
        transform, width, height = calculate_default_transform(
            src.crs,
            'EPSG:3857',
            src.width,
            src.height,
            *src.bounds
        )

        # Update metadata
        kwargs = src.meta.copy()
        kwargs.update({
            'crs': 'EPSG:3857',
            'transform': transform,
            'width': width,
            'height': height
        })

        # Create temporary in-memory file for reprojected data
        with MemoryFile() as memfile:
            with memfile.open(**kwargs) as dst:
                # Reproject
                reproject(
                    source=rasterio.band(src, 1),
                    destination=rasterio.band(dst, 1),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs='EPSG:3857',
                    resampling=Resampling.nearest  # Nearest for categorical data
                )

                # Set band description
                dst.set_band_description(1, "Redwood suitable habitat (daytime fog 10 AM – 2 PM PDT, GOES-18)")

            # Now convert to COG
            print("Creating Cloud Optimized GeoTIFF...")
            cog_translate(
                memfile,
                COG_FILE,
                cog_profiles.get("lzw"),  # LZW compression
                in_memory=True
            )

    print(f"✓ COG created: {COG_FILE}")
    print()


def get_tile_bounds(zoom_level):
    """Calculate tile bounds for study area at given zoom level."""
    # Load bounding box from file
    with open(BBOX_FILE, 'r') as f:
        bbox = json.load(f)

    west = bbox['min_lon']
    south = bbox['min_lat']
    east = bbox['max_lon']
    north = bbox['max_lat']

    # Get tiles covering the bounding box
    tiles = list(mercantile.tiles(west, south, east, north, zoom_level))

    return tiles


def raster_to_rgba(data, nodata_value=255):
    """Convert suitability raster to RGBA image."""
    # Create RGBA array
    rgba = np.zeros((data.shape[0], data.shape[1], 4), dtype=np.uint8)

    # Suitable pixels (value = 1) → green
    suitable_mask = (data == 1)
    rgba[suitable_mask] = SUITABLE_COLOR

    # Not suitable pixels (value = 0) → transparent
    not_suitable_mask = (data == 0)
    rgba[not_suitable_mask] = NOT_SUITABLE_COLOR

    # NoData pixels → transparent
    nodata_mask = (data == nodata_value)
    rgba[nodata_mask] = NODATA_COLOR

    return rgba


def generate_tile(reader, tile, zoom):
    """Generate a single tile from the COG."""
    try:
        # Get tile bounds
        bounds = mercantile.bounds(tile)

        # Read data from COG for this tile
        img = reader.tile(tile.x, tile.y, tile.z, tilesize=TILE_SIZE)

        # Get the data array (single band)
        data = img.data[0]  # First band

        # Convert to RGBA
        rgba = raster_to_rgba(data, nodata_value=255)

        # Create PIL Image
        image = Image.fromarray(rgba, mode='RGBA')

        return image

    except Exception as e:
        # Return transparent tile if no data
        return Image.new('RGBA', (TILE_SIZE, TILE_SIZE), (0, 0, 0, 0))


def generate_tiles():
    """Generate all tiles for zoom levels."""
    print("="*70)
    print("Generating Web Tiles")
    print("="*70)
    print()

    print(f"Zoom levels: {MIN_ZOOM} to {MAX_ZOOM}")
    print(f"Tile size: {TILE_SIZE}x{TILE_SIZE}")
    print(f"Output directory: {TILES_DIR}")
    print()

    # Create output directory
    TILES_DIR.mkdir(parents=True, exist_ok=True)

    # Open COG with rio-tiler
    with Reader(str(COG_FILE)) as reader:
        total_tiles = 0

        for zoom in range(MIN_ZOOM, MAX_ZOOM + 1):
            print(f"\nZoom level {zoom}:")

            # Get tiles for this zoom level
            tiles = get_tile_bounds(zoom)
            print(f"  Tiles to generate: {len(tiles)}")

            # Create zoom directory
            zoom_dir = TILES_DIR / str(zoom)
            zoom_dir.mkdir(exist_ok=True)

            tiles_generated = 0

            for tile in tiles:
                # Create x directory
                x_dir = zoom_dir / str(tile.x)
                x_dir.mkdir(exist_ok=True)

                # Tile filename
                tile_file = x_dir / f"{tile.y}.png"

                # Skip if already exists
                if tile_file.exists():
                    continue

                # Generate tile
                image = generate_tile(reader, tile, zoom)

                # Save tile
                image.save(tile_file, 'PNG', optimize=True)
                tiles_generated += 1

            print(f"  Generated: {tiles_generated} new tiles")
            total_tiles += tiles_generated

        print()
        print(f"✓ Total tiles generated: {total_tiles}")


def calculate_tile_stats():
    """Calculate total tile count and disk usage."""
    print()
    print("="*70)
    print("Tile Statistics")
    print("="*70)
    print()

    total_tiles = 0
    total_size = 0

    for zoom in range(MIN_ZOOM, MAX_ZOOM + 1):
        zoom_dir = TILES_DIR / str(zoom)
        if not zoom_dir.exists():
            continue

        zoom_tiles = sum(1 for _ in zoom_dir.glob('**/*.png'))
        zoom_size = sum(f.stat().st_size for f in zoom_dir.glob('**/*.png'))

        total_tiles += zoom_tiles
        total_size += zoom_size

        print(f"Zoom {zoom:2d}: {zoom_tiles:5d} tiles ({zoom_size / 1024 / 1024:5.1f} MB)")

    print()
    print(f"Total: {total_tiles} tiles ({total_size / 1024 / 1024:.1f} MB)")
    print()


def main():
    print()
    print("="*70)
    print("REDWOOD SUITABILITY WEB TILES")
    print("="*70)
    print()
    print("Generating browser-ready map tiles for the redwood habitat")
    print("suitability layer (study-area extent).")
    print()
    print("Input uses GOES-18 daytime fog detection")
    print("  (Ch2 albedo > 0.30 at 19-21 UTC = 12-15 PDT)")
    print()

    # Step 1: Convert to COG
    convert_to_cog()

    # Step 2: Generate tiles
    generate_tiles()

    # Step 3: Calculate statistics
    calculate_tile_stats()

    print("="*70)
    print("✓ Web tiles generation complete!")
    print("="*70)
    print()
    print("VIEWING INSTRUCTIONS:")
    print("="*70)
    print()
    print("1. Start HTTP server from the web/ directory:")
    print("   cd /home/adrian/redwoods/web")
    print("   python3 -m http.server 8000")
    print()
    print("2. Open in browser:")
    print("   http://localhost:8000/")
    print()
    print("3. What you'll see:")
    print("   - Green overlay: Suitable habitat")
    print("   - Red markers: 4 validated ground truth points")
    print("   - Layer control: Toggle visibility in top-left")
    print()
    print("TROUBLESHOOTING:")
    print("   - No tiles? → Run this script again to regenerate")
    print("   - Tiles now live at web/tiles/redwood_suitability/")
    print()
    print(f"Tiles location: {TILES_DIR.absolute()}")
    print(f"Tile count: {calculate_total_tiles()} tiles")
    print()


def calculate_total_tiles():
    """Helper to count total tiles."""
    total = 0
    for zoom in range(MIN_ZOOM, MAX_ZOOM + 1):
        zoom_dir = TILES_DIR / str(zoom)
        if zoom_dir.exists():
            total += sum(1 for _ in zoom_dir.glob('**/*.png'))
    return total


if __name__ == "__main__":
    main()
