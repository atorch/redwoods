# BTD Threshold 2.0 K - Results and Analysis

## Change Implemented

**Script:** `scripts/11_create_real_fog_layer.py`
**Line 52:** Changed `FOG_BTD_THRESHOLD` from 0.0 K to 2.0 K
**Date:** 2026-04-13
**Rationale:** Align with CIMSS/NOAA standards for nighttime fog detection

## Results: Fog Layer Statistics

### Binary Fog Threshold (≥80 days)

**Before (0.0 K threshold):**
```
Fog days range: 32.9 - 184.0 days
Fog days mean: 167.0 days
Suitable pixels (≥80 days): 122,602 / 122,802 (99.8%)
```

**After (2.0 K threshold):**
```
Fog days range: 0.0 - 144.6 days
Fog days mean: 54.0 days
Suitable pixels (≥80 days): 42,360 / 122,802 (34.5%)
```

**Change:** STATISTICS_MEAN dropped from **0.998 → 0.345** ✓

This confirms the threshold change is working as expected - much more selective fog detection.

## Results: Combined Suitability

**Before (0.0 K threshold):**
```
Rainfall suitable: 67,866 / 81,281 (83.5%)
Fog suitable: 122,602 / 122,802 (99.8%)
Combined suitable: 67,666 / 81,281 (83.2%)
Ground truth validation: 8/8 PASS (100%)
```

**After (2.0 K threshold):**
```
Rainfall suitable: 67,866 / 81,281 (83.5%)
Fog suitable: 42,360 / 122,802 (34.5%)
Combined suitable: 9,951 / 81,281 (12.2%)
Ground truth validation: 3/8 PASS (37.5%)
```

**Impact:** Suitability dropped from 83.2% → **12.2%** (71% reduction)

## Ground Truth Validation Failures

### PASSED (3/8):
1. ✓ Redwood Regional Park, Tres Sendas bridge (37.8237, -122.1758)
2. ✓ Redwood Regional Park, Old Church (37.8111, -122.1561)
3. ✓ Navarro River Redwoods State Park (39.1765, -123.6899)

### FAILED (5/8):
1. ✗ **Muir Woods**, Bridge 2 (37.8959, -122.5755) - One of the most famous foggy redwood groves in California!
2. ✗ The Elbow Tree (37.4106, -122.3594)
3. ✗ Grove of Old Trees (38.3988, -122.9914)
4. ✗ Armstrong Redwoods (38.5372, -123.0066) - Major state park with ancient redwoods
5. ✗ **Humboldt Redwoods State Park** (40.3147, -123.9780) - THE iconic redwood location!

## Critical Issue: Famous Redwood Locations Failing

**This is a red flag!** Locations like Muir Woods and Humboldt Redwoods are:
- World-famous for their redwood groves
- Known to be extremely foggy in summer
- Core habitat for coastal redwoods
- Should absolutely pass any valid fog criterion

**Hypothesis:** The 2.0 K threshold is detecting dense fog, but:
1. California coastal fog may be less dense than typical CIMSS fog thresholds
2. Nighttime sampling misses critical daytime fog
3. Our 80-day threshold may be inappropriate for nighttime-only measurements

## Interpretation

### Success: Fog Criterion Now Discriminates
- 0.0 K: 99.8% suitable = fog criterion useless
- 2.0 K: 34.5% suitable = fog criterion highly selective
- Fog is now providing real spatial discrimination

### Problem: Too Selective - Excluding Known Redwood Habitat
- Failing Muir Woods and Humboldt Redwoods is unacceptable
- These are the archetypical redwood locations
- If our model says these aren't suitable, the model is wrong

## Possible Explanations

### 1. Threshold Too High (2.0 K too conservative)
- CIMSS standards may be for different fog types (radiation fog, valley fog)
- California coastal fog/marine layer may have weaker BTD signal
- **Solution:** Try 1.0 K or 1.5 K threshold

