"""
Redwood habitat heuristic — single source of truth for the rule.

The rule:

    suitable = has_enough_rain  AND  has_enough_fog  AND  is_land

Inputs are binary uint8 rasters on the same grid: 1 = yes, 0 = no, 255 = nodata.
Thresholds come from the academic heuristic ("north of San Simeon, >= 20 in of
wet-season rain, >= 80 fog-days in the dry season"); the land mask drops ocean
and inland water that would otherwise slip through.

Any script that encodes the combined suitability rule should go through
`combine(...)` here rather than re-expressing the AND inline.
"""

import numpy as np

# Wet-season (Nov–Apr) precipitation total, from PRISM 30-year normals.
RAINFALL_THRESHOLD_INCHES = 20.0

# Dry-season nights with fog, from GOES-16 BTD (Ch13 – Ch7).
FOG_DAYS_THRESHOLD = 80

NODATA = np.uint8(255)


def combine(has_rain: np.ndarray, has_fog: np.ndarray, is_land: np.ndarray) -> np.ndarray:
    """Apply the rule, propagating NoData from any input.

    Returns uint8 where 1 = suitable, 0 = not suitable, 255 = nodata.
    """
    if not (has_rain.shape == has_fog.shape == is_land.shape):
        raise ValueError(
            f"shape mismatch: rain={has_rain.shape}, fog={has_fog.shape}, land={is_land.shape}"
        )

    suitable = ((has_rain == 1) & (has_fog == 1) & (is_land == 1)).astype(np.uint8)
    nodata = (has_rain == NODATA) | (has_fog == NODATA) | (is_land == NODATA)
    suitable[nodata] = NODATA
    return suitable
