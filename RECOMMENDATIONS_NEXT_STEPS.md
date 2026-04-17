# Recommendations: Next Steps for Fog Detection

## Executive Summary

Good news: **Empirical BTD threshold tuning is standard practice** in the remote sensing literature.

The literature shows no universal BTD threshold - values range from -2.0 K to 7.5 K depending on fog type, region, and conditions. California coastal fog (marine layer) likely requires different thresholds than Midwest radiation fog or other fog types that CIMSS general guidance targets.

**Recommendation:** Try **1.5 K threshold** as immediate next step, with path to daytime fog detection for proper validation.

## Literature Findings (See LITERATURE_REVIEW_FOG_THRESHOLDS.md)

### Key Insights

1. **No single standard threshold exists**
   - Literature shows 4-7.5 K for some fog types
   - -2.0 K to 5.1 K for sea fog
   - California coastal fog may differ from all of these

2. **Empirical calibration is expected practice**
   - Quote from literature: "A fixed threshold value is not highly accurate"
   - Region-specific tuning using ground truth is scientifically rigorous
   - We have excellent ground truth (8 known redwood locations)

3. **Daytime fog detection is complex but doable**
   - Uses visible reflectance (0.65 µm) + IR temperature
   - Probability-based algorithms available
   - Would measure actual "fog past noon" criterion

## Three Options Evaluated

### Option A: BTD Threshold Tuning (RECOMMENDED IMMEDIATE)

**Action:** Test 1.5 K threshold (midpoint between 0.0 K and 2.0 K)

**Justification:**
- **Scientifically valid:** Literature supports empirical calibration
- **Quick test:** 15-20 minutes to reprocess and validate
- **Ground truth validation:** Proper methodology for threshold selection
- **California-specific:** Marine layer may need different threshold

**Expected outcome:**
- IF validates 7-8 points + shows 25-40% suitable: **Use it for v0**
- IF still fails Muir Woods/Humboldt: Try 1.0 K next
- IF 1.0 K also fails: Confirms need for daytime fog detection

**Effort:** 15-20 minutes
**Risk:** Low
**Scientific validity:** ✓ HIGH

### Option B: Multi-Year Data (RECOMMENDED SECONDARY)

**Action:** Download 2020-2023 nighttime data (same 4 weeks per year)

**Justification:**
- Reduces temporal sampling bias
- Current: 28 days from 2024
- Improved: 84-112 days from 2020-2024 (3-4 years)
- Better fog climatology

**Data requirements:**
- ~10 GB additional download
- Same weeks: May, June, August, September
- Years: 2020, 2021, 2022, 2023 (4 years total incl. 2024)

**Effort:** 3-4 hours (download + reprocessing)
**Risk:** Medium (may not solve nighttime vs daytime fundamental issue)
**Scientific validity:** ✓ HIGH (climatology is best practice)

### Option C: Daytime Fog Detection (RECOMMENDED V1)

**Action:** Implement visible channel fog detection for "fog at noon"

**Justification:**
- **Directly addresses heuristic:** "fog past noon 80 days/season"
- **Proper measurement:** Nighttime fog ≠ daytime persistence
- **Ecologically meaningful:** Redwoods need afternoon fog, not just pre-dawn

**Technical approach:**
1. Download daytime GOES-16 (19-21 UTC = 12pm-2pm PST)
2. Implement algorithm:
   - Visible reflectance (0.65 µm) > threshold
   - Spatial uniformity test
   - IR temperature < threshold (low cloud)
   - 3.9 µm daytime reflectance (small droplets)
3. Detect "fog at noon" specifically
4. Count days with noon fog ≥80 for dry season

**Effort:** 6-8 hours (research + implementation + testing)
**Risk:** High (complex algorithm, more threshold tuning)
**Scientific validity:** ✓✓ HIGHEST (measures actual heuristic criterion)

## Recommended Path Forward

### Phase 1: Quick Threshold Test (TODAY - 20 minutes)

