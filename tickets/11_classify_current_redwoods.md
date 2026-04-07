# Classify Current Redwood Distribution

## Objective
Use park boundaries, spectral classification, and potentially machine learning to map where redwoods are currently growing (Layer 1).

## Approach (to be refined)
Start with simple methods, increase complexity as needed:

1. **Known redwood areas** (baseline):
   - Use park boundaries as definite redwood presence

2. **Spectral classification**:
   - Calculate NDVI and other vegetation indices from NAIP
   - Identify evergreen/conifer signatures
   - Filter by elevation, slope, proximity to coast

3. **Machine learning** (if needed):
   - Train classifier on known redwood (parks) vs non-redwood areas
   - Random Forest or similar on spectral + topographic features
   - Validate and refine

4. **Optional enhancements**:
   - LiDAR canopy height to identify tall trees
   - Texture analysis to distinguish redwood groves from other forests

## Tasks
- [ ] Create training dataset from park boundaries
- [ ] Extract spectral features (NDVI, etc.) from NAIP
- [ ] Develop classification workflow
- [ ] Validate against ground truth
- [ ] Generate final "current redwoods" raster layer

## Outputs
- `current_redwoods_layer1.tif` - classified redwood presence/absence or probability
- Validation report with accuracy metrics
- Documentation of classification methodology

## Dependencies
- Ticket #08: Park boundaries (ground truth)
- Ticket #10: NAIP imagery
- Ticket #07: DEM data (for topographic filtering)

## Notes
- This is Layer 1 (current distribution)
- Accuracy depends on quality of training data and spectral distinctiveness
- May need to distinguish redwoods from Douglas fir, other tall conifers
- Consider confidence/probability rather than binary classification
