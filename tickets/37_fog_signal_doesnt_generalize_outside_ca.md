# Fog signal (GOES-16 nighttime BTD) doesn't discriminate outside California

**Status:** open · **Priority:** medium · **Created:** 2026-08-12 · **Related:**
ticket 36 (northern range limit — where this was found), ticket 34 (evaluated
published fog rasters), ticket 33 (fog window extension)

## Why this ticket exists

Investigating ticket 36's bbox extension to 44 N surfaced a bigger problem
than the range-edge question it was created to answer: **our fog criterion
(GOES-16 Ch13-Ch7 nighttime BTD >= 50 fog-nights/season) stops discriminating
anything once you leave California.**

Masking each of the 5 suitability criteria separately over 41.9-44.0 N:

| band | rain pass | fog pass | temp pass | PHZM pass |
| --- | --- | --- | --- | --- |
| CA/OR border (41.9-42.1N) | 54% | 72% | 46% | 10-12% |
| ~43.0N | 89% | 99% | 41% | 12-33%* |
| ~43.5N | 85% | 100% | 64% | 11-35%* |
| Eugene latitude (43.9-44.0N) | 91% | 95% | 71% | 9-33%* |

(*PHZM range reflects before/after the ticket-36 threshold tightening to
-5.0 C — see that ticket's Progress section.)

Fog goes from being one of our more discriminating criteria at the CA/OR
border (72% pass — meaningfully rejecting ~28% of pixels) to **essentially
saturated (95-100% pass) just a few dozen miles further north**, including
at inland pixels ~40 miles from the coast (Willamette Valley, near Eugene)
where marine advective fog has no physical mechanism to reach at all. This
is the opposite of what the literature predicts (fog frequency should drop
north of Cape Blanco, ~42.85 N — see ticket 36's original writeup) and it
doesn't correlate with distance from the coast the way a real marine-layer
signal should.

Concrete case: Kloster Mountain, OR (43.867 N, ~50 mi inland) reads 89.4
fog-nights/season in our data — comfortably over the 50-night threshold,
and higher than several of our actual coastal redwood-grove ground-truth
points. (This point was the reason PHZM got tightened in ticket 36; the
underlying fog reading there was never fixed, just outvoted by PHZM.)

**Second concrete case, and this one PHZM doesn't save us on either:**
Grassy Knob Wilderness, OR (42.738214389753445, -124.33380578224426),
found 2026-08-12 while spot-checking the ticket-36 bbox westward-extension
fix (Port Orford was getting artificially clipped by `min_lon`; fixing that
pulled Grassy Knob fully into the study area for the first time). Its own
Wikipedia entry describes the forest as Port-Orford-cedar and old-growth
Douglas fir, no redwood mention; Travel Oregon's own material calls the
Chetco River grove near Brookings (~42.05 N) "Oregon's *only* naturally
occurring coastal redwoods." So Grassy Knob, ~50 mi north of that, reads as
a confident non-habitat site on first-principles/documentary grounds. But it
currently passes every criterion in the live rule: 123 in rain, 82.8
fog-nights, 3.8 C coldest-month tmin, and — the notable one — a PHZM avg
annual extreme min of **-3.75 C**, which is *milder* than Humboldt Redwoods
(-3.83 C, one of our confirmed positives). That means no PHZM floor can ever
reject Grassy Knob without also rejecting Humboldt Redwoods: unlike Kloster
(-6.5 C, well outside the ticket-36 gap), this site sits on the *warm* side
of every one of our positives on this variable. PHZM doesn't just fail to
discriminate it — it can't, by construction, for any threshold choice. Left
unresolved for now (not added as a tracked negative control point); noted
here with exact coordinates so a future pass on this ticket's candidate
directions has a concrete, already-verified failure case to test against.

## Working explanation

The NESDIS nighttime BTD method (CIMSS Ch13-Ch7 brightness-temperature
difference) detects **low water cloud generally** — it doesn't distinguish
"coastal marine layer stratus, the kind that drips onto redwood canopy" from
"any other low nighttime cloud." It worked as a fog proxy for California
specifically because CA's dry-season interior is reliably clear at night, so
a positive BTD hit there was almost always real coastal fog by elimination.
Oregon's summer nights are cloudier in general, including well inland, so
the same detector is now picking up ordinary night cloud cover unrelated to
the redwood-relevant mechanism. It's a detector implicitly calibrated to
California's climate regime that silently stopped meaning what we needed it
to mean once pointed at a different one.

This is *not* the same problem ticket 34 investigated (published fog
products disagreeing with each other / coastal-cell coverage artifacts) —
this is our own primary product failing to generalize geographically, which
is a more fundamental issue if we ever want the map to extend past Oregon.

## Why this is lower priority than it sounds

Ticket 36's PHZM tightening (-7 C -> -5 C) already pulls the suitable area
back to a physically plausible narrow coastal ribbon for our current 20
ground-truth points, without touching fog at all — PHZM alone is currently
doing enough discriminating work north of the border to mask this problem
in practice. This ticket is about the fog *signal itself* being unreliable
outside CA, which matters for:

- Confidence in the coastal ribbon that currently remains between the CA/OR
  border and 44 N (is it real marine fog, or just PHZM's threshold holding
  the line alone, with fog silently contributing nothing?)
- Any future extension further into Oregon/Washington, where PHZM's own
  discriminating power is untested and may not hold up alone.

## Candidate directions (not scoped in detail — pick before starting)

1. **Raise the fog threshold specifically outside some latitude/region** —
   fast, but is exactly the kind of ad hoc latitude-proxy patch ticket 36
   explicitly ruled out for the rule itself. Avoid.
2. **Combine multiple fog products into an ensemble/voting signal**
   (GOES-16 nighttime BTD + GOES-18 daytime + MODIS Werner + Torregrosa
   decadal — all already sampled per-point by
   `scripts/annotate_ground_truth_points.py`). Ticket 34 found these
   disagree substantially at individual points (up to ~10x at Limekiln) and
   have their own coverage gaps (Torregrosa's ~4 km coastal-only frame drops
   inland points via NoData). Combining them defensibly is real work:
   deciding a voting/weighting scheme, handling mismatched footprints and
   units, and re-validating against ground truth. This is the most
   promising direction but is not a quick fix.
3. **Look for a feature that's robust to climate-regime shift** — e.g. a
   *relative* fog metric (this pixel vs. its own regional baseline) instead
   of an absolute night-count threshold, or a fog-persistence/duration
   statistic rather than binary occurrence. Needs research before it's
   scoped.
4. **Accept the limitation and document it** — cheapest option. State
   plainly (about page / methodology) that the fog criterion is validated
   for California and may over-admit territory outside it; lean on PHZM and
   the "north of Cape Blanco" framing already drafted in ticket 36's
   recommendation.

## Out of scope for this ticket

- Fixing the specific Kloster Mountain false positive — already handled via
  PHZM in ticket 36.
- Re-litigating ticket 34's published-fog-product evaluation.
- Any change to the CA-only accuracy of the current fog criterion — it's
  fine where it was validated; this is specifically about generalization.