### 2. Nighttime-Only Sampling Insufficient
- We measure pre-dawn fog (06-12 UTC = 11pm-5am PST)
- These locations may have daytime fog that we're missing
- Nighttime fog frequency doesn't correlate with ecological fog importance
- **Solution:** Implement daytime fog detection (Ticket #22)

### 3. 80-Day Threshold Inappropriate for Nighttime Fog
- Original heuristic: "fog past noon 80 days/season"
- Our measurement: "nighttime fog ≥80 days/season"
- These may not be equivalent
- Maybe 40 nighttime fog days = 80 daytime fog persistence days?
- **Solution:** Adjust threshold or measure daytime fog

### 4. Extrapolation Error
- We sampled 28 days, extrapolated to 184 days (6.57x)
- Sample period may not be representative
- **Solution:** Multi-year climatology or more weeks

## Recommended Next Steps

### Option A: Try 1.0 K or 1.5 K Threshold
**Quick test:** Change threshold to intermediate value
- Lower than 2.0 K (less conservative)
- Higher than 0.0 K (more selective than original)
- Check if Muir Woods and Humboldt pass

**Pros:** Quick to test (10 min reprocessing)
**Cons:** Still nighttime-only, empirical threshold tuning

### Option B: Lower 80-Day Threshold
**Test nighttime fog thresholds:** 40, 50, 60 days instead of 80
- Maybe nighttime fog 40-60 days ≈ daytime persistence 80 days?
- Check which threshold validates all ground truth

**Pros:** May better match nighttime sampling to daytime criterion
**Cons:** No theoretical justification, arbitrary tuning

### Option C: Accept Nighttime Fog Limitation + Implement Daytime Detection
**v0:** Document that current approach has limitations
- Use 2.0 K threshold (standard practice)
- Note that validation is incomplete (5/8 failures)
- Clearly state this is preliminary/exploratory

**v1:** Implement proper daytime fog detection
- Download afternoon GOES data
- Measure actual "fog past noon" frequency
- This should properly validate ground truth

**Pros:** Scientifically honest, clear path forward
**Cons:** v0 doesn't fully validate heuristic

## My Recommendation

**Immediate:** Try threshold sweep (1.0 K, 1.5 K, 2.0 K) to find value that:
1. Provides spatial discrimination (not 99.8% suitable)
2. Validates at least 7/8 ground truth points (ideally 8/8)
3. Produces reasonable suitability percentage (20-50%?)

**Rationale:**
- Quick to test (<30 min)
- Will show if there's a sweet spot
- If no threshold works, confirms we need daytime fog detection

**Long-term:** Implement daytime fog detection (Ticket #22) as priority v1 work
- This is the real solution
- Nighttime fog is fundamentally the wrong measurement

## Questions for Decision

1. **Should Muir Woods and Humboldt Redwoods be non-negotiable passes?**
   - If yes: Need to find threshold or approach that validates them
   - If no: Accept that nighttime fog proxy has limitations

2. **What threshold to try next?**
   - 1.0 K (midpoint)
   - 1.5 K (compromise)
   - Variable threshold based on latitude/geography?

3. **What is acceptable validation rate?**
   - 8/8 required (100%)
   - 7/8 acceptable (87.5%)
   - 6/8 acceptable (75%)

4. **Priority of daytime fog detection?**
   - v0 blocker: Must implement before publication
   - v1 priority: Acknowledge v0 limitations, fix in v1
   - Future work: Defer to later

## Current Status

**Threshold:** 2.0 K (CIMSS standard)
**Fog suitable:** 34.5% (down from 99.8%) ✓
**Combined suitable:** 12.2% (down from 83.2%)
**Ground truth validation:** 3/8 PASS (down from 8/8) ✗

**Conclusion:** Threshold change is working (more selective) but may be too conservative (failing famous redwood locations). Need to decide on threshold tuning vs accepting nighttime fog limitations vs implementing daytime fog detection.
