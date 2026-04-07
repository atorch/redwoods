# Define Geographic Extent and Resolution

## Objective
Establish the precise bounding box, CRS, and target resolution for all project data layers.

## Questions to Answer
- [ ] Geographic extent:
  - North boundary: Oregon border? Del Norte County?
  - South boundary: San Simeon (35.6°N)? Big Sur? Further south?
  - East boundary: How far inland? Based on known redwood range?
  - West boundary: Pacific coast
- [ ] Coordinate Reference System:
  - UTM Zone 10N (common for California)?
  - Or state plane coordinate system?
  - WGS84 lat/lon for initial data collection?
- [ ] Target resolution for final habitat model:
  - 30m (Landsat/DEM native)?
  - 100m (computational efficiency)?
  - 10m (high detail but large data)?

## Outputs
- `config/extent.json` or similar with:
  - Bounding box coordinates
  - CRS/EPSG code
  - Target resolution
  - Rationale/documentation

## Dependencies
- None - this is a foundational decision

## Notes
- Affects data download sizes and processing time
- Should align with PRISM (~800m) for climate data but allow finer resolution for imagery
- Consider starting with smaller pilot area (e.g., Marin + SF counties) then expanding
