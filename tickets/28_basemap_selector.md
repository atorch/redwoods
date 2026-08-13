# Basemap Selector (Satellite / Terrain)

> **Status:** TODO — capturing intent.

## Problem

The map currently has a single basemap: OSM's "Standard" raster tiles from
`tile.openstreetmap.org`, styled by OSM Carto. That's a fine default but
for a habitat map people often want:

- **Satellite imagery** to see where the green "suitable" layer overlaps
  with actual forest canopy vs. ag / urban / bare ground.
- **Terrain / topo** to see how suitability tracks ridgelines, coastal
  valleys, and aspect — which is the whole ecological story for fog.

Neither is available from the OSM Standard tile server. OSM doesn't serve
aerial imagery at all; topo exists as a community style (OpenTopoMap) but
on a separate server.

## Proposed UX

Leaflet supports this natively: pass a `baseLayers` dict (radio buttons) to
the existing `L.control.layers(baseLayers, overlays)` call. We already have
an overlays panel in the top-left; base-layer radios render in the same
control, above the overlay checkboxes.

Default: **OSM Standard** (current behavior).
Offer: **Satellite**, **Terrain**, possibly **OSM Standard**.

## Tile source options (no API key required)

| Source | Style | URL template | Notes |
|---|---|---|---|
| OSM Standard (current) | Streets / carto | `https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png` | Baseline. |
| Esri World Imagery | Satellite | `https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}` | No key, widely used in Leaflet ecosystem, decent global resolution. Note `{y}/{x}` order. |
| Esri World Topo | Terrain + streets | `https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}` | No key. Blends shaded relief with labels. |
| OpenTopoMap | Pure topo (contours + hillshade) | `https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png` | No key; slower, please-be-polite usage guidelines. |

Options that would require an API key (keep in mind if we want nicer imagery
or styling later): Mapbox, MapTiler, Stadia/Stamen (as of 2023), Thunderforest.
Skipping for now to keep the static-site deploy key-free.

## Attribution

Each tile source needs its own attribution string passed to `L.tileLayer`.
Leaflet's layer control switches the attribution automatically when the base
layer changes, so just set it correctly per layer:

- Esri: `Tiles © Esri — Source: Esri, Maxar, Earthstar Geographics, and the GIS User Community`
- OpenTopoMap: `Map data: © OpenStreetMap contributors, SRTM | Map style: © OpenTopoMap (CC-BY-SA)`

## Sketch

In `web/index.html`, replace the single `basemap` var with a dict and wire
it into the existing layer control:

```js
const baseLayers = {
    'Streets (OSM)': L.tileLayer('https://{s}.tile.openstreetmap.org/...', { attribution: '...' }),
    'Satellite (Esri)': L.tileLayer('https://server.arcgisonline.com/.../World_Imagery/.../{z}/{y}/{x}', { attribution: '...' }),
    'Terrain (Esri)': L.tileLayer('https://server.arcgisonline.com/.../World_Topo_Map/.../{z}/{y}/{x}', { attribution: '...' })
};
baseLayers['Streets (OSM)'].addTo(map);  // default

L.control.layers(baseLayers, overlays, { position: 'topleft', collapsed: window.innerWidth <= 768 }).addTo(map);
```

May want to bump the suitability overlay opacity down a bit over satellite
(currently `0.7`) — green-on-green can wash out forested areas. Better yet,
swap the overlay **color** when the satellite basemap is active: something
like magenta, bright yellow, or orange that pops off green canopy instead
of blending into it. Our overlay is a pre-rendered PNG tile pyramid, so
options are:

1. Generate a second tile set in the alternate color (cleanest, doubles
   tile count — matters for the Pages 20k cap, see ticket #24).
2. Apply a CSS `filter: hue-rotate()` on the tile layer element when the
   satellite basemap is active (zero extra tiles, but hue-rotate is coarse
   and may not land on the exact color we want).
3. Render client-side from a single-channel raster with a JS-controlled
   colormap — biggest rewrite; only worth it if we end up wanting several
   dynamic styles.

Start with option 2 as a quick experiment; fall back to option 1 if the
hue-rotate result looks off.

## Out of scope

- Paid / API-keyed providers (Mapbox, MapTiler).
- Custom styling or hillshade we generate ourselves from a DEM.
- Remembering the user's basemap choice across sessions (localStorage).
