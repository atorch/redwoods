# Set Up Python Environment

## Objective
Create reproducible Python development environment using `uv` with all required geospatial libraries.

## Tasks
- [ ] Install `uv` if not already present
- [ ] Initialize Python project with `uv`
- [ ] Add core dependencies:
  - `rasterio` - raster I/O and processing
  - `geopandas` - vector data
  - `shapely` - geometric operations
  - `numpy` / `scipy` - numerical operations
  - `xarray` - multidimensional arrays (useful for time-series raster data)
  - `matplotlib` / `cartopy` - visualization
  - `pyproj` - coordinate transformations
- [ ] Add optional dependencies:
  - `scikit-learn` - habitat modeling
  - `rioxarray` - rasterio + xarray integration
  - `netCDF4` - for GOES-16 data (likely in netCDF format)
- [ ] Create `pyproject.toml` with pinned versions
- [ ] Test environment with simple raster read/write

## Outputs
- `pyproject.toml` with all dependencies
- `uv.lock` lockfile for reproducibility
- `requirements.txt` (if needed for compatibility)
- Quick start guide in README or docs/

## Dependencies
- None - foundational setup

## Notes
- `uv` is fast and handles dependency resolution well
- Consider adding pre-commit hooks for code quality
- May need GDAL binaries installed at system level
