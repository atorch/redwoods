# Mobile UX Improvements: Dismissible Info Panel

## Objective

Improve mobile user experience by making the info panel collapsible/dismissible, freeing up screen space for the map on small screens.

## Current Problem

**On mobile devices (phones):**
- ✗ Large info panel takes up ~50-70% of screen height
- ✗ Panel cannot be dismissed or minimized
- ✗ Map is cramped into small remaining space
- ✗ User must scroll down to see legend
- ✗ Poor first impression - info text dominates, not the map

**Current info panel contents:**
- Title: "🌲 Redwood Habitat Suitability"
- Subtitle: "Northern California Coast v0 - Fully Validated"
- Criteria list (3 bullet points)
- Validation status (2 lines)
- Warning box (v0 limitations - 4 bullet points)
- Data sources (3 lines)

**On desktop:**
- ✓ Panel is fine - plenty of screen space
- ✓ Info is useful context
- Info panel is positioned top-right, doesn't obscure map too much

## Proposed Solution

### Option A: Collapsible Panel (Recommended)

Add a minimize/collapse button to the info panel:

**Behavior:**
1. **Initial state (first visit):** Panel is **collapsed** to just a title bar on mobile, **expanded** on desktop
2. **Collapsed state:** Shows only title + expand button (↓ or ▼)
3. **Expanded state:** Shows full content + collapse button (↑ or ▲)
4. **User can toggle:** Click button to expand/collapse
5. **Remembers preference:** Use localStorage to remember collapsed/expanded state

**Benefits:**
- ✓ Gives users choice (can read info if interested)
- ✓ Defaults to better mobile UX (map-first)
- ✓ Doesn't lose important info
- ✓ Standard pattern (users understand collapsible panels)

### Option B: "More Info" Button

Remove panel entirely, add small "ℹ️ Info" button that opens modal/overlay:

**Behavior:**
1. **Default:** Map takes full screen, small "ℹ️" button in corner
2. **Click button:** Modal overlay appears with all info
3. **Click outside or X:** Modal closes

**Benefits:**
- ✓ Maximum screen space for map
- ✓ Cleaner initial view
- ✗ Info is hidden by default (less discoverable)
- ✗ More complex to implement (modal overlay)

### Option C: Move Panel to Bottom (Drawer)

Panel slides up from bottom as a drawer:

**Behavior:**
1. **Default:** Tab at bottom says "About" or "Info"
2. **Swipe up or tap:** Drawer slides up showing content
3. **Swipe down:** Drawer closes

**Benefits:**
- ✓ Mobile-native pattern (like Google Maps)
- ✓ Doesn't block map content
- ✗ Most complex to implement
- ✗ Requires touch gesture handling

**Recommendation:** Start with **Option A (Collapsible Panel)** - simplest to implement, good UX.

## Implementation: Collapsible Panel

### Design Mockup (Text)

**Collapsed state (mobile default):**
```
┌──────────────────────────────┐
│ 🌲 Redwood Habitat      [▼] │
└──────────────────────────────┘
[Map fills rest of screen]
```

**Expanded state (desktop default, mobile after clicking ▼):**
```
┌──────────────────────────────┐
│ 🌲 Redwood Habitat      [▲] │
│                              │
│ Northern California Coast v0 │
│                              │
│ Green areas show where...    │
│ • Wet season rainfall ≥ 20"  │
│ • Nighttime fog ≥ 80 days    │
│ • North of San Simeon        │
│                              │
│ ✓ 8/8 ground truth validated │
│                              │
│ [⚠️ v0 Notes box]            │
│                              │
│ Data Sources:...             │
└──────────────────────────────┘
```

### Code Changes to `web/index.html`

1. **Add collapse button to info panel** (around line 60-90):
   ```html
   <div class="info-panel" id="infoPanel">
       <div class="info-panel-header">
           <h2>🌲 Redwood Habitat Suitability</h2>
           <button id="toggleInfo" class="toggle-button" aria-label="Toggle info panel">
               <span class="icon-collapsed">▼</span>
               <span class="icon-expanded">▲</span>
           </button>
       </div>
       <div class="info-panel-content" id="infoPanelContent">
           <!-- Existing content stays here -->
           <p><strong>Northern California Coast v0 - Fully Validated</strong></p>
           <!-- ... rest of existing content ... -->
       </div>
   </div>
   ```

