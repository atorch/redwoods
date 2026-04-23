# Automate Cloudflare Pages Deploy

> **Status:** TODO — skeleton. Capturing the intent so future sessions don't re-derive it.

## Objective

Replace the manual "zip `web/` and drop it into the Cloudflare dashboard" workflow with a one-command deploy script. Goal: `./scripts/deploy.sh` (or `uv run python scripts/deploy.py`) publishes the current contents of `web/` to redwoods.earth.

## Why now-ish

Right now prod is updated by hand: regenerate tiles → manually upload `web/` via the Cloudflare UI. That's tolerable while we ship one tile set, but becomes the bottleneck as soon as we iterate on:

- the tile allowlist / new zoom levels
- `index.html` copy, legend, ground-truth points
- any future layer toggles

A one-command deploy keeps "make a change → see it on redwoods.earth" short enough that we actually do it.

## Approach (first cut)

**Tool: `wrangler`** (Cloudflare's official CLI).

- `wrangler pages deploy ./web --project-name=redwoods-earth`
- Authenticates once via `wrangler login`; after that, non-interactive.
- Outputs the deployed URL; the Pages project is already wired to the redwoods.earth domain, so a successful deploy updates prod.

Script should:

1. Sanity-check `web/tiles/` is populated (fail fast if someone forgot to regenerate).
2. Print the tile count so we notice if we accidentally ship 31k tiles (Pages cap is 20k).
3. Invoke `wrangler pages deploy web --project-name=redwoods-earth`.
4. Print the preview URL and the production URL.

## Open questions

- Do we want a dry-run / preview-only mode? (`wrangler pages deploy --branch=preview` creates a preview deploy instead of updating prod.)
- Should tile regeneration be part of the deploy script, or stay a separate step? (Lean: separate — regeneration is slow and usually not needed.)
- Authentication: `wrangler login` is interactive. For CI, we'd swap to a `CLOUDFLARE_API_TOKEN` env var. Not needed until we automate from GitHub Actions.

## When the R2 plan (ticket #24) lands

Deploy becomes two steps:

1. `wrangler pages deploy web` — HTML only.
2. `rclone sync web/tiles/ cloudflare-r2:redwoods-tiles/` — tiles to R2.

Worth combining both into the same `deploy.sh` at that point.

## Related

- `tickets/23_production_hosting_domain_setup.md` — Pages project + domain already configured.
- `tickets/24_deploy_tiles_cloudflare_r2.md` — future R2 path once tile count exceeds Pages cap.
