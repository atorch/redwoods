# CLAUDE.md

Developer/Claude Code reference. For project overview and methodology, see `README.md`.

## Running scripts

Scripts are managed by `uv` — it resolves dependencies per-run from `pyproject.toml`:

```bash
uv run python scripts/<script_name>.py
```

Scripts are numbered roughly in pipeline order (`01_` … `16_`). `13_generate_web_tiles.py` is the current tile generator; earlier `03_*`/`05-10_*` variants are superseded experiments left in place for reference.

## Viewing the map locally

Tiles now live under `web/tiles/`, so the viewer uses the relative path `./tiles/redwood_suitability/{z}/{x}/{y}.png`. Serve `web/` directly:

```bash
cd web
python3 -m http.server 8000
# Open http://localhost:8000/
```

## Regenerating tiles

```bash
uv run python scripts/13_generate_web_tiles.py
```

Tiles land in `web/tiles/redwood_suitability/` (git-ignored). Only a bootstrap subset (the 24 zoom-8 tiles) is hosted in production today — see the tile allowlist (`AVAILABLE_TILES`) in `web/index.html`.

## Deployment

- `web/` is uploaded as static content to **Cloudflare Pages** — the whole directory (HTML + tiles) ships as one unit. Don't put anything in here that shouldn't be public.
- **Bootstrap tile hosting**: we ship only the 24 zoom-8 tiles so we stay well under Pages' 20k-file limit. `web/index.html` uses `maxNativeZoom: 8` to stretch them at higher zooms and an allowlist that returns a transparent PNG for any tile coord we haven't shipped (avoiding 404s).
- **Future scale-up**: once we want to ship higher zoom levels (z=9+ adds ~30k more tiles), we'll exceed the Pages file cap and move tiles to **Cloudflare R2**. See `tickets/24_deploy_tiles_cloudflare_r2.md` (deferred) and `tickets/26_automate_cloudflare_deploy.md` (scripted deploy skeleton).

## Key paths

- `scripts/` — processing pipeline
- `data/` — PRISM and GOES-18 inputs (ignored; regenerate via download scripts)
- `outputs/` — derived rasters (`study_area_redwood_suitable.tif` is the final layer)
- `web/tiles/` — generated PNG tile pyramid (ignored); shipped to Cloudflare Pages
- `tickets/` — design docs and task notes
- `web/` — static site deployed to Cloudflare Pages (HTML + tiles)