2. **Add CSS for collapsible behavior** (in `<style>` tag, around line 35-145):
   ```css
   .info-panel-header {
       display: flex;
       justify-content: space-between;
       align-items: center;
       cursor: pointer;
   }

   .info-panel-header h2 {
       margin: 0;
       font-size: 16px; /* Smaller when collapsed */
   }

   .toggle-button {
       background: none;
       border: none;
       font-size: 18px;
       cursor: pointer;
       padding: 5px 10px;
       color: #2c5530;
   }

   .toggle-button:hover {
       background: rgba(0,0,0,0.05);
       border-radius: 3px;
   }

   /* Hide appropriate icon based on state */
   .info-panel.collapsed .icon-expanded {
       display: none;
   }

   .info-panel.expanded .icon-collapsed {
       display: none;
   }

   /* Hide content when collapsed */
   .info-panel.collapsed .info-panel-content {
       display: none;
   }

   /* Mobile: default to collapsed */
   @media (max-width: 768px) {
       .info-panel {
           max-width: 100%; /* Full width on mobile */
           top: 10px;
           right: 10px;
           left: 10px; /* Span full width minus margins */
       }

       .info-panel.collapsed {
           padding: 10px 15px; /* Less padding when collapsed */
       }

       .info-panel-header h2 {
           font-size: 14px; /* Even smaller on mobile */
       }
   }

   /* Desktop: default to expanded */
   @media (min-width: 769px) {
       .info-panel {
           max-width: 320px; /* Keep current width */
       }
   }
   ```

3. **Add JavaScript for toggle behavior** (in `<script>` tag, around line 300):
   ```javascript
   // Collapsible info panel
   (function() {
       const infoPanel = document.getElementById('infoPanel');
       const toggleBtn = document.getElementById('toggleInfo');
       const header = document.querySelector('.info-panel-header');

       // Check if mobile device
       function isMobile() {
           return window.innerWidth <= 768;
       }

       // Load saved state from localStorage, or default based on screen size
       function loadPanelState() {
           const savedState = localStorage.getItem('infoPanelState');
           if (savedState) {
               return savedState; // 'collapsed' or 'expanded'
           }
           // Default: collapsed on mobile, expanded on desktop
           return isMobile() ? 'collapsed' : 'expanded';
       }

       // Save state to localStorage
       function savePanelState(state) {
           localStorage.setItem('infoPanelState', state);
       }

       // Set panel state
       function setPanelState(state) {
           if (state === 'collapsed') {
               infoPanel.classList.add('collapsed');
               infoPanel.classList.remove('expanded');
           } else {
               infoPanel.classList.add('expanded');
               infoPanel.classList.remove('collapsed');
           }
           savePanelState(state);
       }

       // Toggle panel
       function togglePanel() {
           const isCollapsed = infoPanel.classList.contains('collapsed');
           setPanelState(isCollapsed ? 'expanded' : 'collapsed');
       }

       // Initialize panel state on page load
       setPanelState(loadPanelState());

       // Add click handlers
       toggleBtn.addEventListener('click', function(e) {
           e.stopPropagation(); // Prevent triggering header click
           togglePanel();
       });

       // Optional: make entire header clickable
       header.addEventListener('click', function() {
           togglePanel();
       });

       // Optional: reset to default on window resize (mobile <-> desktop)
       let resizeTimer;
       window.addEventListener('resize', function() {
           clearTimeout(resizeTimer);
           resizeTimer = setTimeout(function() {
               // Only reset if crossing mobile/desktop threshold
               const currentState = infoPanel.classList.contains('collapsed') ? 'collapsed' : 'expanded';
               const defaultState = isMobile() ? 'collapsed' : 'expanded';
               if (currentState !== defaultState) {
                   // User hasn't manually set preference, use default for new size
                   const savedState = localStorage.getItem('infoPanelState');
                   if (!savedState) {
                       setPanelState(defaultState);
                   }
               }
           }, 250);
       });
   })();
   ```

