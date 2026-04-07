# Process Fog Afternoon Persistence Metrics

## Objective
Create rasters quantifying fog persistence past noon during dry season (May-Oct) to support 80+ days threshold from historical heuristic.

## Tasks
- [ ] Define "afternoon" time window (e.g., 12pm-6pm local time)
- [ ] For each day in dry season (May-Oct), detect fog presence in afternoon hours
- [ ] Aggregate across multiple years to create climatology
- [ ] Generate metrics:
  - **Primary**: Average days per dry season with fog past noon
  - **Secondary**: Average hours/day of fog by month (May-Oct)
- [ ] Create 80+ day threshold layer for heuristic validation

## Outputs
- `fog_afternoon_days_dry_season.tif` - average days/season with afternoon fog
- `fog_hours_per_day_[month].tif` - monthly fog duration (6 rasters for May-Oct)
- `fog_80day_threshold.tif` - binary layer (1 = meets 80+ day criteria)

## Dependencies
- Ticket #03: Acquire GOES-16 fog data
- Ticket #03b: Investigation and decision on fog metric approach

## Notes
- May need to account for satellite artifacts noted in fog.today documentation
- Consider validating against NOAA weather station fog observations
- Dry season defined as May-October (confirm with literature)
