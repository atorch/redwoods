# Deploy Tiles to Cloudflare R2 for Production

## Objective

Upload the 31,069 redwood suitability tiles to Cloudflare R2 object storage and update the production site at redwoods.earth to load tiles from R2, completing the full production deployment.

## Current Status

**What's working:**
- ✓ Domain purchased: redwoods.earth ($19.98/year via Namecheap)
- ✓ DNS configured: Nameservers pointing to Cloudflare
- ✓ Cloudflare Pages deployed: HTML/JS hosted at redwoods.earth
- ✓ Map loads with OpenStreetMap basemap and ground truth markers

**What's missing:**
- ✗ Green suitability overlay (tiles not deployed)
- ✗ Tiles are local only (`tiles/redwood_suitability/`)
- ✗ Browser shows 404 errors for tile requests

**Why R2?**
- Cloudflare Pages has a 20,000 file limit per deployment
- We have 31,069 tiles (exceeds limit)
- R2 (object storage) has no file count limits
- R2 free tier: 10 GB storage (we only use 12 MB)
- R2 integrates with Pages CDN for fast global delivery

## Background: Why Not Other Options?

### Why Not Upload Tiles to Pages?
- ✗ File count limit: 20,000 files (we have 31,069)
- Would require reducing zoom levels (8-12 instead of 8-14)
- Loss of detail at higher zoom levels

### Why Not GitHub Pages?
- ✓ GitHub Pages has no file count limit under 1 GB (our tiles are 12 MB)
- ✓ Simpler deployment (just push to repo)
- ✗ Slower CDN than Cloudflare globally
- ✗ Already using Cloudflare Pages for HTML
- ℹ️ This is a viable alternative if R2 proves problematic

### Why Not AWS S3?
- ✓ Industry standard, excellent CDN with CloudFront
- ✗ More complex setup (IAM policies, bucket policies, CORS)
- ✗ Costs ~$0.50-2/month (vs R2 free)
- ✗ Not integrated with Cloudflare dashboard

**Decision:** Use Cloudflare R2 for simplicity and cost (free).

## Implementation Steps

### Phase 1: Create R2 Bucket

1. **Log in to Cloudflare dashboard**
   - [ ] Go to https://dash.cloudflare.com/

2. **Navigate to R2 section**
   - [ ] In left sidebar, find "R2" under "Storage"
   - [ ] Click "R2"

3. **Create bucket**
   - [ ] Click "Create bucket"
   - [ ] **Bucket name:** `redwoods-tiles` (or `redwood-suitability-tiles`)
   - [ ] **Location:** Automatic (Cloudflare chooses optimal location)
   - [ ] Click "Create bucket"

4. **Enable public access**
   - [ ] In bucket settings, find "Public access" or "R2.dev subdomain"
   - [ ] Click "Allow Access" or "Enable public URL"
   - [ ] **Important:** Note the public R2 URL (looks like `https://pub-xxxxxxxxxxxxx.r2.dev`)
   - [ ] Save this URL - you'll need it in Phase 3

**Expected outcome:** Bucket created with public URL like `https://pub-abc123def456.r2.dev`

### Phase 2: Upload Tiles to R2

**Challenge:** 31,069 files is too many to upload via web UI.

**Recommended approach:** Use `rclone` (command-line tool for cloud storage)

#### Option A: Upload with rclone (Recommended)

1. **Install rclone**
   ```bash
   # On Ubuntu/Debian
   sudo apt install rclone

   # Or download from: https://rclone.org/downloads/
   ```

2. **Configure rclone for Cloudflare R2**
   - [ ] Run: `rclone config`
   - [ ] Choose: `n` (new remote)
   - [ ] Name: `cloudflare-r2`
   - [ ] Storage type: Choose number for "Amazon S3 Compliant Storage Providers including Cloudflare R2"
   - [ ] Provider: Choose "Cloudflare R2"
   - [ ] Access Key ID: Get from Cloudflare R2 settings → "Manage R2 API Tokens"
   - [ ] Secret Access Key: From same place
   - [ ] Endpoint: `https://<account_id>.r2.cloudflarestorage.com`
     - Find your account ID in Cloudflare dashboard (right sidebar)
   - [ ] Leave other settings as default
   - [ ] Confirm and save

3. **Upload tiles**
   ```bash
   cd /home/adrian/redwoods

   # Upload entire tiles directory to R2 bucket
   rclone copy tiles/redwood_suitability/ cloudflare-r2:redwoods-tiles/redwood_suitability/ \
     --progress \
     --transfers 16
   ```

   **Expected time:** 5-20 minutes depending on upload speed

4. **Verify upload**
   ```bash
   # List files in R2 bucket
   rclone ls cloudflare-r2:redwoods-tiles/redwood_suitability/ | wc -l
   # Should output: 31069
   ```

