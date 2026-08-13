# Weighted suitability rule (with biological floors)

**Status:** open · **Priority:** medium · **Created:** 2026-05-05 · **Depends on:** ticket 29 (negative control points)

## Why

The current rule is a logical AND of independent thresholds:

```
suitable = (rainfall ≥ 20 in) AND (fog_days ≥ 50) AND (is_land) AND (lat ≥ 35.6)
```

That carves a rectangular **box** in (rainfall, fog) space — both axes must independently clear a fixed bar. But redwoods don't keep separate "rainfall account" and "fog account"; they need enough total warm-season moisture supply, and the two sources substitute (rainfall replenishes soil; fog drip + canopy interception adds dry-season water — Dawson 1998 puts fog drip at up to ~45% of summer water). Inspecting our annotated ground truth (`uv run python scripts/annotate_ground_truth_points.py` after running the suitability pipeline), the box rule misclassifies some real redwood sites:

| Site | rainfall (in) | fog days | box rule |
|---|---|---|---|
| Humboldt Redwoods State Park | **71.5** | 27.7 | FAIL (very wet, low midday fog) |
| Armstrong Redwoods | 47.7 | 29.2 | FAIL (wet, low midday fog) |
| Muir Woods | 36.3 | 62.8 | PASS |
| Stout Grove (Smith River) | 68.6 | 64.3 | PASS |

Humboldt and Armstrong are real redwood habitat. They fail the box on the fog axis despite very high rainfall — they compensate for less satellite-detectable midday fog with more rain (and morning marine layer that satellite at 17–21 UTC partly misses). The ecology says they shouldn't fail; the rule shape is what's failing them.

## Proposed shape (first cut — likely too permissive)

A half-plane in (rainfall, fog) space:

```
suitable = (α·rainfall + β·fog ≥ W) AND (is_land) AND (lat ≥ 35.6)
```

Land and latitude filters stay as separate ANDs — they're hard constraints, not substitutable. The half-plane lets, say, 20 extra inches of rain trade cleanly for some number of fog days.

This is the obvious generalization of the box rule, but it gets the biology only half right. See the next section.

## Refinement: dry-season fog has a non-substitutable floor

Fog isn't just a rainfall stand-in. It has a unique physiological pathway — **foliar uptake** — that rain water can't replace. Per the US Forest Service paper our about page links (Burgess & Dawson, *Foliar uptake of fog in the coast redwood ecosystem*):

> "foliar uptake provides an efficient mechanism to hydrate photosynthetic tissue when water is available aboveground because the water does not need to be absorbed from the soil first and transported from the roots to the plant crown second."

Fog "may contribute little or no water to the soil profile, but may wet leaves for hours at a time" — letting the tree pull water directly through needles and stems on a time scale (hours) and via a route (above-ground) that soil water from winter rain simply cannot match. The paper labels this a "novel drought-alleviation strategy."

Save the Redwoods (citing Dawson, UC Berkeley) puts summer fog at "30 percent or more of the annual water intake" for coast redwoods, and notes the ~33% decline in coastal fog 1951–2008 (plus another 7% 2010–2023) is implicated *specifically* in drought stress on these trees — not winter precipitation, which has no comparable trend.

**Implication**: a pure half-plane is too permissive. A site with massive winter rain but zero summer fog isn't redwood habitat regardless of what α·rain + β·fog says. The rule should enforce a fog floor below which substitution is not allowed:

```
suitable = (dry_season_fog ≥ FOG_FLOOR)              # non-substitutable
       AND (α·fog + β·rain ≥ W)                      # combined moisture, above the floor
       AND (is_land) AND (lat ≥ 35.6)
```

The floor is a hard biological constraint; the half-plane handles substitution *above* it. Practically: even a sopping-wet inland site that never sees summer fog cannot pass.

## Refinement: add dry-season rainfall as a third variable

The current pipeline only tracks wet-season rainfall (Nov–Apr). But coastal CA — especially the north coast (Humboldt, Del Norte) — gets meaningful summer storms in May/Jun and Sep/Oct that fall when the trees most need water. Two sites with the same Nov–Apr total can have very different *summer* water budgets. That difference is exactly the kind of thing we want a moisture-budget model to capture.

Three input variables instead of two:

| variable | source | meaning |
|---|---|---|
| `wet_season_rainfall` | PRISM Nov–Apr (already have) | soil-column recharge ahead of dry season |
| `dry_season_rainfall` | PRISM May–Oct (sum from existing files) | direct dry-season soil top-up |
| `dry_season_fog` | GOES-18 daytime layer (already have) | foliar uptake + canopy drip |

The PRISM monthly normals are already on disk (`data/prism_ppt_us_30s_2020XX_avg_30y/` for all 12 months); computing the dry-season raster is a small extension to `scripts/01_process_study_area_rainfall.py` to also write `outputs/study_area_dry_season_rainfall.tif`.

Rule with three inputs:

```
suitable = (dry_season_fog ≥ FOG_FLOOR)
       AND (wet_season_rainfall ≥ WET_RAIN_FLOOR)            # winter recharge still required
       AND (α·fog + β·dry_rain + γ·wet_rain ≥ W)             # combined moisture above the floors
       AND (is_land) AND (lat ≥ 35.6)
```

