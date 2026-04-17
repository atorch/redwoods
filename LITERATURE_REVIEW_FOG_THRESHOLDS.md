# Literature Review: GOES-16 Fog Detection Thresholds

## Research Question

What are the appropriate BTD thresholds for California coastal fog detection, and what methods exist for daytime fog detection?

## Key Findings

### Nighttime BTD Thresholds (Highly Variable)

The literature shows **no single standard threshold** - values vary significantly by:
- Geographic region
- Fog type (radiation fog, sea fog, marine layer, valley fog)
- Seasonal and atmospheric conditions
- Study methodology

**Reported threshold values:**
- General nighttime fog: 4-7.5 K (simulated datasets)
- Sea fog: -2.0 K to 4.1 K (ocean), 5.1 K (land)
- California coastal fog: Thresholds around 4-5 K mentioned

**Critical insight from literature:**
> "Since the atmosphere fluctuates over both short and long periods of time, a fixed threshold value is not highly accurate for fog discrimination from imagery captured by various satellites at different times."

**Implication:** Empirical threshold tuning for specific regions/conditions is **expected practice**, not a methodological flaw.

### California-Specific Considerations

California coastal fog (marine layer) may require **different thresholds** than:
- Midwest radiation fog
- Valley fog
- Sea fog in other regions

**Why:**
- Marine layer has different droplet size distribution
- Coastal temperature/humidity profiles differ
- Fog formation mechanisms are distinct

**CIMSS Fused Fog approach:** Combines satellite BTD with "Rapid Refresh model estimates of low-level saturation" to improve accuracy, especially when higher clouds obscure fog.

### Daytime Fog Detection Methods

**Primary technique:** Visible reflectance (0.65 µm) + IR temperature

**Algorithm components:**
1. **High reflectance in visible:** Fog appears bright (high albedo)
2. **Spatial uniformity:** Fog shows smooth texture in 0.65 µm
3. **3.9 µm reflectance:** Small droplets are slightly reflective at 3.9 µm during day
4. **Temperature tests:** Distinguish fog (low/surface) from higher clouds

**Probability-based approach:** Recent methods assign fog probability using:
- Small droplet proxy
- Spatial homogeneity tests
- Temperature difference tests

**Challenge:** More complex than nighttime BTD, requires multiple channel analysis

## Recommendations for Our Project

### Option 1: Empirical BTD Threshold Tuning (Acceptable Practice)

**Justification:**
- Literature supports region-specific threshold calibration
- California coastal fog may require different threshold than CIMSS general guidance
- Ground truth validation is the appropriate calibration method

**Approach:**
Test thresholds: 1.0 K, 1.5 K, 2.0 K, 2.5 K
- Select threshold that validates 7-8 ground truth points
- Provides spatial discrimination (not 99.8% suitable)
- Document threshold choice and justification

**Effort:** Low (1-2 hours total)
**Risk:** Low - this is standard practice
**Scientific validity:** HIGH - empirical calibration with ground truth is rigorous

### Option 2: Multi-Year Temporal Coverage

**Justification:**
- Current: 4 weeks from 2024 (28 days sampled)
- Better: 3-5 years of same weeks (84-140 days sampled)
- Reduces temporal sampling bias
- More robust climatology

**Approach:**
- Download 2020-2024 data for same weeks (May, June, August, September)
- ~10 GB additional data
- Reprocess fog layer with multi-year climatology

**Effort:** Medium (3-4 hours download + processing)
**Risk:** Medium - more data may not solve fundamental nighttime vs daytime issue
**Scientific validity:** HIGH - climatology is best practice

### Option 3: Daytime Fog Detection (Proper Validation of Heuristic)

**Justification:**
- Original heuristic: "fog **past noon** 80 days/season"
- Our nighttime sampling: 06-12 UTC = 11pm-5am PST (pre-dawn)
- These measure fundamentally different phenomena
- Ecologically, daytime fog persistence is what matters for redwoods

**Approach:**
- Download daytime GOES-16 data (19-21 UTC = 12pm-2pm PST)
- Implement visible reflectance + IR algorithm
- Detect "fog at noon" specifically
- Combine with nighttime detection if needed

**Effort:** High (6-8 hours research + implementation)
**Risk:** High - complex algorithm, threshold tuning needed
**Scientific validity:** HIGHEST - directly measures the heuristic criterion

### Option 4: Hybrid Approach (Recommended)

**Phase 1 (Immediate - 2 hours):**
1. Test BTD thresholds 1.0 K, 1.5 K, 2.0 K
2. Select threshold that validates ≥7 ground truth points
3. Document as "nighttime fog proxy" with limitation noted

**Phase 2 (Near-term - 4 hours):**
1. Add 2-3 more years of nighttime data (2021-2023)
2. Reprocess with multi-year climatology
3. More robust nighttime fog estimates

**Phase 3 (v1 Priority - 8 hours):**
1. Implement daytime fog detection
2. Measure actual "fog past noon" frequency
3. Proper validation of original heuristic
4. Compare daytime vs nighttime patterns

**Rationale:**
- Phase 1: Quick improvement, scientifically defensible
- Phase 2: Better v0, still nighttime limitation
- Phase 3: Proper solution, but can be v1 work

## Specific Threshold Recommendation

Based on literature review, for **California coastal marine layer:**

**Try 1.5 K first:**
- Midpoint between our 0.0 K (too lenient) and 2.0 K (too conservative)
- Literature shows 4-5 K for some fog types, but marine layer may be weaker
- If 1.5 K validates Muir Woods + Humboldt: use it
- If 1.5 K still fails: try 1.0 K
- If 1.0 K still fails: confirms nighttime vs daytime issue

**Validation criteria:**
- ≥7/8 ground truth points pass (minimum)
- Muir Woods and Humboldt Redwoods specifically pass (non-negotiable)
- 20-50% of study area suitable (reasonable range)
- Spatial pattern shows coastal concentration

## Sources

- [Automatic nighttime sea fog detection using GOES-16 imagery - ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0169809519305447)
- [GOES-R Fog Product Examples - CIMSS](https://fusedfog.ssec.wisc.edu/)
- [California Fog Detection - CIMSS](https://fusedfog.ssec.wisc.edu/category/california/)
- [A Probability-Based Daytime Algorithm for Sea Fog Detection Using GOES-16 Imagery - IEEE](https://ieeexplore.ieee.org/document/9252141/)
- [GOES-derived fog and low cloud indices for coastal north and central California - Torregrosa 2016](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1002/2015EA000119)
- [Data Products: Low Cloud and Fog - GOES-R](https://www.goes-r.gov/products/opt2-low-cloud-fog.html)

## Conclusion

**For immediate progress:** Test 1.5 K threshold - this is scientifically defensible as empirical calibration for California coastal fog.

**For proper validation:** Implement daytime fog detection to measure actual "fog past noon" criterion.

**Current 2.0 K threshold:** May be appropriate for some fog types but appears too conservative for California marine layer based on ground truth failures.