5. **Test a tile URL in browser**
   - [ ] Get your public R2 URL (from Phase 1)
   - [ ] Test URL: `https://pub-xxxxx.r2.dev/redwood_suitability/9/81/197.png`
   - [ ] Should show a green/transparent tile PNG image
   - [ ] If 404 or access denied, check public access settings

#### Option B: Upload via Cloudflare Dashboard (For Small Subsets)

**NOT recommended for 31K files** - web UI will be too slow.

Only use this if you want to test with a small subset (e.g., zoom level 9 only = ~300 tiles):

1. **In R2 bucket, click "Upload"**
2. **Select files** - can upload multiple at once
3. **Preserve directory structure:** `redwood_suitability/9/81/197.png`
4. **Click "Upload"**

**Limitation:** Very time-consuming for thousands of files.

#### Option C: Upload via AWS CLI (Alternative)

R2 is S3-compatible, so AWS CLI works:

```bash
# Install AWS CLI
sudo apt install awscli

# Configure for R2
aws configure --profile r2
# Access Key: From Cloudflare R2 API tokens
# Secret Key: From Cloudflare R2 API tokens
# Region: auto
# Output: json

# Upload
aws s3 sync tiles/redwood_suitability/ \
  s3://redwoods-tiles/redwood_suitability/ \
  --endpoint-url https://<account_id>.r2.cloudflarestorage.com \
  --profile r2
```

**Recommendation:** Use rclone (Option A) - it's designed for this and has better progress reporting.

### Phase 3: Update Web Code to Use R2 Tiles

1. **Edit `web/index.html` locally**
   - [ ] Open: `/home/adrian/redwoods/web/index.html`
   - [ ] Find the tile layer code (around line 209):
     ```javascript
     const suitabilityLayer = L.tileLayer('../tiles/redwood_suitability/{z}/{x}/{y}.png', {
     ```

   - [ ] Replace with your R2 URL:
     ```javascript
     const suitabilityLayer = L.tileLayer('https://pub-xxxxx.r2.dev/redwood_suitability/{z}/{x}/{y}.png', {
     ```

   - [ ] Replace `pub-xxxxx.r2.dev` with your actual R2 public URL from Phase 1
   - [ ] Save the file

2. **Test locally first**
   - [ ] Open http://localhost:8000/web/ in browser
   - [ ] Verify tiles load from R2 (check browser Network tab)
   - [ ] Green overlay should appear
   - [ ] No 404 errors in console

3. **Deploy updated HTML to Cloudflare Pages**
   - [ ] Go to Cloudflare dashboard → Workers & Pages
   - [ ] Click on your `redwoods-earth` project
   - [ ] Go to "Deployments" tab
   - [ ] Click "Create deployment" or "Upload new version"
   - [ ] Upload the updated `index.html` file
   - [ ] Wait 1-2 minutes for deployment

4. **Test production site**
   - [ ] Visit https://redwoods.earth
   - [ ] **Hard refresh** (Ctrl+Shift+R or Cmd+Shift+R) to clear cache
   - [ ] Verify green suitability overlay appears
   - [ ] Check browser console - no 404 errors for tiles
   - [ ] Test on mobile device

### Phase 4: Verification & Testing

- [ ] **Desktop testing:**
  - Open https://redwoods.earth in Chrome
  - Open browser DevTools (F12) → Network tab
  - Filter by "PNG" to see tile requests
  - Verify tiles load from `pub-xxxxx.r2.dev` domain
  - Check status codes: all should be 200 OK
  - Pan and zoom - tiles should load smoothly

- [ ] **Mobile testing:**
  - Open https://redwoods.earth on phone
  - Green overlay should appear
  - Pan and zoom work smoothly
  - No obvious performance issues

- [ ] **Performance testing:**
  - Measure tile load time (should be <500ms per tile)
  - Check total page load time (<3 seconds)
  - Verify tiles are cached (second visit is faster)

- [ ] **Ground truth validation:**
  - All 8 ground truth points should be in green zones
  - Same validation as local testing

- [ ] **Cross-browser testing:**
  - Test in Firefox, Safari, Edge
  - Verify tiles load in all browsers

## Outputs

### Files Modified
```
web/index.html (UPDATED)
  - Tile URL changed from relative path to R2 absolute URL
  - Line ~209: Updated L.tileLayer() URL parameter
```

### Infrastructure Created
```
Cloudflare R2:
  └── redwoods-tiles/ (bucket)
      └── redwood_suitability/
          ├── 8/ (31,069 PNG tiles total)
          ├── 9/
          ├── 10/
          ├── 11/
          ├── 12/
          ├── 13/
          └── 14/
```

### Git Considerations

**Commit the updated `web/index.html`:**
- ✓ HTML file with R2 URL should be committed
- ✓ Document the R2 URL in commit message or README
- ✗ Don't commit R2 API tokens to git
- ✗ `tiles/` directory still in `.gitignore` (no need to commit local tiles)

