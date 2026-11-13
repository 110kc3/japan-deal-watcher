# Verification of the F01–F16 fixes — 2026-11-13

Repository: `japan-deal-watcher` · Agent: Claude Code

Verified source: code at [`196097d`](https://github.com/110kc3/japan-deal-watcher/commit/196097d9f55534d1a63167c4f4aa650073b8b84b); published feed also checked at
[`0cd3310`](https://github.com/110kc3/japan-deal-watcher/commit/0cd331077c67be355ec0f43c33ebb27d30f6d7c3) (2026-11-13 21:20 UTC). The commits between them change generated
data and reports only.

The [11 November review](../REVIEW.md) listed findings F01–F16. Commit `add2062`
("implement review roadmap choices 1-9, fix F01-F16") claimed to fix all of them. This
document checks that claim finding by finding. The owner asked for it to be recorded here.
**Nothing below is fixed by this document, and the suggestions are not selected.**

## Verdict

**The feed cannot be trusted for buying decisions yet.** Of the 16 findings, 1 is fixed
(F16, in code only and unused), 10 are partially fixed and 5 are not fixed; no P0 finding
is fully fixed. The new modules exist and are unit-tested, but most are not called by the
pipeline that produces the published feed. The original review's own mismatch examples are
still in that feed as available deals.

## Method and limits

- Read-only. `main.py`, `check_deals.py`, `inspect_lot.py` and `scripts/` were not
  executed; no marketplace was contacted. Pipeline wiring is established from reading the
  code and the committed outputs.
- Experiments ran on a `git archive` copy outside the repository with synthetic input.
  `docs/app.js` was run in a Node `vm` with a stubbed DOM, which covers the string
  renderers, sorting and calculator, not real browser layout.
- The wiring results for `ProductMatcher`, `RecommendationModel`, `AlertsEngine`,
  `calculate_marginal_freight` and `ResaleLedger`, the presence of the six listed listing
  IDs in the committed feed, the guarantee line in the generated report, the unpinned
  requirement and the workflow's staged-file list were confirmed by a second, independent
  read. The remaining rows rest on the first pass.
- Not checked: whether the mismatched listings are still on sale; real Yahoo end times;
  card height at 390×844; the deployed Pages build; the host timer for the Switch scan.

## Verification status

- The repository's `.venv` has no pytest (`No module named pytest`).
  `.venv/bin/python -m unittest discover -s tests -q`: exit 0, **166 tests OK**, with the
  network blocked and no connection attempts.
- The tests are not hermetic: the run rewrote `data/finished_auctions.json` in the copy,
  because `tests/test_webapp_exporter.py:80,110,169,224` build the exporter without a
  `finished_file`.
- Scheduled Actions runs are green, the latest being [43509644590](https://github.com/110kc3/japan-deal-watcher/actions/runs/43509644590). They ran roughly
  every 6–9 hours rather than hourly.
- Documentation push for this report: CI verification pending; not awaited.

## F01–F16 at the verified commit

| ID | Verdict | Evidence | Basis |
|---|---|---|---|
| F01 identity | **In code, not wired in**; the matcher is also weak | `ProductMatcher` is called only at `watcher/deal_analyzer.py:102`, which feeds `reports/latest.md`. `watcher/webapp_exporter.py:324-435,498-501` exports every available record under the template model, with no seller title. | Reproduced |
| F02 observed prices | **Not fixed** | Clamps remain at `scripts/update_with_real_live_listings.py:139-145,231-234` and `scripts/apply_time_and_price_calibration.py:21,36,67`. `price_jpy != current_price_jpy` in 68 of 73 Yahoo records. Price falls back to `target_price_jpy` at `watcher/fetcher.py:207`. | Reproduced (data); code reading (scripts) |
| F03 expiry | **Partially fixed** | A valid past `ends_at` now stays ended (`watcher/time_utils.py:63-70`). An unparseable `ends_at` falls back to `now + minutes` (`:71-84`), and an active status with no time gets +120 minutes (`:88-91`). | Reproduced |
| F04 Polish evidence | **Not fixed** | `est_pl × 1.08 / 0.90` fallbacks remain at `watcher/webapp_exporter.py:150-151,336-337` and are still labelled as finished Allegro and haggled OLX prices at `docs/app.js:1549-1550`. No comparables dataset exists. | Code reading |
| F05 condition and risk | **Partially fixed** | Empty text now gives `unknown` (`watcher/fetcher.py:153-182`). The untested bonus remains at `watcher/deal_analyzer.py:226-227`; `checks_passed` is appended without running at `:281`. A junk, no-power listing classifies as `unknown`, not broken. | Reproduced |
| F06 net profit | **Partially fixed; the real model is not wired in** | `watcher/costs.py` is unchanged: no selling fees, returns or labour, and it still returns `guaranteed_margin_pln`. `RecommendationModel` is imported at `watcher/deal_analyzer.py:17` and never called. | Reproduced |
| F07 realized results | **Partially fixed** | Errors and 404s are no longer logged as sales and the hardcoded +82.8% is gone. `realized_margin_pln` is still written in `watcher/history_tracker.py`, and a first-seen sold item is still labelled as selling within 24 hours. | Reproduced |
| F08 "AI Vision" | **Partially fixed** | Text-only input is now labelled as text analysis. A bare `image_analyzed: True` with no image still yields "AI Vision" (`watcher/lot_vision_inspector.py:474-495`); prefilled inspections bypass relabelling (`watcher/webapp_exporter.py:261`); `docs/app.js:1445` prints a photo-inspection label for everything. | Reproduced |
| F09 parcel | **In code, not wired in** | `calculate_marginal_freight` (`watcher/consolidation.py:380`) is used only by tests; `main.py:80-84` still uses one global start date. The "sea mail, zero battery limits" text is still generated at `watcher/sniper_guide_generator.py:342` and `watcher/alternative_generator.py:194`. | Code reading |
| F10 clutter | **Partially fixed** | README is 81 lines (the commit said 65). The app defaults to a compact Top-5 (`docs/app.js:608-683`). The nine root reports still total about 33,000 words. | Code reading |
| F11 unsafe HTML | **Partially fixed** | About 1,280 single-field mutations found no injection in deal or stream cards. `docs/app.js:1139` interpolates a string `final_price_jpy` raw at `:1182,1200`; `sanitizeUrl` returns `//host` unchanged (`:225`); there is no CSP. | Reproduced (Node harness) |
| F12 archives and writes | **Partially fixed** | Both finished archives hold the same records. Non-atomic writes remain at `main.py:75,97,113,126,139,152,189` and `watcher/alerts.py:88`. A corrupt finished file is quarantined, then replaced by eight seed records (`watcher/finished_auctions_tracker.py:300-304`). The workflow does not stage `data/finished_auctions.json`, `reports/latest.md` or `MYSTERY_LOTS_ANALYSIS.md`. | Reproduced |
| F13 refresh claims | **Not fixed** | `.github/workflows/update-deals.yml` runs tests, `main.py` and `check_deals.py --strict`: it rescans tracked Mercari IDs and reads Yahoo from disk. `data/yahoo_deals.json` last changed 2026-11-10. `AlertsEngine` is not imported outside tests. The app shows no feed age. | Code reading plus data |
| F14 tests | **Partially fixed** | The new tests assert real behaviour of the new modules. Nothing tests that the exported feed excludes mismatches; there is no JavaScript, browser or injection test. `tests/test_deal_analyzer.py:96-117` still requires untested gear to be worth buying. | Reproduced |
| F15 duplication and automation | **Not fixed** (two sub-items done) | `requirements.txt` is still `mercapi>=0.5.0` with no lock; no pull-request trigger; `rebase -X ours --autostash` remains; version strings are 2.2.2 in the exporter and 2.3.1 in `docs/sw.js`. README is now static and vault writes are opt-in (`main.py:157`). | Code reading |
| F16 resale ledger | **Fixed in code, unused** | `watcher/resale_ledger.py` has the lifecycle, atomic writes, CSV export and tests. `main.py:229-232` only prints metrics; no CLI or UI adds a purchase and no ledger file exists. | Code reading |

### F01 in detail

Seven of 54 exported Mercari deals are ones `ProductMatcher` itself rejects. All five
examples from the original review are still in the feed as available:

| Listing | What it is | Shown as |
|---|---|---|
| `m50999156610` | two PS4 games | PlayStation 4 Metal Gear Solid V console |
| `m21968455105` | Mju Zoom Panorama | Olympus Mju-II prime |
| `m63811160268` | silicone cover | Nintendo DS Lite |
| `m35606738599` | ASICS shoes | PSP-2000 |
| `m88450883898` | box and manual | Game Boy Advance SP |

Running `docs/app.js` against both the verified and the latest feed puts the games, the
Mju Zoom and the silicone cover at positions 1, 2 and 5 of the default Top-5, with the
shoes at position 6.

Mismatches the matcher does not catch in committed data: `m62431207953` (a GameCube
controller valued as the console, also row 3 of `reports/latest.md`), `m15645134061`
(a lens hood and cap set valued as a 50 mm lens) and `m10006553647` (Switch software
valued as a Game Boy Color).

Matcher probes on synthetic titles: 24 of 25 titles that should be rejected were accepted
(only "box only" was caught) — including junk listings, empty boxes, compatible batteries,
a game titled with the console name, Switch Lite, OLED and Switch 2 against each other's
targets, Joy-Con and a dock. In the other direction, 7 of 7 legitimate listings were
rejected, for example a complete DS Lite with box and manual. Yahoo records carry no
seller title, so identity there cannot be verified at all.

### Calculator parity (F06)

The review's case now gives 390.50 PLN in both Python and the browser. Over 3,000 random
cases in the selectable categories, 50 differ by 0.01–0.03 PLN from rounding. For
categories missing from the JavaScript map at `docs/app.js:1707-1722` (for example
`ps1_consoles`, `retro_consoles_no_battery`, `mechanical_keyboards`) the difference
reaches 44 PLN.

## New findings

1. **High — the default Top-5 puts the worst mismatches first.** `docs/app.js:301-331`
   gates on margin only, and the `time_asc` sort at `:913-919` treats Mercari items as
   ending now, so they sort ahead of all auctions. Reproduced on both feeds.
2. **High — `reports/latest.md` asserts a false guarantee.**
   `watcher/markdown_generator.py:412` hardcodes that identity is 100% checked by
   `ProductMatcher` with zero product substitutions. The workflow never commits this file,
   although the README links it first. Reproduced.
3. **High — Yahoo data is frozen with synthetic end times.** All 73 end times fall on a
   handful of identical minute-and-second stamps. Ended ones are archived as won auctions
   with the last price as the final price (`watcher/finished_auctions_tracker.py:356-361`).
   The auction tab was down to nine and will be empty by 2026-11-16. Reproduced from data.
4. **Medium — test fixtures are in the published archive.** `deal_ended`, `test_camera`
   and `new_n3ds_xl_red` are in `docs/data/finished_auctions.json`. The workflow runs the
   tests before `main.py`, so this recurs every run. Reproduced.
5. **Medium — `closed_at` is rewritten every run.** The exporter re-harvests each ended
   auction and stamps a new time (`watcher/finished_auctions_tracker.py:391-397`); 60 of
   71 records share one timestamp. Reproduced.
6. **Medium — `ProductMatcher` rejects real consoles and lots.** Any console title that
   mentions a manual, case or film is rejected (`watcher/product_matcher.py:14-27`), and
   "3ds" in a lot's model name makes it a console target (`:226-227`). Reproduced.
7. **Medium — any exception containing "data" becomes "ended / 404".**
   `watcher/fetcher.py:297` matches on the error message, so an unrelated API or parse
   failure marks a live listing as gone. Code reading.
8. **Low — `sanitizeUrl` allowlist bypass.** `//host` and `/\host` are returned unchanged
   (`docs/app.js:225`). The feed is self-generated, so exposure is small. Reproduced.
9. **Low — a string numeric field breaks rendering.** `.toFixed` on a string price throws
   (`docs/app.js:1407-1408`, `:1140-1144`); one bad record blanks the list. Reproduced.
10. **Low — the calculator keeps the previous category** when the deal's category has no
    option (`docs/app.js:1683`), so the wrong shipping share is used.
11. **Low — the Switch scanner's matcher is permissive.** `scripts/scan_switch_offers.py:45-55`
    accepts games, Joy-Con, docks, empty boxes, cracked screens and banned-account
    listings. The committed report is mostly real consoles because the search is scoped.
12. **Low — the service worker cache grows without bound.** `deals.json?v=<timestamp>` is
    cached under a new key each load, and the offline fallback at `docs/sw.js:63-67` can
    never match. Code reading.

Also noted: the repository is public while the README describes it as private. A pattern
scan of tracked files and history found no credentials.

### Uncertain

- `m76298209263`, a Fuji Cardia listing at 500 JPY (row 4 of `reports/latest.md`), may be
  only a camera case.
- Timestamps use `datetime.now()` labelled "UTC" (`watcher/webapp_exporter.py:442`,
  `watcher/history_tracker.py:61`): correct on CI, wrong on a non-UTC host.
- `publish()` in `scripts/scan_switch_offers.py:227` never removes its temporary clone.

## Suggestions — not selected

1. **Export the seller's Japanese title and the match verdict in the feed, and gate the
   export on it.** `docs/app.js:1340` already renders `seller_title`; the exporter never
   sends it. This is the shortest path to making F01 real.
2. **Show feed age and per-source last-observed time** in the app header, and suppress buy
   actions beyond a threshold.
3. **Add a small ledger CLI** (add purchase, advance stage, record settlement) so F16 can
   record the first real resale outcome.
