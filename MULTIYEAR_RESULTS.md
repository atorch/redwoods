# Multi-Year GOES-16 Results (2020-2024)

## Processing Complete ✓

**Data processed:** 1,958 Ch7/Ch13 pairs (5 years, 140 sample days)
**BTD threshold:** 1.5 K
**Date:** 2026-04-15

## Fog Statistics Comparison

| Metric | 2024 Only (28 days) | 2020-2024 (140 days) | Change |
|--------|---------------------|----------------------|--------|
| **Mean fog days** | 62.1 days | 69.0 days | +6.9 days ✓ |
| **Fog suitable (≥80 days)** | 40.4% | 46.9% | +6.5% ✓ |
| **Combined suitable** | 16.9% | 19.0% | +2.1% ✓ |

**Improvement:** Multi-year data increased fog detection by ~11% (40.4% → 46.9%)

## Ground Truth Validation - Surprising Change

### Before (2024 only): 5/8 Pass

1. ✓ Redwood Regional Park, Tres Sendas
2. ✓ Redwood Regional Park, Old Church
3. ✓ **Muir Woods** - WAS PASSING
4. ✓ The Elbow Tree
5. ✗ Grove of Old Trees
6. ✗ Armstrong Redwoods
7. ✗ Humboldt Redwoods State Park
8. ✓ Navarro River Redwoods

### After (2020-2024): 6/8 Pass

1. ✓ Redwood Regional Park, Tres Sendas
2. ✓ Redwood Regional Park, Old Church
3. ✗ **Muir Woods** - NOW FAILING! ⚠️
4. ✓ The Elbow Tree
5. ✓ **Grove of Old Trees** - NOW PASSING ✓
6. ✗ Armstrong Redwoods
7. ✓ **Humboldt Redwoods** - NOW PASSING! ✓✓
8. ✓ Navarro River Redwoods

## Key Findings

### Good News ✓
- **Humboldt Redwoods now passes!** Major win - this is THE iconic redwood location
- **Grove of Old Trees now passes!**
- Overall validation: 6/8 (75%) vs 5/8 (62.5%)
- Suitability: 19.0% (reasonable range)

### Concerning ⚠️
- **Muir Woods now fails** - This is very strange!
  - 2024 had enough fog for Muir Woods (passed)
  - 2020-2024 average has less fog at Muir Woods? (fails)
  - Suggests 2024 was an unusually foggy year at Muir Woods specifically

- **Armstrong Redwoods still fails** - Major state park, should pass

## Interpretation

### Hypothesis: Geographic Variability in Fog Years

The fact that multi-year averaging caused Muir Woods to fail while Humboldt passed suggests:

1. **2024 was exceptionally foggy at Muir Woods**
   - Single year (2024) showed high fog
   - Multi-year average dilutes this

2. **2024 was less foggy at Humboldt**
   - Single year (2024) showed lower fog
   - Multi-year average brings it up

3. **Inter-annual variability is high**
   - Different locations have different fog patterns year-to-year
   - 5-year average is more representative, but...
   - If Muir Woods truly has fog but happened to be low 2020-2023, we're penalizing it

### The Core Problem Remains: Nighttime vs Daytime Fog

Even with multi-year data:
- Still failing 2/8 locations (25%)
- Muir Woods failing is unacceptable (world-famous foggy redwood grove)
- Suggests our measurement (nighttime fog) doesn't capture what matters

**Fundamental issue:** We're measuring "nighttime fog frequency" not "fog past noon persistence"
- These may not correlate well
- Muir Woods may have less pre-dawn fog but more afternoon fog
- Our method misses this

## Comparison to Single-Year Results

| Location | 2024 Only | 2020-2024 | Interpretation |
|----------|-----------|-----------|----------------|
| Muir Woods | ✓ PASS | ✗ FAIL | 2024 unusually foggy at this location |
| Humboldt | ✗ FAIL | ✓ PASS | 2024 less foggy, multi-year average higher |
| Grove of Old Trees | ✗ FAIL | ✓ PASS | 2024 less foggy, multi-year average higher |
| Armstrong | ✗ FAIL | ✗ FAIL | Consistently below threshold |

## Decision Matrix

### Option A: Accept 6/8 Validation (75%)

**Pros:**
- Humboldt Redwoods passes (THE key location)
- 75% validation is decent
- Multi-year climatology is more robust
- 19.0% suitable is reasonable

**Cons:**
- Muir Woods failing is problematic (iconic location)
- Armstrong Redwoods failing (major state park)
- 25% false negative rate

### Option B: Use 2024-Only Data (5/8 but includes Muir Woods)

**Pros:**
- Muir Woods passes (important)
- 2024 data may be more representative for some locations

**Cons:**
- Only 28 sample days (less robust)
- Humboldt Redwoods fails (unacceptable)
- Temporal sampling bias

### Option C: Lower Threshold to 1.0 K

**Quick test:** Try 1.0 K threshold with multi-year data
- May validate Muir Woods + Armstrong
- But may be too liberal (captures weak signals)

### Option D: Implement Daytime Fog Detection (Recommended)

**Why this is the real solution:**
- Measures actual "fog past noon" criterion
- Would resolve nighttime vs daytime discrepancy
- More ecologically meaningful
- Scientifically rigorous

**Effort:** ~6-8 hours
**Priority:** High (needed for proper validation)

## Recommendation

### Immediate: Test 1.0 K Threshold (15 minutes)

Try BTD threshold = 1.0 K with multi-year data:
- See if Muir Woods + Armstrong pass
- Check if overall pattern makes sense
- If 7-8/8 pass: use it
- If not: confirms daytime fog needed

### Near-term: Implement Daytime Fog Detection

Regardless of 1.0 K results, we should:
- Acknowledge nighttime-only limitation
- Plan daytime fog detection for v1
- This is needed for proper "fog past noon" validation

## Current Status

**Files updated:**
- `outputs/bay_area_fog_days_goes16.tif` - Multi-year climatology
- `outputs/bay_area_fog_80days_goes16.tif` - 46.9% suitable
- `outputs/bay_area_redwood_suitable.tif` - 19.0% suitable (6/8 validation)

**Ground truth: 6/8 pass (75%)**
- ✓ Humboldt Redwoods (iconic - CRITICAL WIN)
- ✗ Muir Woods (iconic - CONCERNING)
- ✗ Armstrong Redwoods (major state park)

**Next step:** Test 1.0 K threshold or proceed with daytime fog detection
