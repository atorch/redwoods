# Production Hosting & Domain Setup

## Objective

Purchase a domain name (e.g., redwoods.earth) and set up production hosting to make the redwood habitat map publicly accessible on the internet.

## Background: How Domains and Hosting Work

**For someone who's never done this before, here's the complete picture:**

### What is a Domain Name?

A **domain name** is the human-readable address people type in their browser (like `redwoods.earth`). Behind the scenes, computers use IP addresses (like `172.67.154.23`) to find websites, but domains make things memorable.

**Key concepts:**
- **Top-Level Domain (TLD)**: The ending part (`.earth`, `.com`, `.org`)
- **Registrar**: Company you pay to "rent" your domain (you never truly own it, you lease it yearly)
- **DNS (Domain Name System)**: The phonebook of the internet that translates `redwoods.earth` → IP address

**Think of it like renting an apartment:**
- The **domain** is your mailing address (123 Main St)
- The **registrar** is the landlord who rents you the address
- **DNS** is the postal service that knows how to route mail to your address
- **Hosting** is the actual apartment building where your stuff lives

### What is Hosting?

**Hosting** is where your actual website files live - the HTML, images, tiles, etc. Someone's server (computer) needs to be running 24/7 to serve your files when people visit your domain.

**Hosting options for this project:**
1. **Static hosting** (our case): Just serve files, no server-side code
2. **Dynamic hosting**: Runs code on the server (not needed for us)

### How They Connect

```
User types "redwoods.earth"
    ↓
DNS lookup: "What IP address is redwoods.earth?"
    ↓
DNS responds: "172.67.154.23" (Cloudflare's server)
    ↓
Browser contacts that server
    ↓
Server sends back your HTML, tiles, images
    ↓
User sees the map!
```

**YOU control the connection by configuring DNS records** - you tell the DNS system "redwoods.earth points to [hosting provider's IP]"

## Recommended Approach for This Project

### Domain: redwoods.earth via Namecheap

**Why .earth?**
- ✓ Environmental focus (perfect for redwood conservation project)
- ✓ Memorable and mission-aligned
- ✓ Less competitive than .com (more likely available)
- ✓ **Available at $19.98/year** (as of 2026-04-19)

**Why NOT Cloudflare Registrar?**
- ✗ Cloudflare does not yet support the .earth TLD extension
- ✗ Error: "redwoods.earth cannot be registered as Cloudflare does not yet support the '.earth' extension"
- ℹ️ You can still use Cloudflare for DNS/hosting (just not domain registration)

