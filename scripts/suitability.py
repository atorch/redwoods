"""
Redwood habitat heuristic — single source of truth for the rule.

The rule:

    suitable = has_enough_rain
               AND has_enough_fog
               AND is_land
               AND is_temperate
               AND is_frost_hardy

Inputs are binary uint8 rasters on the same grid: 1 = yes, 0 = no, 255 = nodata.
Rain and fog thresholds start from the academic heuristic (~20 in of wet-season
rain, ~80 dry-season fog days, north of San Simeon) and are then tuned against
ground truth; the temperature and land masks replace the latitude filter,
dropping the cold interior, the hot Central Valley, and open water / wetland.
The frost-hardiness mask (ticket 36) catches high-elevation / far-northern-
interior sites that pass the *mean* coldest-month tmin floor but experience
real winter extreme-cold events the monthly-normal mean smooths away.

Any script that encodes the combined suitability rule should go through
`combine(...)` here rather than re-expressing the AND inline.
"""

import numpy as np

# Wet-season (Nov–Apr) precipitation total, from PRISM 30-year normals.
RAINFALL_THRESHOLD_INCHES = 20.0

# Dry-season nights with low-cloud / marine-layer overhead, from GOES-16
# Ch13−Ch7 BTD at 06–12 UTC (11 PM – 5 AM PST), 4-week × 5-year climatology
# (2020–2024). Nighttime BTD separates the ground truth set much better than
# the GOES-18 daytime albedo signal does — daytime under-detects inland canyon
# redwood sites (Armstrong / Humboldt / Navarro) and false-positives Mt Shasta
# on orographic high cloud + snow albedo. Fog alone doesn't cleanly separate
# the classes at any threshold — Davis CA sits at ≈79 nights, above the
# positives' floor (Limekiln ≈70). The 50-night threshold rejects the
# never-foggy Central Valley sites while admitting every coastal positive;
# the remaining overlap (Davis, Mt Shasta) is rejected by the rainfall and
# temperature filters, not by fog. See the per-site separation table from
# `scripts/annotate_ground_truth_points.py`.
FOG_DAYS_THRESHOLD = 50

# Temperature envelope, from PRISM monthly tmin/tmax 30-year normals (ticket 32).
# Coldest-month mean tmin floor: below this, mean January lows imply repeated
# freeze events past the Silvics "rarely below -9 °C" tolerance.
# Hottest-month mean tmax ceiling: above this, mean July highs imply daily
# Central-Valley summers above the Silvics 38 °C tolerance.
COLDEST_MONTH_TMIN_FLOOR_C = -3.0
HOTTEST_MONTH_TMAX_CEILING_C = 30.0

# USDA Plant Hardiness Zone Map 2023 (PRISM Climate Group), average annual
# extreme minimum temperature, 1991-2020 (ticket 36). Unlike the coldest-month
# *mean* tmin above, this is the mean of each year's single coldest daily low —
# it captures the left tail (hard-freeze years), not just a smoothed monthly
# average.
#
# -7 C (the original ticket-36 estimate, "roughly the 9a-10b hardiness-zone
# edge") was too loose once the study area was extended into Oregon: it
# passed Kloster Mountain, OR (-6.5 C) — ~120 mi north of the documented
# native range edge (42 09'N, Chetco River, per the USDA Silvics Manual) and
# added as a negative control specifically to probe this. -5.0 C is
# tightened to reject it, chosen from the gap between the coldest confirmed
# positive (Humboldt Redwoods, -3.83 C) and the coldest rejected negative
# short of that (Kloster, -6.5 C) — every one of our 20 evaluable ground-
# truth/negative-control points (scripts/annotate_ground_truth_points.py)
# classifies correctly anywhere in (-6.5, -3.83]; -5.0 sits roughly in the
# middle of that gap. Revisit as more ground truth accumulates near the
# range edge — see ticket 36's "Progress" section and ticket 37.
PHZM_EXTREME_MIN_FLOOR_C = -5.0

NODATA = np.uint8(255)


def combine(
    has_rain: np.ndarray,
    has_fog: np.ndarray,
    is_land: np.ndarray,
    is_temperate: np.ndarray,
    is_frost_hardy: np.ndarray,
) -> np.ndarray:
    """Apply the rule, propagating NoData from any input.

    Returns uint8 where 1 = suitable, 0 = not suitable, 255 = nodata.
    """
    shapes = {
        "rain": has_rain.shape,
        "fog": has_fog.shape,
        "land": is_land.shape,
        "temperate": is_temperate.shape,
        "frost_hardy": is_frost_hardy.shape,
    }
    if len(set(shapes.values())) != 1:
        raise ValueError(f"shape mismatch: {shapes}")

    suitable = (
        (has_rain == 1)
        & (has_fog == 1)
        & (is_land == 1)
        & (is_temperate == 1)
        & (is_frost_hardy == 1)
    ).astype(np.uint8)
    nodata = (
        (has_rain == NODATA)
        | (has_fog == NODATA)
        | (is_land == NODATA)
        | (is_temperate == NODATA)
        | (is_frost_hardy == NODATA)
    )
    suitable[nodata] = NODATA
    return suitable
