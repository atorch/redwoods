# Acquire Park Boundaries with Known Redwoods

## Objective
Obtain vector data for state/national parks and protected areas containing known redwood groves.

## Tasks
- [ ] Download California State Parks boundaries
  - Source: CA State Parks GIS data or Cal Fire
- [ ] Download National Park Service boundaries
  - Source: NPS Data Store
  - Focus on: Redwood National Park, Muir Woods, Big Basin, etc.
- [ ] Filter for parks known to contain coast redwoods
- [ ] Merge into single vector layer
- [ ] Add attributes: park name, redwood presence (confirmed), area

## Outputs
- `known_redwood_parks.geojson` or `.gpkg` - vector boundaries
- List/table of included parks with metadata

## Dependencies
- Ticket #05: Define geographic extent (to know which parks to include)

## Notes
- This serves as "ground truth" for validation
- Can be used as positive training samples for classification
- May also identify protected areas for future restoration analysis
- Consider including conservation easements if available
