# Create Web Map Interface

## Objective
Build interactive web-based map displaying current redwood distribution (Layer 1) and natural suitable habitat (Layer 2) with layer toggles, legend, and metadata.

## High-Level Tasks
- [ ] Generate web tiles from processed rasters
  - Vector tiles and/or raster tiles at appropriate zoom levels
  - Optimize for web delivery
- [ ] Build web interface using Leaflet.js, Mapbox GL JS, or OpenLayers
  - Basemap (OpenStreetMap or satellite imagery)
  - Layer toggle controls (Layer 1 on/off, Layer 2 on/off)
  - Legend showing what colors/symbols represent
  - Metadata panel with data sources and methodology
- [ ] Optional: Click interaction to show environmental variables at location
- [ ] Deploy/host the map
  - Local server, GitHub Pages, or cloud hosting

## Dependencies
- Layer 1 raster (current redwood distribution) - tickets TBD
- Layer 2 raster (natural suitable habitat) - ticket #09
- All data processing complete

## Notes
- Initial work-in-progress visualization can be done in QGIS
- Web interface is final deliverable for public/interactive access
- Consider mobile responsiveness
- May want basemap with terrain/hillshade for context
