# Temperature constraints (PRISM tmin / tmax / tmean)

**Status:** open · **Priority:** medium · **Created:** 2026-05-05

## Why

Coast redwoods are a mild-climate species — the maritime fog belt is mild because the Pacific and the marine layer buffer both extremes. Per the USDA *Silvics of North America* entry for *Sequoia sempervirens*:

> "Mean annual temperatures vary between 10° and 16° C (50° and 60° F). Temperatures rarely drop below -9° C (15° F) or rise above 38° C (100° F). The frost-free period varies from 6 to 11 months."

Two things this implies for our model:

- **Cold extremes**: redwoods don't survive prolonged winter freezes. Sites with a January mean tmin below ~-3 to -5 °C see freeze events well below -9 °C regularly. This catches Mt Shasta and the Cascade / high Klamath / Sierra interior — which the elevation mask in ticket 31 also catches, but temperature is a direct biological filter rather than a topographic proxy.
- **Heat extremes**: redwoods can't transpire through Central Valley summers. Sacramento's mean July tmax is ~33–34 °C, well above coastal sites at 17–22 °C, and *every* Central Valley negative in the POC fit (Davis, Stockton, Antioch, Modesto) shares this signature. A "summer mean tmax ≤ 27–30 °C" filter directly rejects those four points without relying on the more variable fog signal or the not-yet-built dry-season rainfall layer.

Adding temperature is conceptually the same shape as the land mask (ticket 17) and elevation mask (ticket 31): one or two binary masks on the study grid, AND-ed into `suitability.combine()`.

## What we have / what to download

- **Already on disk** under `data/prism_tmean_us_30s_2020XX_avg_30y/` (and `.zip`): PRISM monthly mean-temperature 30-year normals, all 12 months.
- **Need to download**, from the same PRISM normals source we used for precipitation:
  - tmin monthly normals (mean of daily lows, all 12 months)
  - tmax monthly normals (mean of daily highs, all 12 months)
- File naming convention will mirror precip: `data/prism_tmin_us_30s_2020XX_avg_30y/` etc.

## Proposed variables and thresholds

Three aggregated variables to consider, in order of how directly they map to the biology:

| variable | source | suggested threshold | rationale |
|---|---|---|---|
| `coldest_month_tmin` | min over 12 monthly tmin rasters | `≥ -3 °C` | Mean Jan/Dec tmin below this implies repeated dips well past Silvics' "rarely below -9 °C" tolerance. |
| `hottest_month_tmax` | max over 12 monthly tmax rasters | `≤ 30 °C` | Mean Jul/Aug tmax above this implies daily highs regularly hitting the Silvics 38 °C ceiling. Native coastal sites cluster 17–22 °C. |
| `annual_mean_temp` | mean over 12 tmean rasters | `8 °C ≤ x ≤ 18 °C` | Silvics range is 10–16 °C; ±2 °C buffer for coastal microclimate. Likely redundant with the two extremes above; include only if needed. |

Likely `coldest_month_tmin` and `hottest_month_tmax` together are sufficient — they bracket the maritime envelope cleanly.

## What to build

1. **New script** `scripts/build_temperature_masks.py`, modeled on `17_build_land_mask.py`:
   - Read all 12 monthly tmin rasters, take per-pixel min → `outputs/study_area_coldest_month_tmin.tif` (continuous, °C).
   - Read all 12 monthly tmax rasters, take per-pixel max → `outputs/study_area_hottest_month_tmax.tif` (continuous).
   - Apply thresholds → two binary masks: `outputs/study_area_temperature_mask.tif` (uint8, 1 = pass both, 0 = fail either). Could also write the two binary intermediates if useful for diagnosis.
2. **Wire into the rule.** Extend `scripts/suitability.py`'s `combine()` to take the temperature mask. Update `04_combine_suitability.py` to load and pass it. Same plumbing as land + elevation masks.
3. **Update `scripts/annotate_ground_truth_points.py`** and `scripts/fit_suitability_rule.py` to also sample the two continuous temperature rasters — useful to inspect whether the threshold choices are right before wiring into the rule.
4. **Update `web/about.html`** with one sentence: "places that get colder than ~-3 °C in winter or hotter than ~30 °C in summer are excluded — coast redwoods are a maritime species and don't tolerate either extreme." Cite the Silvics range.

## Sanity check before deploying

Once the continuous tmin/tmax rasters exist, sample them at every positive ground truth point — those values bound the *empirical* envelope our positives actually occupy. Compare against the Silvics literature numbers; if all 12 positives sit comfortably inside the proposed thresholds, deploy as-is. If any positive sits near or beyond a threshold (e.g. an inland Mendocino or Big Sur site that gets warm summers), loosen that threshold rather than dropping the point.

## Relationship to other tickets

- **Ticket 31 (elevation mask)**: partly redundant. Elevation catches Mt Shasta via topography; temperature catches it via cold extreme. Keep both — they're cheap, biology-grounded, and address different failure modes (elevation also fixes PRISM's snow-as-rainfall artifact, which temperature doesn't).
- **Ticket 30 (weighted suitability rule)**: temperature could enter as a fourth/fifth axis in the linear combination, but the more conservative path is hard masks first (cold AND hot AND land AND elevation), with the half-plane reserved for fog + rainfall. Heat and cold are non-substitutable: massive moisture doesn't rescue a freezing or scorching site.

## Out of scope

- **Daily extreme statistics** (e.g. days below 0 °C per year, growing degree days). PRISM monthly normals don't carry that directly; would need daily PRISM or a derivative product. Defer until monthly aggregates are shown insufficient.
- **Microclimate within bbox** (cold-air drainage, marine inversions). 800 m PRISM grid won't resolve canyon-scale temperature variation.
- **Climate-change projections.** This ticket is about current native-range envelope, not future suitability under warming.
