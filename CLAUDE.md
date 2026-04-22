# CLAUDE.md

Developer/Claude Code reference. For project overview and methodology, see `README.md`.

## Running scripts

Scripts are managed by `uv` — it resolves dependencies per-run from `pyproject.toml`:

```bash
uv run python scripts/<script_name>.py
```

Scripts are numbered roughly in pipeline order (`01_` … `16_`). `13_generate_web_tiles.py` is the current tile generator; earlier `03_*`/`05-10_*` variants are superseded experiments left in place for reference.

## Viewing the map locally

The local viewer expects tiles at `../tiles/redwood_suitability/{z}/{x}/{y}.png` relative to `web/index.html`, so the HTTP server's root **must be the project root**, not `web/`:

```bash
# From project root
python3 -m http.server 8000
# Open http://localhost:8000/web/   ← note the /web/ path
```

Starting the server inside `web/` will 404 every tile.

## Regenerating tiles

```bash
uv run python scripts/13_generate_web_tiles.py
```

Tiles land in `tiles/redwood_suitability/` (git-ignored). Production copies live in Cloudflare R2.

## Deployment

- `web/` is uploaded as static content to **Cloudflare Pages** (the whole directory ships — don't put anything in here that shouldn't be public).
- Tiles are served from **Cloudflare R2** (`tiles/` is too large for Pages' 20k-file limit).
- For production, `web/index.html`'s tile URL must point at the R2 public URL instead of the `../tiles/…` relative path used locally. See `tickets/24_deploy_tiles_cloudflare_r2.md`.

## Key paths

- `scripts/` — processing pipeline
- `data/` — PRISM and GOES-16 inputs (ignored; regenerate via download scripts)
- `outputs/` — derived rasters (`bay_area_redwood_suitable.tif` is the final layer)
- `tiles/` — generated PNG tile pyramid (ignored)
- `tickets/` — design docs and task notes
- `web/` — static site deployed to Cloudflare Pages
