# Mask Water From Suitability Raster

> **Status:** TODO — capturing intent.

## Problem

The suitability raster currently marks ocean and inland water (SF Bay, large lakes)
as "suitable habitat" wherever those pixels happen to satisfy the rainfall + fog
criteria. Visually, the green layer leaks into the Pacific and bays, which is
obviously wrong and undermines the map's credibility.

We want the rule to become:
`suitable = sufficient_fog AND sufficient_rainfall AND NOT water`.

## Options

### A. USDA CDL (Cropland Data Layer) — raster mask
- <https://www.nass.usda.gov/Research_and_Science/Cropland/Release/index.php>
- Has a "Water" class (value 111) plus a few wetland classes; 30m national raster.
- **Pro:** raster-native, trivial to combine with our existing GeoTIFFs
  (reproject to our 800m grid, treat water class as a binary mask).
- **Con:** multi-GB national download when we only need a clip around NorCal;
  CDL is really designed for agriculture and is overkill for "is this ocean?"
- **Con:** CDL doesn't extend offshore — ocean pixels are NoData. Workable
  though: the rule becomes `NOT (CDL water OR CDL wetland OR CDL NoData)`,
  i.e. treat "outside the CDL footprint" as not-land. Risk: any legitimate
  NoData inside the land footprint (sensor gaps, masked pixels) also gets
  dropped, which may or may not matter in practice.

### B. Census TIGER/Line — vector water
- TIGER water shapefiles (area hydrography + coastline).
- **Pro:** authoritative, free, covers ocean coastline and inland water.
- **Con:** multiple layers to stitch (areawater per county + coastline),
  vector → rasterize step adds pipeline complexity.

### C. Natural Earth land polygons — vector, coarse
- <https://www.naturalearthdata.com/downloads/10m-physical-vectors/>
  (ne_10m_land, ne_10m_ocean, ne_10m_lakes).
- **Pro:** tiny download, public domain, one clean polygon set, handles
  ocean and major lakes in one shot.
- **Con:** 10m scale (~250m on the ground at best); fine for "is this the
  Pacific?" but misses small ponds and narrow river channels. At our 800m
  raster resolution this almost certainly doesn't matter.

### D. OpenStreetMap coastline / water
- `natural=coastline`, `natural=water` via Geofabrik extract or Overpass.
- **Pro:** very high resolution, current.
- **Con:** heavier download + processing; overkill for an 800m raster.

## Recommendation

Start with **Option C (Natural Earth)**. At 800m output resolution the coarse
polygons are more than accurate enough, the download is a single small zip,
and the pipeline step is one `rasterize → multiply` against our existing
`study_area_redwood_suitable.tif`.

If/when we move to finer resolutions (e.g. 30m or 100m) we can swap in TIGER
or OSM water without changing the overall structure — same "rasterize a land
mask, multiply through" shape.

## Sketch

```
scripts/14_build_land_mask.py
  - download ne_10m_land.zip (cache in data/)
  - clip to study bbox
  - rasterize to the exact grid/CRS of study_area_redwood_suitable.tif
  - save data/land_mask.tif (1 = land, 0 = water)

scripts/15_apply_land_mask.py  (or fold into the existing combine step)
  - suitable = suitable * land_mask
  - overwrite outputs/study_area_redwood_suitable.tif
  - regenerate tiles (scripts/13_generate_web_tiles.py)
```

## Out of scope

- Distinguishing freshwater from saltwater.
- Masking rivers / streams that are narrower than our 800m pixel.
- Anything fancier than a binary land/water gate.