## Success Criteria

1. ✓ R2 bucket created and public URL obtained
2. ✓ All 31,069 tiles uploaded to R2 (verified with `rclone ls` or file count)
3. ✓ Test tile URL works in browser (shows PNG image)
4. ✓ `web/index.html` updated with R2 URL
5. ✓ Production site at https://redwoods.earth shows green overlay
6. ✓ No 404 errors in browser console
7. ✓ Tiles load quickly (<1 second per tile)
8. ✓ All 8 ground truth points in green zones
9. ✓ Works on mobile and desktop browsers

## Cost

**R2 Storage:**
- Storage: 12 MB (well under 10 GB free tier)
- Bandwidth: Class A operations (uploads) - one-time during deployment
- Bandwidth: Class B operations (downloads/requests) - 1M free/month
- **Total cost:** $0/month (free tier covers usage)

**Estimated monthly tile requests:**
- If 100 visitors/day × 50 tiles/visit = 5,000 tiles/day = 150,000/month
- Well under 1M free tier
- Even at 1,000 visitors/day, still under free tier

## Timeline Estimate

- **rclone setup:** 15 minutes (first time only)
- **Tile upload:** 10-30 minutes (depending on internet speed)
- **Update HTML + deploy:** 10 minutes
- **Testing:** 15 minutes
- **Total:** ~1-1.5 hours

## Risks & Mitigations

### Risk 1: R2 Upload Fails or Times Out
- **Issue:** 31K files, upload may fail partway through
- **Mitigation:**
  - rclone has automatic retry logic
  - Can resume interrupted uploads
  - If fails repeatedly, use `rclone sync` instead of `copy` (sync skips already-uploaded files)

### Risk 2: CORS Issues (Cross-Origin Resource Sharing)
- **Issue:** Browser blocks tile requests from different domain (r2.dev vs redwoods.earth)
- **Likelihood:** Medium - R2 might need CORS configuration
- **Mitigation:**
  - In R2 bucket settings, add CORS policy:
    ```json
    {
      "AllowedOrigins": ["https://redwoods.earth", "https://www.redwoods.earth"],
      "AllowedMethods": ["GET"],
      "AllowedHeaders": ["*"]
    }
    ```
  - Or use a custom domain for R2 (advanced)

### Risk 3: R2 Public URL Not Working
- **Issue:** Tiles return 403 Forbidden or 404
- **Likelihood:** Medium if public access not enabled correctly
- **Mitigation:**
  - Verify "Public access" or "R2.dev subdomain" is enabled in bucket settings
  - Test a tile URL directly in browser before updating HTML
  - Check R2 bucket permissions

### Risk 4: Tile Paths Don't Match
- **Issue:** Uploaded tiles at different path than expected
- **Example:** Uploaded to `/tiles/...` instead of `/redwood_suitability/...`
- **Mitigation:**
  - Test one tile URL before uploading all 31K
  - Verify directory structure matches: `bucket/redwood_suitability/9/81/197.png`
  - Use `rclone tree` to preview structure before upload

## Alternative: GitHub Pages (If R2 Problematic)

If Cloudflare R2 proves too complex or has issues, fall back to GitHub Pages:

1. **Create GitHub repo:**
   - Push entire project including `tiles/` directory
   - 12 MB is well under 1 GB repo limit

2. **Enable GitHub Pages:**
   - Settings → Pages → Deploy from branch
   - Branch: main, folder: `/` (root)

3. **Update Namecheap DNS:**
   - Point `redwoods.earth` to GitHub Pages IPs (see Ticket #23)

4. **Tiles load from GitHub:**
   - No R2 needed, tiles served from GitHub CDN
   - Slightly slower than Cloudflare R2 globally, but still fast

**Trade-offs:**
- ✓ Simpler (no R2 setup)
- ✓ All code + tiles in one place (easier to manage)
- ✗ Slower CDN (GitHub vs Cloudflare)
- ✗ Tiles committed to git (larger repo, but manageable at 12 MB)

## Documentation Updates

- [ ] Document R2 URL in `CLAUDE.md`
- [ ] Document R2 bucket name and public URL
- [ ] Add instructions for regenerating/uploading tiles if data updates
- [ ] Update main README with production URL and tile hosting details

## Related Tickets

- **Ticket #21:** Production web tiles (tile generation - COMPLETED)
- **Ticket #23:** Production hosting and domain setup (Pages deployment - COMPLETED)
- **Ticket #25:** Mobile UX improvements (dismissible info panel - PENDING)

## Notes

- This ticket completes the production deployment
- After this, https://redwoods.earth will be fully functional
- Future tile updates: regenerate locally, then re-upload to R2 with `rclone sync`
- Consider adding cache headers for tiles (R2 should handle this automatically)