## Alternative: Simple Version (Minimal Code)

If the above is too complex, here's a simpler version:

**Just add X button to close panel:**

```html
<!-- Add to info panel header -->
<button id="closeInfo" style="float: right; background: none; border: none; font-size: 20px; cursor: pointer;">&times;</button>

<script>
// Simple close button
document.getElementById('closeInfo').addEventListener('click', function() {
    document.getElementById('infoPanel').style.display = 'none';
});
</script>
```

**Trade-offs:**
- ✓ Super simple (5 lines of code)
- ✓ Fixes mobile UX issue immediately
- ✗ No way to re-open panel once closed
- ✗ Desktop users might accidentally close useful info

## Testing Plan

### Desktop Testing
- [ ] Panel starts expanded by default
- [ ] Click ▲ button → panel collapses to just title bar
- [ ] Click ▼ button → panel expands again
- [ ] Refresh page → panel remembers last state
- [ ] Clear localStorage → panel resets to expanded default
- [ ] Map is still visible and usable in both states

### Mobile Testing (< 768px width)
- [ ] Panel starts collapsed by default (just title bar)
- [ ] Click ▼ button → panel expands showing all content
- [ ] Click ▲ button → panel collapses again
- [ ] Refresh page → panel remembers last state
- [ ] Clear localStorage → panel resets to collapsed default
- [ ] Map takes up most of screen when collapsed
- [ ] Panel doesn't cover more than 70% of screen when expanded

### Cross-browser Testing
- [ ] Test in Chrome (desktop + mobile emulation)
- [ ] Test in Firefox
- [ ] Test in Safari (iOS)
- [ ] Test in Edge
- [ ] Verify toggle animation is smooth (if added)

### Accessibility Testing
- [ ] Toggle button has proper `aria-label`
- [ ] Keyboard navigation works (Tab to button, Enter to toggle)
- [ ] Screen reader announces panel state ("expanded" / "collapsed")
- [ ] Focus management is logical

## Future Enhancements (Out of Scope for This Ticket)

- [ ] Smooth animation for expand/collapse (CSS transition)
- [ ] Swipe gesture support on mobile (swipe up/down to toggle)
- [ ] "Tour" mode for first-time visitors (highlights features)
- [ ] Move legend inside collapsible panel on mobile
- [ ] Add "Share" button to panel (copy URL, share on social media)
- [ ] Add "Download data" button (export GeoJSON of visible area)

## Success Criteria

1. ✓ Info panel is collapsible via button click
2. ✓ Panel defaults to collapsed on mobile (<768px)
3. ✓ Panel defaults to expanded on desktop (≥769px)
4. ✓ Panel state persists across page reloads (localStorage)
5. ✓ Map is fully usable in both collapsed and expanded states
6. ✓ Button indicates current state (▼ when collapsed, ▲ when expanded)
7. ✓ Works on all major browsers (Chrome, Firefox, Safari, Edge)
8. ✓ Accessible via keyboard navigation
9. ✓ Production site updated at https://redwoods.earth

## Timeline Estimate

- **Code changes:** 30-45 minutes
- **Local testing:** 15 minutes
- **Deploy to production:** 5 minutes
- **Production testing:** 15 minutes
- **Total:** ~1-1.5 hours

## Files Modified

```
web/index.html
  - Add .info-panel-header wrapper around title
  - Add #toggleInfo button
  - Wrap content in .info-panel-content div
  - Add CSS for collapsed/expanded states
  - Add JavaScript for toggle behavior and localStorage
```

## Related Tickets

- **Ticket #21:** Production web tiles (COMPLETED - includes mobile responsive claim)
- **Ticket #23:** Production hosting (COMPLETED)
- **Ticket #24:** Deploy tiles to Cloudflare R2 (PENDING)

## Notes

- This ticket addresses the gap in Ticket #21's "mobile responsive design" claim
- Ticket #21 made the layout responsive, but didn't optimize content for mobile screens
- After this, mobile UX should be significantly improved
- Consider user feedback - might need to adjust default state or behavior
- Could A/B test: collapsed vs expanded default on mobile
