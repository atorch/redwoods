# Fog Detection Threshold Investigation

## Problem Identified

**Issue:** 99.8% of pixels show sufficient fog (≥80 days), making the fog criterion nearly meaningless.

**Current fog statistics:**
- Minimum: 32.9 days (only 0.2% of pixels below 80-day threshold)
- Maximum: 184.0 days
- Mean: 167.0 days
- Threshold: ≥80 days required

**Result:** Suitability layer is essentially just the rainfall layer, since fog condition holds almost everywhere.

## Root Cause Analysis

### Current BTD Threshold: 0.0 K (TOO LENIENT)

From `scripts/11_create_real_fog_layer.py`:
```python
FOG_BTD_THRESHOLD = 0.0  # Line 52
fog_mask = btd > FOG_BTD_THRESHOLD  # Line 211
```

This means we detect "fog" whenever `BT_Ch13 - BT_Ch7 > 0K`.

### Standard CIMSS/NOAA Thresholds

According to NOAA/CIMSS fog detection literature:
- **Typical nighttime fog BTD threshold: 2-4 K** (not 0 K)
- BTD > 0K can indicate many conditions besides fog (thin clouds, moisture, etc.)
- More stringent thresholds (2-4K) are needed to distinguish fog from other phenomena

### Why This Matters

With BTD > 0K threshold:
- Detecting any slight temperature difference as "fog"
- Likely capturing thin clouds, marine layer, general moisture
- Not distinguishing dense coastal fog from other atmospheric conditions
- Result: Over-estimating fog frequency by possibly 2-3x

## Potential Contributing Factors

### 1. Nighttime-Only Sampling
- We sample 06-12 UTC (11pm-5am PST) = nighttime/pre-dawn hours
- This is when marine layer is most common along California coast
- BTD signal strongest at night, but we may be too sensitive

### 2. Limited Temporal Sample
- 4 weeks in 2024 (May, June, August, September)
- Total: 28 sample days across dry season
- Extrapolation factor: 6.57x (28 days → 184 days)
- If sample period was exceptionally foggy/cloudy: bias in extrapolation

### 3. Coastal Geography
- Study area: Northern California coast (Bay Area to Humboldt)
- This region IS genuinely very foggy in summer
- However, inland areas (valleys, mountains) should show less fog
- Current results show almost uniform high fog frequency (suspicious)

## Investigation Steps

### Immediate Diagnostics

1. **Sample BTD value distribution:**
   - What % of pixels have BTD > 0K vs > 2K vs > 4K?
   - Check if most BTD values are in 0-2K range (weak signal)

2. **Spatial pattern analysis:**
   - Does fog frequency decrease inland? (it should)
   - Compare coastal vs inland pixels
   - Check if Humboldt (very foggy) shows higher values than Central Valley edges

3. **Temporal pattern:**
   - Are we detecting "fog" in 25-28 out of 28 sample days? (would explain 167-day mean)
   - Check individual day fog detection rates

### Threshold Sensitivity Analysis

Test different BTD thresholds:
- **0.0 K** (current): 99.8% suitable
- **2.0 K** (CIMSS recommended): ?% suitable
- **4.0 K** (conservative): ?% suitable

### Literature Review

Need to verify:
- Standard CIMSS nighttime fog BTD threshold
- NOAA GOES-16 fog product methodology
- California-specific fog detection studies

## Recommended Next Steps

### Option 1: Fix BTD Threshold (IMMEDIATE)
**Action:** Change `FOG_BTD_THRESHOLD` from 0.0 to 2.0 or 3.0 K
**Risk:** Low - this is standard practice
**Effort:** Minimal - one line change, rerun fog processing
**Outcome:** More realistic fog detection, better spatial discrimination

### Option 2: Calibrate Against Ground Truth
**Action:**
- Sample BTD values at known foggy locations (Muir Woods, Humboldt)
- Sample BTD values at known less-foggy locations (inland valleys)
- Determine threshold that best separates these

### Option 3: Multi-Year Climatology
**Action:** Download GOES-16 data from 2018-2024 (5-7 years)
**Risk:** Medium - requires significant data download/storage
**Effort:** High - 5-7x more data to process
**Outcome:** Reduces temporal sampling bias

