# Acquire GOES-16 Fog Data

## Objective
Obtain GOES-16 satellite data to analyze fog patterns, specifically afternoon fog persistence during dry season (May-Oct).

## Tasks
- [ ] Research GOES-16 data access methods
  - UW-Madison Space Science & Engineering Center's Real Earth project
  - NOAA GOES-16 archives
  - Potentially contact fog.today creator for methodology
- [ ] Identify appropriate GOES-16 product for fog detection
  - Low cloud/fog product or raw channels?
  - Temporal resolution available (hourly?)
- [ ] Determine historical time period needed
  - Multiple years for climatology (5-10 years?)
  - Or use most recent complete dry season?
- [ ] Download sample data for pilot area (e.g., SF Bay Area)
- [ ] Document data format, resolution, and artifacts/limitations

## Outputs
- GOES-16 fog/cloud data for study area
- Documentation of data source, product type, and known limitations
- Sample processing script demonstrating data access

## Dependencies
- Need to define geographic extent and temporal scope

## Notes
- fog.today notes potential artifacts and inaccuracies in satellite data
- May need to validate against ground truth (NOAA weather stations)
- High temporal resolution is key advantage (enables "past noon" filtering)