```bash
# Test 1.5 K threshold
# Edit scripts/11_create_real_fog_layer.py line 52:
FOG_BTD_THRESHOLD = 1.5

# Reprocess
uv run python scripts/11_create_real_fog_layer.py
uv run python scripts/04_combine_suitability.py

# Check results:
# - How many ground truth points pass?
# - What % of study area is suitable?
# - Does fog pattern look reasonable?
```

**Decision criteria:**
- ✓ If 7-8/8 pass + 25-40% suitable + Muir Woods/Humboldt pass: **USE 1.5 K**
- ✗ If still failing key locations: Try 1.0 K
- ✗ If 1.0 K fails: Move to Phase 3 (daytime fog)

### Phase 2: Multi-Year Data (OPTIONAL - if Phase 1 succeeds)

Only if 1.5 K (or 1.0 K) threshold works:
```bash
# Download 2020-2023 nighttime data
# Add ~84 more sample days (3 more years)
# Reprocess with 4-year climatology
# More robust fog estimates
```

**Timeline:** Can be done after Phase 1 succeeds
**Purpose:** Improve v0 robustness, reduce temporal bias

### Phase 3: Daytime Fog Detection (V1 PRIORITY - if Phase 1 fails)

If empirical threshold tuning doesn't validate ground truth:
```bash
# This confirms nighttime fog ≠ "fog past noon"
# Need to implement proper daytime detection
# See Ticket #22 for full implementation plan
```

**Timeline:** Could be next week's work
**Purpose:** Proper validation of original heuristic

## Immediate Action Plan

**Right now:**

1. **Test 1.5 K threshold** (15-20 min)
   - Change FOG_BTD_THRESHOLD to 1.5
   - Reprocess fog + suitability
   - Check ground truth validation
   - Check spatial patterns

2. **Document results:**
   - How many points pass?
   - What is suitable percentage?
   - Do Muir Woods and Humboldt pass?

3. **Decision:**
   - IF good: Document, regenerate tiles, use for v0
   - IF not: Try 1.0 K
   - IF 1.0 K fails: Plan daytime fog detection

**Next (if threshold tuning works):**

4. **Optional:** Multi-year data download (2020-2023)
5. **Optional:** Regenerate with 4-year climatology

**Next (if threshold tuning fails):**

4. **Required:** Implement daytime fog detection
5. Measure actual "fog past noon" frequency

## Expected Outcomes

### Success Case (1.5 K or 1.0 K works):

**Ground truth:** 7-8/8 pass (including Muir Woods, Humboldt)
**Suitability:** 25-40% of study area
**Spatial pattern:** Strong coastal concentration, inland reduction
**Scientific validity:** Empirical calibration for CA coastal fog
**v0 status:** Ready to document and publish

**Documentation needed:**
- "BTD threshold of X.X K calibrated for California coastal marine layer"
- "Validated against 8 known redwood locations"
- "Note: Nighttime fog frequency used as proxy for fog availability"
- "Future work: Daytime fog detection for 'fog past noon' criterion"

### Failure Case (even 1.0 K too conservative):

**Conclusion:** Nighttime fog fundamentally doesn't correlate with daytime persistence
**Action required:** Implement daytime fog detection
**Timeline:** ~8 hours work, could be done this week
**v0 status:** Delayed until daytime detection implemented

## My Recommendation

**Try 1.5 K threshold right now** (literally 15-20 minutes to test).

**Why:**
- Literature supports this approach
- California marine layer may legitimately need lower threshold than CIMSS general guidance
- Quick to test, rigorous if validated with ground truth
- If it works: v0 is done
- If it fails: Confirms need for daytime detection

**How to decide:**
- 1.5 K validates Muir Woods + Humboldt → **Use it**
- 1.5 K fails → Try 1.0 K
- 1.0 K validates → **Use it**
- 1.0 K fails → **Implement daytime fog detection**

**Bottom line:** We should know in 30 minutes whether empirical threshold tuning will work or if we need daytime detection.
