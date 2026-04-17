# Summary: BTD Threshold Change from 0.0 K to 2.0 K

## What Changed

**File:** `scripts/11_create_real_fog_layer.py` line 52
**Change:** `FOG_BTD_THRESHOLD = 0.0` → `FOG_BTD_THRESHOLD = 2.0`
**Rationale:** Align with CIMSS/NOAA standards for nighttime fog detection

## Results

### Fog Suitability (≥80 days)

| Metric | Before (0.0 K) | After (2.0 K) | Change |
|--------|---------------|---------------|--------|
| **STATISTICS_MEAN** | 0.998 (99.8%) | 0.345 (34.5%) | **-65.3%** ✓ |
| Mean fog days | 167.0 days | 54.0 days | -113.0 days |
| Suitable pixels | 122,602 / 122,802 | 42,360 / 122,802 | -80,242 pixels |

**✓ Success:** Fog criterion now provides meaningful discrimination (not 99.8% suitable everywhere)

### Combined Suitability (Rainfall AND Fog)

| Metric | Before (0.0 K) | After (2.0 K) | Change |
|--------|---------------|---------------|--------|
| **Suitable area** | 83.2% | 12.2% | **-71.0%** |
| Suitable pixels | 67,666 / 81,281 | 9,951 / 81,281 | -57,715 pixels |
| Mean fog (suitable) | 169.2 days | 103.7 days | -65.5 days |

### Ground Truth Validation

| Location | Before (0.0 K) | After (2.0 K) |
|----------|---------------|---------------|
| Redwood Regional Park, Tres Sendas | ✓ PASS | ✓ PASS |
| Redwood Regional Park, Old Church | ✓ PASS | ✓ PASS |
| **Muir Woods**, Bridge 2 | ✓ PASS | ✗ **FAIL** |
| The Elbow Tree | ✓ PASS | ✗ **FAIL** |
| Grove of Old Trees | ✓ PASS | ✗ **FAIL** |
| Armstrong Redwoods | ✓ PASS | ✗ **FAIL** |
| **Humboldt Redwoods State Park** | ✓ PASS | ✗ **FAIL** |
| Navarro River Redwoods State Park | ✓ PASS | ✓ PASS |
| **TOTAL** | **8/8 (100%)** | **3/8 (37.5%)** |

**✗ Problem:** Failing famous redwood locations (Muir Woods, Humboldt Redwoods)

## Interpretation

### What Worked
1. **Fog criterion now discriminates:** 99.8% → 34.5% suitable
2. **Spatial patterns visible:** Fog no longer uniform across region
3. **Standard methodology:** Using CIMSS-recommended 2.0 K threshold

### What's Concerning
1. **Muir Woods FAILED** - One of the most iconic foggy redwood groves in the world
2. **Humboldt Redwoods FAILED** - THE archetypal old-growth redwood location
3. **Armstrong Redwoods FAILED** - Major redwood state park
4. **5/8 failures overall** - Model is rejecting known excellent redwood habitat

### Likely Explanations

**Hypothesis 1: 2.0 K Too Conservative for California Coastal Fog**
- CIMSS standards may target different fog types (radiation fog, valley fog)
- California marine layer may have weaker BTD signal than typical fog
- Threshold calibrated for different geographic regions

**Hypothesis 2: Nighttime Fog ≠ Daytime Fog Persistence** (Primary Issue)
- We measure: Nighttime fog (06-12 UTC = 11pm-5am PST)
- Heuristic requires: "Fog past noon 80 days/season"
- These locations may have nighttime fog that burns off by noon
- Our measurement doesn't capture what matters ecologically

**Hypothesis 3: 80-Day Threshold Inappropriate for Nighttime-Only**
- Original threshold assumes 24-hour fog measurements
- Nighttime-only sampling may need different threshold
- Maybe 40 nighttime fog days ≈ 80 daytime persistence days?

## Recommendation

### Immediate Options

**Option A: Try Lower Threshold (1.0 K or 1.5 K)**
- Quick test to see if intermediate value validates ground truth
- May find "sweet spot" between discrimination and validation
- Risk: Empirical tuning without theoretical justification

**Option B: Lower 80-Day Threshold**
- Test 40, 50, 60 days for nighttime fog
- Find threshold that validates 7-8 ground truth points
- Risk: Arbitrary adjustment of heuristic

**Option C: Accept Limitations, Document, Implement Daytime Detection**
- v0: Use 2.0 K, note validation failures, clear documentation
- v1: Implement daytime fog detection (Ticket #22) - THE REAL SOLUTION
- Honest about current limitations

### My Recommendation

**Try Option A first** (1.5 K threshold):
- 15 minutes to test
- Will show if there's a viable intermediate value
- If it validates 7-8 points and shows 25-40% suitable → use it
- If it still fails, confirms we need daytime fog detection

**Long-term: Option C** (daytime fog detection is required)
- Nighttime fog fundamentally doesn't measure "fog past noon"
- This is why famous locations are failing
- Daytime detection is the scientifically correct solution

## Files Changed

**New documentation:**
- `FOG_THRESHOLD_INVESTIGATION.md` - Full technical analysis
- `FOG_THRESHOLD_NEXT_STEPS.md` - Decision framework
- `BTD_THRESHOLD_2K_RESULTS.md` - Detailed results (this threshold)

**Scripts:**
- `scripts/11_create_real_fog_layer.py` - BTD threshold changed to 2.0 K
- `scripts/15_quick_btd_check.py` - BTD diagnostic tool

**Outputs:**
- `outputs/bay_area_fog_80days_goes16.tif` - Regenerated with 2.0 K
- `outputs/bay_area_fog_days_goes16.tif` - Regenerated with 2.0 K
- `outputs/bay_area_redwood_suitable.tif` - Regenerated (12.2% suitable)
- Web tiles - Regenerated (31,069 tiles, 10.9 MB)

**Web interface:**
- `web/index.html` - Updated statistics and warnings

All changes staged, ready to view in QGIS/browser.

## Next Steps

1. **Review in QGIS:** Check if spatial patterns look reasonable
2. **Review in browser:** Check web tile rendering
3. **Decide on threshold:**
   - Keep 2.0 K (standard but fails ground truth)
   - Try 1.5 K (compromise)
   - Try 1.0 K (more liberal)
   - Accept nighttime limitation and document
4. **Consider daytime fog detection priority**

---

**Bottom line:** The threshold change worked (fog now discriminates) but may be too conservative (failing famous redwood locations). Likely need daytime fog detection for proper validation.
