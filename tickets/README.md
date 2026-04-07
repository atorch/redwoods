# Redwoods Mapping Project - Tickets

## Overview

This directory contains individual work tickets for the redwoods mapping project. Tickets are organized by workflow phase.

## Ticket Organization

### Foundation (Start Here)
- **#05** - Define geographic extent and resolution
- **#06** - Set up Python environment (uv + geospatial libraries)

### Layer 2: Natural Suitable Habitat (Historical/Hypothetical Range)
*Three-criteria heuristic: north of San Simeon + fog persistence + wet season rainfall*

**Data Acquisition:**
- **#01** - Download PRISM monthly precipitation data
- **#03** - Acquire GOES-16 fog/cloud satellite data
- **#07** - Acquire DEM (elevation) data
- **#08** - Acquire park boundaries (known redwood areas for validation)

**Data Processing:**
- **#02** - Compute wet season rainfall totals (Nov-Apr) and 20" threshold
- **#03b** - Investigate fog metrics approach (research & decision)
- **#04** - Process fog afternoon persistence and 80-day threshold

**Integration:**
- **#09** - Combine heuristic layers into final suitable habitat map

### Layer 1: Current Redwood Distribution
*Spectral classification from imagery*

- **#10** - Acquire NAIP imagery (1m resolution, 4-band)
- **#11** - Classify current redwood distribution using imagery + ML

### Web Delivery
- **#20** - Create web map interface (placeholder - high-level)

## Workflow Dependencies

```
Foundation:
  #05 (extent) ──┬──> #06 (Python env)
                 │
                 ├──> Data Acquisition (Layer 2)
                 │      #01 (PRISM)
                 │      #03 (GOES-16)
                 │      #07 (DEM)
                 │      #08 (Parks)
                 │
                 └──> Data Acquisition (Layer 1)
                        #10 (NAIP)

Layer 2 Processing:
  #01 ──> #02 (wet season rainfall) ──┐
                                       │
  #03 ──> #03b (fog investigation) ──>├──> #09 (combine heuristic)
          #03b ──> #04 (fog process) ──┘

Layer 1 Processing:
  #08 + #10 + #07 ──> #11 (classify current redwoods)

Web Delivery:
  #09 + #11 ──> #20 (web map)
```

## Current Status
All tickets are in planning/TODO state. Recommended starting order:
1. **#05** - Define extent (foundational decision)
2. **#06** - Set up Python environment
3. **#01, #03, #07, #08, #10** - Data acquisition (can run in parallel)
4. Process data according to dependencies above

## Notes
- Initial visualization can be done in QGIS before web interface (#20) is built
- Layer 2 (suitable habitat) uses the same model for both historical (1750) and hypothetical ranges
- Tickets can be updated/refined as work progresses
