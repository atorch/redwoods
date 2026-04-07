# Download PRISM Monthly Precipitation Data

## Objective
Acquire PRISM monthly precipitation normals to support wet season rainfall analysis (20+ inches Nov-Apr threshold from historical heuristic).

## Tasks
- [ ] Identify geographic extent/bounding box for California coastal redwood region
- [x] Download PRISM 30-year monthly precipitation normals (800m resolution)
  - Months needed: All 12 months (focus on Nov-Apr for wet season)
  - Source: https://prism.oregonstate.edu/
  - Data location: https://data.prism.oregonstate.edu/normals/us/800m/ppt/ (note: "ppt" = precipitation)
  - **Downloaded**: 12 monthly files + 1 annual (1991-2020 normals, ~800m/30 arc-second)
- [ ] Inspect data in QGIS to verify coverage and quality
- [ ] Verify data covers area north of San Simeon (~35.6°N) through redwood range
- [x] Document CRS and resolution of downloaded data

## Outputs
- Raw PRISM monthly precipitation rasters (GeoTIFF format)
- Metadata file documenting download parameters, date, version

## Dependencies
- Need to define final geographic extent (see ticket for bounding box definition)

## Notes
- PRISM provides climate normals at ~800m resolution
- Data available as BIL or GeoTIFF
- May need to mosaic multiple tiles depending on extent
