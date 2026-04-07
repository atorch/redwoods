# Acquire Digital Elevation Model Data

## Objective
Download USGS 3DEP DEM data for topographic analysis (elevation, slope, aspect, wetness index).

## Tasks
- [ ] Identify appropriate 3DEP product:
  - 10m resolution (high detail) vs 30m (standard)
  - 1/3 arc-second vs 1 arc-second
- [ ] Download DEM tiles covering study area
  - Source: USGS National Map or 3DEP portal
  - Format: GeoTIFF preferred
- [ ] Mosaic tiles if necessary
- [ ] Verify vertical datum (NAVD88 or similar)

## Outputs
- `dem.tif` - mosaicked elevation raster
- Metadata documenting source, resolution, datum

## Dependencies
- Ticket #05: Define geographic extent

## Notes
- 10m resolution available for much of California via 3DEP
- Will be used to derive slope, aspect, topographic wetness index
- Elevation interacts with fog persistence (coastal fog vs inland)