Two floors enforce non-substitutable biological needs (the trees can't make it through summer with no fog, and they can't make it through winter→spring with no soil recharge). The linear combination calibrates "enough total moisture" against the negative controls. Floors can be set either as fixed values (preserve the original 20 in / 50 days as a rough biology prior) or as a quantile of the negative controls (e.g. "above the 90th-percentile fog of negatives") — the second option is more data-driven once we have ticket 29 in place.

## What this depends on

**Cannot be fit from positives alone.** Any half-plane that contains all 12 ground truth points has infinitely many candidates; without "no" points, the boundary is unconstrained on the dry-interior side. Ticket 29 (negative control points: Sacramento, Modesto, Lassen vicinity, etc.) is the prerequisite that anchors the separator.

Once negatives are in place, fit in two stages:
1. **Inspect**: scatter the positives + negatives in (rainfall, fog) space. Eyeball whether they're linearly separable and roughly where the boundary should run.
2. **Fit**: logistic regression of label ~ rainfall + fog gives a calibrated linear separator. With ~12 positives and ~4 negatives it'll be similar to a linear-kernel SVM — both methods will give consistent (α, β, W) up to scale.

## Implementation sketch

- Extend `scripts/01_process_study_area_rainfall.py` to also output `outputs/study_area_dry_season_rainfall.tif` (May–Oct sum of the existing PRISM monthly rasters). Same template/grid as the wet-season output.
- Extend `scripts/annotate_ground_truth_points.py` to sample dry-season rainfall too — adds a `dry_rainfall_inches` column. Useful for inspection before any fitting.
- New `scripts/fit_suitability_rule.py`: reads positive + negative CSVs annotated with rainfall (wet + dry) and fog; picks `FOG_FLOOR` and `WET_RAIN_FLOOR` (either fixed or as quantile-of-negatives); fits logistic regression for (α, β, γ, W) on points that clear the floors; prints all five constants.
- `scripts/suitability.py`: replace the two threshold constants with a `(FOG_FLOOR, WET_RAIN_FLOOR, α, β, γ, W)` tuple. Rewrite `combine()` to evaluate the floors-AND-half-plane rule against four input rasters (rain wet, rain dry, fog, land). Latitude filter unchanged.
- `04_combine_suitability.py`: load four layers instead of three. Validation pass: print pass/fail for both positive and negative CSVs.
- `web/about.html`: describe the new rule honestly — "we require both a minimum amount of summer fog (which redwoods absorb directly through their needles) and a minimum amount of winter rain (to recharge the soil); above those floors we score sites by a weighted sum of fog plus rainfall, calibrated against known redwood and non-redwood points." Drop "≥ 20 in" and "≥ 50 days" as standalone facts.

## Potential pitfalls

- **Tiny training set.** 12 positives + ~4 negatives is enough to fit a few parameters, not enough to cross-validate. Don't over-claim accuracy. The fit is a calibration tool, not a generalization claim. With three input variables and floors, parameter count rises (3 weights + 1 intercept + 2 floors = 6); fix floors first (from biology / negative-control quantiles) before fitting weights, so logistic regression only learns 4 numbers.
- **Collinearity.** Wet rainfall, dry rainfall, and fog are all positively correlated along the CA coast (everything peaks west). The fit may be poorly determined; an L2 regularizer with a small weight, or a prior centered on the original (20 in wet, 50 days fog) threshold pair, would stabilize without overriding the data.
- **No clean separator.** If some negatives sit *between* positives in (wet, dry, fog) space — e.g. a foggy-but-too-cold high-elevation interior site — no half-plane will work. In that case accept some misclassification or move to a non-linear boundary (defer to follow-up). Ticket 29's "subtler set" (Cloverdale / Hopland / Lake County, along the inland fog-belt edge) would expose this if it's real.
- **Ecological honesty cap.** A linear combination above floors is still an engineering convenience — fog (foliar uptake), winter rain (soil recharge), and summer rain (direct soil top-up) enter the tree by different physiological pathways with different effective coefficients across the year. The model will be more honest than the box but still cartoon biology. Document the limit in the about page rather than implying mechanism.
- **Stability under input changes.** If we later retune the fog measurement (window, threshold, sample weeks), the fit shifts too. Re-fit and re-deploy as one operation. Worth noting in the script header.
- **Floor choice changes everything.** A fog floor at 20 days vs 30 days is the difference between accepting most inland canyon sites and rejecting them. Ticket 22 work suggests our satellite midday-fog measurement under-counts by maybe 10–20 days at canyon sites; the floor should be set with that uncertainty explicit, not as if the GOES-18 number were ground truth.

## Success criteria

- All 12 ground truth positives pass under the fitted rule (or, if not, the failures are documented and accepted because they reveal a measurement gap).
- All ticket-29 negative controls fail.
- The map under the half-plane rule includes Humboldt + Armstrong + Navarro (the inland-canyon redwood sites the box rule excludes), without bleeding into the Central Valley or onto Lassen.
- `about.html` reads honestly to a non-expert.

## Out of scope

- Nonlinear boundaries beyond floors-plus-half-plane, or input variables beyond {wet rain, dry rain, fog}. If those three plus floors don't work, revisit before adding more.
- Changing the fog or rainfall measurements themselves — those are upstream (ticket 22 and follow-ups).
- Probabilistic output ("80% suitable"). The map stays binary; the rule just decides where the boundary lives.
- Modeling temperature, vapor pressure deficit, or fog-water-equivalent inches directly. Each is a real refinement that would let us replace the linear combo with a true water-budget model — but that's a v2 ticket once the v1 floors-and-weights rule is shipped and we know what it gets wrong.