**Why Namecheap?**
- ✓ **Best price:** $19.98/year (vs $40/year at Squarespace)
- ✓ Supports .earth TLD
- ✓ Free WHOIS privacy (hides your personal info from public database)
- ✓ Established registrar since 2000
- ✓ Easy to point nameservers to Cloudflare for DNS/hosting
- ✓ Auto-renewal available (don't lose your domain)

**Alternative: Squarespace Domains**
- ✓ Cleaner interface, better support
- ✓ Free WHOIS privacy, email forwarding
- ✗ **Double the price:** $40/year
- ℹ️ Only worth it if you strongly prefer simpler UI/better support

**Alternatives if redwoods.earth is taken:**
- `redwood-habitat.earth`
- `coast-redwoods.earth`
- `redwoods.map`
- `redwood.eco` (.eco is another environmental TLD)

### Hosting: Cloudflare Pages + R2 (Recommended)

**Architecture:**
- **Cloudflare Pages** (free): Host `web/index.html` and JavaScript
- **Cloudflare R2** (free tier 10GB): Host your 31K tiles (12 MB)

**Why this split approach?**
- Cloudflare Pages has a **20,000 file limit per deployment**
- You have 31,069 tiles (exceeds limit)
- Cloudflare R2 (object storage) has **no file count limits**
- R2 free tier: 10 GB storage, 1M class A ops/month (more than enough)
- Both on Cloudflare = same CDN, automatic integration

**How it works:**
1. Upload `web/index.html` to Cloudflare Pages
2. Upload `tiles/` directory to Cloudflare R2 bucket
3. Update map code to load tiles from R2 URL
4. When someone visits `redwoods.earth`:
   - HTML/JS loads from Pages (fast, global CDN)
   - Tiles load from R2 (fast, global CDN)
5. No server to maintain - Cloudflare handles everything

**Alternative hosting options:**

**Option A: GitHub Pages (Simplest)**
- **Pros:** Extremely simple, free, no account complexity
- **Cons:** 1 GB repository limit (you only have 12 MB, so fine!), slower CDN
- **File limit:** No explicit file count limit for repos <1GB
- **Cost:** Free
- **Best if:** You want the absolute simplest deployment

**Option B: Netlify**
- **Pros:** Similar to Cloudflare Pages, good CDN
- **Cons:** 100K file limit (exceeds 31K, but much higher than Cloudflare)
- **Cost:** Free tier available
- **Best if:** Cloudflare doesn't work out

**Option C: AWS S3 + CloudFront**
- **Pros:** Industry standard, unlimited files, excellent CDN
- **Cons:** More complex setup, costs ~$0.50-2/month
- **Best if:** You're comfortable with AWS

## Step-by-Step Implementation

### Phase 1: Check Domain Availability

**Status: ✓ CONFIRMED AVAILABLE**

- [x] Checked at Namecheap: `redwoods.earth` is available at $19.98/year
- [x] Checked at Cloudflare: Not supported (.earth TLD not available)
- [x] Checked at Squarespace: Available at $40/year

**Recommendation:** Purchase at Namecheap for $19.98/year

**If redwoods.earth becomes unavailable, try alternatives:**
- `redwood-habitat.earth`
- `coast-redwoods.earth`
- `redwoods.map`
- `redwood.eco` (.eco is another environmental TLD)

### Phase 2: Purchase Domain at Namecheap

**Prerequisites:**
- [ ] Create Namecheap account (free, just email + password)
- [ ] Add payment method (credit card or PayPal)

**Purchase process:**
- [ ] Go to: https://www.namecheap.com/domains/registration/results/?domain=redwoods.earth
- [ ] Add `redwoods.earth` to cart ($19.98/year)
- [ ] **At checkout, UNCHECK upsells you don't need:**
  - ✗ SSL certificate (Cloudflare/GitHub Pages provides free SSL)
  - ✗ Email hosting (unless you want hello@redwoods.earth email)
  - ✗ Premium DNS (you'll use Cloudflare DNS instead)
- [ ] **At checkout, VERIFY these are ENABLED:**
  - ✓ **WhoisGuard** (free WHOIS privacy - should be included)
  - ✓ **Auto-renewal** (so you don't lose your domain)
- [ ] **Prepayment decision:**
  - Option A: Pay for 1 year ($19.98) with auto-renewal ← **Recommended**
  - Option B: Prepay for multiple years (e.g., 3 years = $59.94)
  - **Recommendation:** Just pay for 1 year with auto-renewal enabled
    - Renewal price is likely the same ($19.98/year)
    - More flexibility if you want to transfer registrars later
    - Auto-renewal protects you from forgetting
    - Only prepay if you're worried about price increases
- [ ] Complete purchase
- [ ] Verify contact email (ICANN requirement - Namecheap will send confirmation)

**What you're buying:**
- 1 year lease on the domain name (renewable annually)
- Automatic renewal each year (cancel anytime)
- Free WHOIS privacy included (WhoisGuard)
- DNS management at Namecheap (but you'll likely switch to Cloudflare)

**Important:**
- Domains can't be transferred to another registrar for **60 days after purchase** (ICANN rule)
- Save your Namecheap login credentials somewhere safe
- You'll need to log in to Namecheap to:
  - Update nameservers (pointing to Cloudflare or GitHub)
  - Manage auto-renewal settings
  - Transfer domain later (if desired)

### Phase 3: Set Up Cloudflare Hosting

**Prerequisites:**
- [ ] Cloudflare account (same as above)
- [ ] Your website files ready (`web/` folder + `tiles/`)

**Setup process:**

1. **Create R2 bucket for tiles:**
   - [ ] Log in to Cloudflare dashboard
   - [ ] Go to "R2" section
   - [ ] Click "Create bucket"
   - [ ] Name it `redwoods-tiles` or similar
   - [ ] Enable public access for the bucket

2. **Upload tiles to R2:**
   - [ ] Upload your entire `tiles/redwood_suitability/` directory structure
   - [ ] Use Cloudflare web UI or `rclone` for bulk upload
   - [ ] Get the public R2 bucket URL (looks like: `https://pub-xxxxx.r2.dev/`)
   - [ ] Test a tile URL: `https://pub-xxxxx.r2.dev/redwood_suitability/9/81/197.png`

3. **Create Pages project for web interface:**
   - [ ] Go to "Pages" section in Cloudflare dashboard
   - [ ] Click "Create a project"
   - [ ] Choose "Direct Upload" (manual file upload)
   - [ ] Name it `redwoods-map` or similar

4. **Update web code to use R2 tiles:**
   - [ ] Edit `web/index.html`
   - [ ] Change tile URL from:
     ```javascript
     '../tiles/redwood_suitability/{z}/{x}/{y}.png'
     ```
   - [ ] To R2 URL:
     ```javascript
     'https://pub-xxxxx.r2.dev/redwood_suitability/{z}/{x}/{y}.png'
     ```

5. **Upload web files to Pages:**
   - [ ] Upload `web/` directory to Cloudflare Pages
   - [ ] Wait for deployment (usually 1-2 minutes)
   - [ ] Test at auto-generated URL (like `redwoods-map.pages.dev`)

**Alternative: GitHub Pages (Simpler, No File Limit Issue)**

If Cloudflare R2 seems too complex, GitHub Pages is simpler:

1. **Create public GitHub repo:**
   - [ ] Push your project to GitHub (include `tiles/` directory)
   - [ ] Note: 12 MB of tiles is well under 1 GB repo limit

2. **Enable GitHub Pages:**
   - [ ] In repo settings → Pages
   - [ ] Source: Deploy from branch
   - [ ] Branch: `main`, folder: `/` (root)
   - [ ] Wait 2-5 minutes for deployment

3. **Test at GitHub Pages URL:**
   - [ ] Visit `https://yourusername.github.io/redwoods/web/`
   - [ ] Verify tiles load correctly

**Recommended for first-timers:** Start with GitHub Pages (much simpler), then migrate to Cloudflare + R2 later if you need faster global CDN performance.

### Phase 4: Connect Domain to Hosting

**If using Cloudflare Pages:**

1. **Point Namecheap domain to Cloudflare:**
   - [ ] Create free Cloudflare account (cloudflare.com)
   - [ ] In Cloudflare, click "Add a site" and enter `redwoods.earth`
   - [ ] Cloudflare will scan your DNS and give you nameservers (like `ns1.cloudflare.com`)
   - [ ] In Namecheap dashboard, go to Domain List → Manage → Nameservers
   - [ ] Change from "Namecheap BasicDNS" to "Custom DNS"
   - [ ] Enter Cloudflare's nameservers (they'll provide 2 nameservers)
   - [ ] Save changes (DNS propagation takes 5 min - 48 hours, usually <30 min)

2. **Add custom domain to Cloudflare Pages:**
   - [ ] In Cloudflare Pages project settings
   - [ ] Click "Custom domains"
   - [ ] Add `redwoods.earth`
   - [ ] Cloudflare will auto-configure DNS records

3. **Verify DNS records:**
   - [ ] Check DNS tab in Cloudflare dashboard
   - [ ] Verify `A` record: `redwoods.earth` → Cloudflare Pages IP
   - [ ] Verify `AAAA` record (IPv6 version)
   - [ ] Verify `CNAME` for `www.redwoods.earth` → `redwoods.earth`

4. **Enable HTTPS:**
   - [ ] In SSL/TLS tab, ensure "Full" or "Full (strict)" mode
   - [ ] Wait 10-30 minutes for SSL certificate to activate
   - [ ] Verify padlock icon appears in browser at `https://redwoods.earth`

**If using GitHub Pages:**

1. **Add custom domain to GitHub:**
   - [ ] In repo settings → Pages → Custom domain
   - [ ] Enter `redwoods.earth`
   - [ ] Wait for DNS check (GitHub will verify you own the domain)

2. **Configure DNS at Namecheap:**
   - [ ] Log in to Namecheap
   - [ ] Go to Domain List → Manage → Advanced DNS
   - [ ] Add `A` records pointing to GitHub's IPs:
     - `185.199.108.153`
     - `185.199.109.153`
     - `185.199.110.153`
     - `185.199.111.153`
   - [ ] Add `CNAME` record: `www` → `yourusername.github.io`
   - [ ] Save changes (DNS propagation takes 5 min - 48 hours)

3. **Enable HTTPS on GitHub:**
   - [ ] In GitHub Pages settings, check "Enforce HTTPS"
   - [ ] Wait 10-30 minutes for certificate to activate

**Alternative: Use Cloudflare DNS (even with GitHub Pages)**
- [ ] Point Namecheap nameservers to Cloudflare (see above)
- [ ] Configure DNS in Cloudflare dashboard instead of Namecheap
- [ ] Benefit: Faster DNS, better DDoS protection, free CDN
- [ ] Still host on GitHub Pages, just use Cloudflare for DNS

**What happens during DNS propagation:**
- Changes take **5 minutes to 48 hours** to spread worldwide
- Usually works in 10-30 minutes for most users
- Can check with: `dig redwoods.earth` or online tool (whatsmydns.net)

### Phase 5: Testing & Verification

- [ ] Visit `https://redwoods.earth` - should show your map
- [ ] Test `https://www.redwoods.earth` - should redirect to non-www
- [ ] Verify HTTPS (padlock icon in address bar)
- [ ] Test tile loading - open browser dev tools, check Network tab
- [ ] Test on mobile device
- [ ] Check different geographic locations (use VPN or ask friend)
- [ ] Verify all ground truth points render correctly
- [ ] Test pan/zoom performance

**Troubleshooting:**
- If domain doesn't work: Check DNS records, wait 30 min
- If HTTPS error: Wait for SSL cert to activate (can take 30 min)
- If tiles don't load: Check CORS headers, verify tile paths
- If slow: Check Cloudflare caching is enabled

## Alternative Workflow: GitHub Pages + Custom Domain

**If you prefer a simpler approach (no Cloudflare hosting):**

1. **Host on GitHub Pages:**
   - [ ] Push code to public GitHub repo
   - [ ] Enable GitHub Pages in repo settings
   - [ ] Select branch and `/web` folder
   - [ ] Get URL like `username.github.io/redwoods`

2. **Buy domain separately:**
   - [ ] Purchase `redwoods.earth` from Namecheap or Cloudflare
   - [ ] In GitHub repo settings, add custom domain
   - [ ] In domain registrar DNS settings, add:
     - `A` records pointing to GitHub's IPs:
       - `185.199.108.153`
       - `185.199.109.153`
       - `185.199.110.153`
       - `185.199.111.153`
     - `CNAME` record: `www` → `username.github.io`

3. **Enable HTTPS:**
   - [ ] In GitHub Pages settings, check "Enforce HTTPS"
   - [ ] Wait 10-30 min for certificate

**Trade-offs vs Cloudflare Pages:**
- ✓ Simpler deployment (just `git push`)
- ✗ Slower global CDN (GitHub CDN not as fast as Cloudflare)
- ✗ Still need to buy domain separately (not integrated)
- ✓ More familiar if you use GitHub already

## Cost Summary

### Option 1: Cloudflare Pages + R2 (Recommended for Performance)
- **Domain:** $19.98/year (via Namecheap)
- **Hosting (Pages):** $0/month (free tier)
- **Tile Storage (R2):** $0/month (12 MB well under 10 GB free tier)
- **SSL:** $0 (included free)
- **Total Year 1:** **$19.98**
- **Ongoing:** **$19.98/year** (just domain renewal)

### Option 2: GitHub Pages (Simplest for Beginners) ⭐
- **Domain:** $19.98/year (via Namecheap)
- **Hosting:** $0 (GitHub Pages free for public repos)
- **Tile Storage:** $0 (included in repo, 12 MB well under 1 GB limit)
- **SSL:** $0 (included free)
- **Total Year 1:** **$19.98**
- **Ongoing:** **$19.98/year** (just domain renewal)

### Option 3: AWS S3 + CloudFront (Most Powerful)
- **Domain:** $19.98/year (via Namecheap)
- **Storage (S3):** ~$0.023/GB/month = ~$0.28/year for 12 MB
- **CDN (CloudFront):** ~$0.50-1/month for low traffic
- **SSL:** $0 (included free)
- **Total Year 1:** ~$26-32
- **Ongoing:** ~$26-32/year

**All options are incredibly affordable!** The domain is the only real cost.

**Recommendation:** Start with **GitHub Pages** (simplest), migrate to Cloudflare Pages + R2 later if you need faster CDN.

## Files to Update

```
web/
  ├── index.html          # Update Mapbox tile URLs if needed
  └── README.md           # Document production URL

tickets/
  └── 23_production_hosting_domain_setup.md  # This file

.gitignore
  # Add if not present:
  tiles/                  # Don't commit 31K tiles to Git

README.md               # Add "View live at redwoods.earth" badge
```

## Documentation Updates Needed

- [ ] Add production URL to main README.md
- [ ] Document tile regeneration → redeployment workflow
- [ ] Add deployment instructions to `CLAUDE.md`
- [ ] Document domain renewal process (set calendar reminder)
- [ ] Add troubleshooting guide for common issues

## Success Criteria

1. ✓ `redwoods.earth` (or alternative) purchased and owned
2. ✓ Can visit `https://redwoods.earth` in browser
3. ✓ HTTPS working (green padlock icon)
4. ✓ Map loads and tiles display correctly
5. ✓ Performance is good (tiles load <2 seconds on cable internet)
6. ✓ Works on mobile browsers
7. ✓ All 8 ground truth points visible in suitable zones
8. ✓ Domain auto-renews (won't expire accidentally)

## Timeline Estimate

**Option 1: GitHub Pages (Recommended for First-Timers)**
- Domain purchase: 30 minutes
- Push code to GitHub: 15 minutes
- Enable GitHub Pages: 5 minutes
- Configure custom domain + DNS: 15 minutes (+ 30 min wait for propagation)
- Testing: 30 minutes
- **Total: ~2 hours** (mostly waiting for DNS)

**Option 2: Cloudflare Pages + R2**
- Domain purchase: 30 minutes
- Set up R2 bucket + upload tiles: 1 hour
- Update web code for R2 URLs: 15 minutes
- Set up Cloudflare Pages: 30 minutes
- DNS configuration: 5 minutes (+ 30 min wait)
- Testing: 30 minutes
- **Total: ~3-4 hours** (more complex but faster CDN)

## Risks & Mitigations

### Risk 1: Domain Already Taken
- **Status:** ✓ RESOLVED - `redwoods.earth` is available at Namecheap
- **Mitigation (if it becomes taken):**
  - Have 3-5 backup names ready: `redwood-habitat.earth`, `coast-redwoods.earth`, `redwoods.map`
  - Consider related TLDs: `.eco`, `.green`, `.map`

### Risk 2: File Count Limits
- **Issue:** Some hosting services have file count limits (Cloudflare Pages: 20K, we have 31K tiles)
- **Likelihood:** Certain for Cloudflare Pages direct upload
- **Mitigation:**
  - **Solution A:** Use Cloudflare R2 for tiles (no file limit)
  - **Solution B:** Use GitHub Pages (no file limit under 1 GB)
  - **Solution C:** Reduce zoom levels (8-12 instead of 8-14) → ~8K tiles
  - **Solution D:** Use AWS S3 (no limits)

### Risk 3: Forget to Renew Domain
- **Issue:** Domain expires, someone else buys it
- **Likelihood:** Low (if auto-renew enabled)
- **Mitigation:**
  - Enable auto-renewal at purchase
  - Add calendar reminder 2 months before expiry
  - Keep payment method valid

### Risk 4: Costs Increase
- **Issue:** Namecheap raises .earth renewal price
- **Likelihood:** Medium (happens occasionally with specialty TLDs)
- **Mitigation:**
  - **Option A:** Prepay for multiple years (e.g., 3 years @ $59.94 locks in $19.98/year rate)
  - **Option B:** Keep auto-renewal, transfer to cheaper registrar if price jumps significantly
  - **Recommendation:** Stick with annual renewal at $19.98/year - price is already very reasonable
  - Budget $25-30/year for domain (includes buffer for potential increases)
  - Can transfer to another registrar after 60-day lock if needed

### Risk 5: DNS Misconfiguration
- **Issue:** Domain doesn't point to hosting
- **Likelihood:** Low (if using Cloudflare for both)
- **Mitigation:**
  - Follow Cloudflare's auto-configuration
  - Use DNS checker tools (dig, whatsmydns.net)
  - Ask for help in Cloudflare community forum

## Learning Resources

### Domain Registration Basics
- [ICANN - What is a Domain Name?](https://www.icann.org/resources/pages/what-2012-02-25-en)
- [Cloudflare Registrar Docs](https://developers.cloudflare.com/registrar/)

### DNS Fundamentals
- [Cloudflare Learning - What is DNS?](https://www.cloudflare.com/learning/dns/what-is-dns/)
- [How DNS Works (Comic)](https://howdns.works/)

### Cloudflare Pages
- [Cloudflare Pages Docs](https://developers.cloudflare.com/pages/)
- [Custom Domains Guide](https://developers.cloudflare.com/pages/configuration/custom-domains/)
- [Deploy from Git](https://developers.cloudflare.com/pages/get-started/git-integration/)

### Alternative: GitHub Pages
- [GitHub Pages Quickstart](https://docs.github.com/en/pages/quickstart)
- [Custom Domain Setup](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site)

## Glossary (For First-Timers)

**A Record:** DNS record mapping domain → IPv4 address (e.g., `redwoods.earth` → `172.67.154.23`)

**AAAA Record:** DNS record mapping domain → IPv6 address (newer internet protocol)

**CDN (Content Delivery Network):** Network of servers worldwide that cache your content close to users for speed

**CNAME:** DNS alias record (e.g., `www.redwoods.earth` → `redwoods.earth`)

**DNS Propagation:** Time it takes for DNS changes to spread across internet (5 min - 48 hours)

**ICANN:** Non-profit that coordinates domain name system globally

**Nameservers:** Servers that hold DNS records for your domain (e.g., `ns1.cloudflare.com`)

**Registrar:** Company you pay to lease a domain (Cloudflare, Namecheap, GoDaddy, etc.)

**Registry:** Organization that manages a TLD (e.g., Interlink manages .earth)

**SSL/TLS Certificate:** Security certificate that enables HTTPS (the padlock icon)

**Static Site:** Website with just files (HTML/CSS/JS) - no server-side code

**TTL (Time To Live):** How long DNS records are cached before checking for updates

**WHOIS:** Public database of domain ownership info (privacy protection hides your details)

## Next Steps After Hosting

Once the site is live:
- [ ] Submit to Google Search Console for SEO
- [ ] Add analytics (Cloudflare Web Analytics - privacy-friendly, free)
- [ ] Share on social media / relevant forums
- [ ] Add "Share this map" functionality
- [ ] Create OpenGraph meta tags for link previews
- [ ] Consider adding a blog/updates page
- [ ] Link from relevant organizations (Save the Redwoods League?)

## Dependencies

### Prerequisites
- ✓ Web tiles generated (Ticket #21 - COMPLETED: 31,069 tiles, 12 MB)
- ✓ Web interface functional locally (Leaflet.js + OSM basemap)
- ✓ No external API dependencies (no Mapbox needed!)
- ⚠️ Payment method (credit card/PayPal for domain purchase)
- ⚠️ Email address (for domain registration verification)

### Hosting Requirements (Choose One)
- **GitHub account** (if using GitHub Pages - simplest option)
- **Cloudflare account** (if using Cloudflare Pages + R2)
- **AWS account** (if using S3 + CloudFront - most complex)

## Notes

- **Privacy:** Use WHOIS privacy protection (free with Cloudflare) to hide personal info
- **Backups:** Keep local copy of all web files - hosting is not a backup
- **Version control:** Keep website code in Git (separate from tiles if size is an issue)
- **Monitoring:** Set up uptime monitoring (UptimeRobot free tier) to alert if site goes down
- **License:** Consider adding open source license to clarify data usage rights
