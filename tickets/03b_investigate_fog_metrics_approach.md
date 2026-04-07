# Investigate and Decide Fog Metric Approach

## Objective
Research GOES-16 data capabilities and determine which fog metrics to derive for the 80-day afternoon fog heuristic.

## Background
Historical heuristic requires: "fog lasts past noon 80 days/dry season"

GOES-16 provides high temporal resolution enabling afternoon fog detection. Need to decide on processing approach.

## Options to Evaluate

### Option A: Binary "fog past noon" day count
- **Approach**: For each day, detect if fog present after noon → count days per dry season
- **Pros**: Directly matches heuristic specification
- **Cons**: Less flexible, binary threshold may miss nuances
- **Output**: Single raster with "days per dry season with afternoon fog"

### Option B: Monthly average fog hours/day
- **Approach**: Calculate daily fog duration → aggregate to monthly averages
- **Pros**: Continuous variable, flexible, enables correlation analysis
- **Cons**: Doesn't directly match heuristic (requires threshold derivation)
- **Output**: 6 rasters (May-Oct) showing average fog hours per day

### Option C: Both metrics
- **Approach**: Derive both A and B from same underlying data
- **Pros**: Comprehensive, supports validation and multiple analyses
- **Cons**: More processing work and storage
- **Output**: Both metric sets from above

## Research Tasks
- [ ] Examine GOES-16 data structure and temporal resolution
  - What is native time resolution? (15min, hourly?)
  - How is fog/low cloud detected in the data products?
  - What artifacts exist (noted by fog.today)?
- [ ] Review fog.today methodology if documentation available
  - Contact creator Logan Williams for methodology details?
  - Examine "Fogust" historical data approach
- [ ] Prototype simple fog detection for sample area/time period
  - Test different thresholds for "fog present"
  - Validate against ground truth (NOAA stations, visual inspection)
- [ ] Estimate computational requirements for each option
- [ ] **Make recommendation and document decision**

## Recommended Approach (to validate)
Start with **Option B** (monthly average fog hours/day):
1. Acquire GOES-16 historical low cloud/fog data (May-Oct for multiple years)
2. For each pixel, calculate daily fog duration
3. Aggregate to monthly averages: "average hours/day of fog in May", "June", etc.
4. Create separate rasters for each dry season month
5. Can then derive "days with fog past noon" by applying thresholds (gets us Option A too)

**Rationale**: More flexible, supports derived metrics, enables correlation with other factors.

## Outputs
- Decision document explaining chosen approach and rationale
- Sample processing code demonstrating fog detection on subset of data
- Validation results comparing GOES-16 fog detection to ground truth
- Updated processing plan for ticket #04

## Dependencies
- Ticket #03: Acquire GOES-16 fog data (sample data for testing)

## Notes
- This is primarily a research/investigation ticket
- Decision should be documented before proceeding to full processing
- Consider computational trade-offs: processing time vs storage vs flexibility
