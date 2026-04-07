# Acquire NAIP Imagery for Current Redwood Detection

## Objective
Download NAIP (National Agriculture Imagery Program) imagery for visual and spectral classification of current redwood stands.

## Tasks
- [ ] Identify NAIP imagery coverage for study area
  - Most recent year available (2020, 2022, etc.)
  - 1m resolution, 4-band (RGB + NIR)
- [ ] Download tiles covering redwood range
  - Source: USDA NAIP via USGS Earth Explorer or similar
  - Format: GeoTIFF or MrSID
- [ ] Mosaic tiles if necessary
- [ ] Verify bands: Red, Green, Blue, Near-Infrared
- [ ] Calculate and validate NDVI for sample areas

## Outputs
- NAIP imagery mosaic for study area
- Metadata: acquisition year, resolution, band configuration
- Sample NDVI calculation demonstrating data quality

## Dependencies
- Ticket #05: Define geographic extent

## Notes
- NAIP imagery is key for distinguishing redwoods from other conifers
- 1m resolution allows identification of individual trees/groves
- NIR band enables vegetation indices (NDVI, etc.)
- May be large data volume - consider processing in tiles
- Used for Layer 1 (current redwood distribution)
