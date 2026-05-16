# Limekiln State Park fails on the 800 m land mask

**Status:** open · **Priority:** low · **Created:** 2026-05-16

## Symptom

Limekiln State Park (36.0116, -121.5160) is a documented ground-truth positive
but the suitability raster marks it 0. From `annotate_ground_truth_points.py`:

| Site | rainfall_inches | fog_days | coldest_tmin_c | hottest_tmax_c | is_suitable |
|---|---|---|---|---|---|
| Limekiln State Park | 28.73 | 69.7 | 8.56 | 18.33 | **0** |

All four rule inputs pass their thresholds (rain ≥ 20, fog ≥ 50, tmin ≥ -3,
tmax ≤ 30). The only remaining factor is the land mask
(`outputs/study_area_land_mask.tif`), which presumably classifies the 800 m
PRISM-grid pixel containing Limekiln as water — Limekiln sits in a steep
coastal canyon right where the canyon mouth meets the Pacific, so an 800 m
pixel centered on (or near) that point is plausibly more ocean than land.

## Root cause hypothesis

The USDA CDL land mask is built at 10 m native resolution and resampled to
the 800 m PRISM grid (see `scripts/17_build_land_mask.py`). For an 800 m
pixel that straddles the coast, the resampler may pick "water" if water is
the majority class — which over-rejects narrow coastal valleys whose redwood
groves sit on a few hectares of land between ocean and ridgeline.

## Verification (one command)

```bash
uv run python -c "
import rasterio
from rasterio.transform import rowcol
with rasterio.open('outputs/study_area_land_mask.tif') as src:
    py, px = rowcol(src.transform, -121.5160, 36.0116)
    arr = src.read(1)
    print(f'Limekiln pixel ({py},{px}): land_mask = {arr[py, px]}')
    # neighborhood
    print(arr[py-2:py+3, px-2:px+3])
"
```

## Possible fixes (out of scope here — design decision needed)

- **Majority → any-land rule:** treat an 800 m pixel as land if *any* 10 m
  sub-pixel is land. Recovers narrow coastal canyons; risks adding noisy
  near-shore ocean pixels back to the green layer.
- **Buffer the coastline inland by one pixel:** dilate the land mask by 1
  cell before applying. Cheaper, similar effect.
- **Move to a finer base grid:** the real fix at scale, but a much bigger
  pipeline change (PRISM is the limiting resolution).
- **Accept the miss:** Limekiln is one of 12 positives; the other 11 all
  pass; the southern Big Sur coast is genuinely the edge of the range. We
  could just document it as a known false-negative.

## Out of scope

- Re-tuning fog/temperature thresholds. All four climate inputs pass here;
  this is purely a land-mask resolution artifact.
- Adding more Big Sur ground-truth points to disambiguate.
