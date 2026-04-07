# Combine Historical Heuristic Layers

## Objective
Integrate the three criteria from the 1750 historical heuristic into a single suitability layer.

## Tasks
- [ ] Load three threshold layers:
  - Geographic: north of San Simeon (latitude > 35.6°N)
  - Wet season rainfall: >= 20 inches Nov-Apr
  - Fog persistence: >= 80 days/dry season with afternoon fog
- [ ] Ensure all layers have identical extent, CRS, and resolution
- [ ] Create combined binary layer: 1 where ALL three criteria met
- [ ] Compute area statistics (square miles/acres meeting all criteria)
- [ ] Overlay with current known redwood locations for validation
- [ ] Generate visualization/map of predicted 1750 range

## Outputs
- `historical_range_1750_heuristic.tif` - binary suitability layer
- Summary statistics report
- Validation analysis comparing to known redwood parks
- Map visualization (static image or interactive)

## Dependencies
- Ticket #02: Wet season rainfall layer
- Ticket #04: Fog persistence layer
- Ticket #08: Park boundaries (for validation)

## Notes
- This provides a simple, interpretable model based on expert knowledge
- Can compare against more complex ML-based habitat models later
- Validation against current redwood locations will show how well heuristic performs
