# Compute Wet Season Rainfall Totals

## Objective
Sum November-April precipitation to create wet season total rainfall raster, then generate 20+ inch threshold layer.

## Tasks
- [ ] Load PRISM monthly precipitation rasters (Nov, Dec, Jan, Feb, Mar, Apr)
- [ ] Ensure all rasters aligned (same CRS, extent, resolution)
- [ ] Sum the 6 monthly rasters to create wet season total
- [ ] Create binary threshold layer: 1 where total >= 20 inches, 0 otherwise
- [ ] Validate results against known redwood areas

## Outputs
- `wet_season_total_precip.tif` - continuous rainfall values (inches)
- `wet_season_20in_threshold.tif` - binary layer (1 = meets threshold, 0 = does not)
- Visualization/QA map showing threshold boundary

## Dependencies
- Ticket #01: Download PRISM precipitation data

## Notes
- 20 inch threshold from historical heuristic
- Should validate that known redwood groves exceed this threshold
- Consider creating additional thresholds (15", 25") for sensitivity analysis
