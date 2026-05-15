"""
Redwood habitat heuristic — single source of truth for the rule.

The rule:

    suitable = has_enough_rain
               AND has_enough_fog
               AND is_land
               AND is_temperate

Inputs are binary uint8 rasters on the same grid: 1 = yes, 0 = no, 255 = nodata.
Thresholds come from the academic heuristic ("north of San Simeon, >= 20 in of
wet-season rain, >= 80 fog-days in the dry season"); the land mask drops ocean
and inland water that would otherwise slip through; the temperature mask drops
sites outside the maritime envelope (cold interior + hot Central Valley).

Any script that encodes the combined suitability rule should go through
`combine(...)` here rather than re-expressing the AND inline.
"""

import numpy as np

# Wet-season (Nov–Apr) precipitation total, from PRISM 30-year normals.
RAINFALL_THRESHOLD_INCHES = 20.0

# Dry-season days with marine-layer cloud overhead at any point in 15–21 UTC
# (8 AM – 2 PM PDT), from GOES-18 Ch2 albedo > 0.25. Broader than the original
# "fog past noon" station heuristic — satellite midday-only severely under-
# detects inland canyon redwood sites that depend on morning fog. Threshold
# tuned against ground truth points.
FOG_DAYS_THRESHOLD = 50

# Temperature envelope, from PRISM monthly tmin/tmax 30-year normals (ticket 32).
# Coldest-month mean tmin floor: below this, mean January lows imply repeated
# freeze events past the Silvics "rarely below -9 °C" tolerance.
# Hottest-month mean tmax ceiling: above this, mean July highs imply daily
# Central-Valley summers above the Silvics 38 °C tolerance.
COLDEST_MONTH_TMIN_FLOOR_C = -3.0
HOTTEST_MONTH_TMAX_CEILING_C = 30.0

NODATA = np.uint8(255)


def combine(
    has_rain: np.ndarray,
    has_fog: np.ndarray,
    is_land: np.ndarray,
    is_temperate: np.ndarray,
) -> np.ndarray:
    """Apply the rule, propagating NoData from any input.

    Returns uint8 where 1 = suitable, 0 = not suitable, 255 = nodata.
    """
    shapes = {
        "rain": has_rain.shape,
        "fog": has_fog.shape,
        "land": is_land.shape,
        "temperate": is_temperate.shape,
    }
    if len(set(shapes.values())) != 1:
        raise ValueError(f"shape mismatch: {shapes}")

    suitable = (
        (has_rain == 1)
        & (has_fog == 1)
        & (is_land == 1)
        & (is_temperate == 1)
    ).astype(np.uint8)
    nodata = (
        (has_rain == NODATA)
        | (has_fog == NODATA)
        | (is_land == NODATA)
        | (is_temperate == NODATA)
    )
    suitable[nodata] = NODATA
    return suitable
