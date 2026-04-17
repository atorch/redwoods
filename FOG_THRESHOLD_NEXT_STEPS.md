# Fog Threshold Investigation - Next Steps

## Summary of Findings

**Problem:** 99.8% of pixels show sufficient fog (≥80 days), making fog criterion ineffective.

**Root causes identified:**
1. **Primary:** Nighttime-only sampling captures pre-dawn marine layer (universal along coast) rather than "fog past noon" persistence (the original heuristic)
2. **Secondary:** BTD threshold of 0.0 K may be too lenient (CIMSS recommends 2-3 K)

**Current v0 status:** Suitability layer is essentially just the rainfall layer, since fog condition holds almost everywhere.

## Options for Next Steps

### Option 1: Increase BTD Threshold (Quick Fix)

**What:** Change `FOG_BTD_THRESHOLD` from 0.0 K to 2.0-3.0 K in `scripts/11_create_real_fog_layer.py`

**Pros:**
- Immediate fix (one line change)
- Aligns with CIMSS/NOAA standards
- Reduces false positives from weak BTD signals
- Will create better spatial discrimination (coastal vs inland)

**Cons:**
- Still only measures nighttime fog, not "fog past noon"
- May overcorrect and miss valid fog signals
- Doesn't address fundamental mismatch with original heuristic

**Effort:** Low (5 minutes to change + 30 minutes to reprocess + regenerate tiles)

**Recommendation:** Change to 2.0 K as immediate improvement

### Option 2: Accept Nighttime Fog as Proxy + Document Limitation

**What:** Keep current approach, clearly document that v0 measures "nighttime fog frequency" not "daytime fog persistence"

**Pros:**
- No reprocessing needed
- Northern California coast genuinely has near-universal nighttime fog in summer
- Honest about what we're measuring
- Can still be useful for identifying areas with NO fog (rare, but informative)

**Cons:**
- Doesn't validate original heuristic
- Fog criterion provides almost no discrimination
- Scientifically less rigorous

**Effort:** Low (documentation only)

**Recommendation:** Do this in addition to Option 1, not instead of it

### Option 3: Implement Daytime Fog Detection (Ticket #22)

**What:** Download daytime GOES-16 data (19-00 UTC = 12pm-5pm PST), implement visible channel fog detection

**Pros:**
- Addresses the real issue (nighttime vs daytime fog)
- Enables proper validation of "fog past noon" criterion
- More ecologically meaningful for redwood habitat
- Much better spatial discrimination expected

**Cons:**
- Significant effort (~2-3 days work)
- Requires downloading more GOES data (~3 GB)
- Algorithm more complex (visible + IR channels)
- Threshold tuning needed for California conditions

**Effort:** High (see Ticket #22 for full implementation plan)

**Timeline:** Could be done as follow-up work after v0 publication

**Recommendation:** Priority follow-up for v1

### Option 4: Hybrid Approach (Recommended)

**What:** Combine Options 1 and 2 for v0, plan Option 3 for v1

**v0 immediate actions:**
1. Increase BTD threshold to 2.0 K (better nighttime fog detection)
2. Update all documentation to state "nighttime fog frequency ≥80 days"
3. Note limitation prominently in web interface and documentation
4. Acknowledge that this is a proxy, not the original "fog past noon" criterion

**v1 future work:**
1. Implement daytime fog detection (Ticket #22)
2. Measure actual "fog past noon" frequency
3. Validate against original heuristic
4. Compare nighttime vs daytime fog patterns

**Pros:**
- Improved v0 with minimal effort
- Honest about limitations
- Clear path to v1 improvement
- v0 is still useful (nighttime fog IS ecologically relevant)

**Cons:**
- v0 won't fully validate original heuristic
- Need to be clear about limitations in any publications/presentations

**Effort:** Low for v0 (1 hour), High for v1 (2-3 days)

**Recommendation:** This is the best path forward

## Immediate Implementation Steps (Option 4)

### Step 1: Update BTD Threshold (30 minutes)

```bash
# Edit scripts/11_create_real_fog_layer.py
# Change line 52 from:
FOG_BTD_THRESHOLD = 0.0

# To:
FOG_BTD_THRESHOLD = 2.0  # CIMSS nighttime fog detection standard
```

### Step 2: Reprocess Fog Layer (30 minutes)

```bash
# Reprocess with new threshold
uv run python scripts/11_create_real_fog_layer.py

# Check new statistics
gdalinfo outputs/bay_area_fog_80days_goes16.tif -stats | grep MEAN

# Expected: Lower percentage of suitable pixels (60-80% instead of 99.8%)
```

### Step 3: Regenerate Suitability and Tiles (30 minutes)

```bash
# Regenerate suitability layer
uv run python scripts/04_combine_suitability.py

# Validate ground truth points still pass
# (all 8 should still be suitable if threshold is reasonable)

# Regenerate web tiles
rm -rf tiles/ outputs/bay_area_redwood_suitable_cog.tif
uv run python scripts/13_generate_web_tiles.py
```

### Step 4: Update Documentation (30 minutes)

Update the following to clarify "nighttime fog":
- `web/index.html` - info panel text
- `web/README.md` - data sources section
- `README.md` - heuristic description
- All scripts - comments/docstrings

### Step 5: Git Commit

```bash
git add -A
git commit -m "Increase BTD threshold to 2.0 K for more selective fog detection

- Change FOG_BTD_THRESHOLD from 0.0 K to 2.0 K (CIMSS standard)
- Update documentation to clarify nighttime fog limitation
- Note: Still measures nighttime fog, not 'fog past noon' criterion
- See FOG_THRESHOLD_INVESTIGATION.md for analysis
- Daytime fog detection (Ticket #22) planned for v1"
```

## Long-term Recommendation

**For scientific rigor and validating the original heuristic:**
Implement daytime fog detection (Ticket #22) as priority work for v1 or next phase. This will:
- Properly measure "fog past noon" frequency
- Provide much better spatial discrimination
- Be more ecologically meaningful for redwood habitat modeling
- Enable true validation of the academic heuristic

**For now (v0):**
Increase BTD threshold to 2.0 K, document limitations clearly, and acknowledge this as a preliminary analysis using nighttime fog as a proxy for fog availability.

## Questions for Decision

1. **What BTD threshold to use?**
   - Recommended: 2.0 K (standard CIMSS value)
   - Conservative: 3.0 K (denser fog only)
   - Current: 0.0 K (too lenient)

2. **How to label the fog criterion?**
   - Honest: "Nighttime fog frequency ≥80 days"
   - Aspirational: "Fog frequency ≥80 days" (with footnote about nighttime limitation)

3. **Priority of daytime fog detection?**
   - v0 only: Accept nighttime fog limitation
   - v1 priority: Implement daytime fog detection soon
   - Future work: Defer to later phase

4. **Validation criteria?**
   - Should all 8 ground truth points still pass with higher threshold?
   - What % suitable is reasonable? (Currently 83.2% with rainfall, would be ~83% with fog if 0.0 K → probably 60-75% with 2.0 K)