### Option 4: Validate Against fog.today Data
**Action:** Compare our fog detection with fog.today's real-time GOES-16 fog product
**Outcome:** External validation of our methodology

## Priority Investigation

**Highest priority: Option 1** (Fix BTD threshold to 2-3 K)
- This is a clear methodological issue
- Easy to implement and test
- Standard practice in remote sensing literature

**Secondary: Diagnostic Analysis**
- Check BTD value distribution
- Verify spatial patterns (coast vs inland)
- Compare results with different thresholds

## References to Review

1. CIMSS Night Fog BTD Guide: https://cimss.ssec.wisc.edu/goes/OCLOFactSheetPDFs/ABIQuickGuide_NightFogBTD.pdf
2. NOAA GOES-R Fog Detection ATBD: https://www.star.nesdis.noaa.gov/goesr/documents/ATBDs/Baseline/ATBD_GOES-R_Fog_v1.0_Sep2010.pdf
3. fog.today methodology (UW-Madison Real Earth project)

## Diagnostic Results

### BTD Distribution Analysis (Sample GOES-16 Image)

Ran `scripts/15_quick_btd_check.py` on representative nighttime image:

**Full GOES-16 field of view:**
- BTD mean: -3.93 K (median: -1.47 K)
- BTD range: -53.03 K to 6.17 K
- Fog detection at different thresholds:
  - **0.0 K: 21.3%** (current threshold)
  - 1.0 K: 7.1%
  - **2.0 K: 4.4%** (CIMSS recommended)
  - **3.0 K: 2.4%** (conservative)
  - 4.0 K: 0.9%

### Key Insight

The 21.3% fog detection at 0.0 K threshold across the full GOES field is not obviously too high.

**However**, our study region (Northern California coast) is a subset that:
1. Is genuinely one of the foggiest regions in North America
2. We sample only nighttime hours (06-12 UTC = pre-dawn marine layer peak)
3. We sample summer months (May-Sep) when California coastal fog is most frequent

**Result:** Even with 0.0 K threshold, it's plausible that 99.8% of our specific coastal pixels show fog, because:
- We're looking at the foggiest part of the GOES view
- We're sampling the foggiest time of day
- We're sampling the foggiest season

### Two Competing Hypotheses

**Hypothesis 1: Threshold Too Lenient (0.0 K)**
- Detection of weak signals that aren't true fog
- Should use CIMSS standard of 2-3 K
- Would reduce false positives
- **Risk:** May be appropriate for other regions, but California coast really is that foggy

**Hypothesis 2: Region Really Is That Foggy (Nighttime Summer Coastal)**
- Northern California coast in summer is genuinely 99%+ foggy at night
- Our sampling (nighttime, coastal, summer) is biased toward maximum fog
- 0.0 K threshold may be acceptable for this specific use case
- **Risk:** Missing daytime fog (when BTD doesn't work) biases the result

### The Real Problem: Nighttime-Only Sampling

**This may be the actual issue:**
- We only sample 06-12 UTC (11pm-5am PST) = nighttime
- California coastal fog is most common at night/early morning
- Original heuristic: "fog lasts past noon 80 days/season"
- We're NOT detecting daytime fog (BTD fails in daylight)

**Result:** We're measuring "nighttime fog frequency" not "daytime fog persistence"

If nighttime fog is present 99% of nights but burns off by noon most days, we'd:
- Detect 99% fog coverage (nighttime)
- Fail the original heuristic (which requires fog past noon)

## Current Status

- **Issue confirmed:** 99.8% suitable fog is unrealistic for the original heuristic
- **Root cause (primary):** Nighttime-only sampling doesn't measure "fog past noon"
- **Root cause (secondary):** BTD threshold of 0.0 K may be too lenient
- **Immediate fixes available:**
  1. Increase BTD threshold to 2-3 K (reduces false positives)
  2. Document that v0 measures nighttime fog, not daytime persistence
  3. Implement daytime fog detection (Ticket #22) for true heuristic validation
- **Decision needed:** Which threshold to use (0, 2, or 3 K)?
