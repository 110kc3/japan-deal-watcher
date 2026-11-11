# Review findings

[Start here](../REVIEW.md) · [Model](recommendation-model.md) · [Roadmap](product-and-roadmap.md) · [Evidence](evidence.md)

Observed 2026-11-11 at commit `bbc7a511268bb1efa607cc8598a19846877a30dd`; feed timestamp `2026-11-11 17:03 UTC`. P0 means a purchase decision can be materially wrong; P1 means substantial quality, usability or operational risk; P2 means maintenance debt. Findings describe the reviewed implementation, not implemented fixes.

## What is worth keeping

The small Python pipeline and static PWA are a reasonable base for a personal sourcing tool. Preserve PLN calculations, the central Python cost functions, direct listing links, category filters, saved cart, exact-model search intent, tests using temporary files, and camera/lens purchase caps. A framework rewrite, native Android app or paid AI service is unnecessary for the first improvements.

## P0: misleading purchasing decisions

### F01 — Product identity and valuation are disconnected

[`data/current_deals.json`](../data/current_deals.json) contains these active records. Translation below describes the stored Japanese title; it is not a fresh availability claim.

| Item ID | Displayed/valued as | Stored seller title indicates | Displayed margin |
|---|---|---|---:|
| `m50999156610` | PS4 Metal Gear Solid V limited console, boxed | `[まとめ売り] PS4 メタルギアソリッドV 2本セット`: two PS4 game titles | +753.44 PLN |
| `m21968455105` | Olympus Mju-II 35mm f/2.8 prime | `オリンパス ミュー(mju:)ZOOM PANORAMA`: Mju Zoom Panorama | +688.40 PLN |
| `m63811160268` | DS Lite Dialga/Palkia console | `Nintendo DS Liteシリコンカバー…`: silicone cover | +206.89 PLN |
| `m35606738599` | PSP-2000 Mint Green | `22.0 ASICS SUKU2 … TOPSPEED MINI`: children's shoes | +199.03 PLN |
| `m88450883898` | GBA SP console with charger | `ゲームボーイアドバンスSP 外箱 取扱説明書 オニキスブラック`: outer box and manual | +186.56 PLN |

[`scripts/update_with_real_live_listings.py`](../scripts/update_with_real_live_listings.py), `harvest_mercari_deals` and `harvest_yahoo_deals`, select the first unused search result while retaining the template's model, colour and resale value. Search exclusions are stripped. [`watcher/fetcher.py`](../watcher/fetcher.py), `scan_watchlist`, preserves this identity; [`watcher/webapp_exporter.py`](../watcher/webapp_exporter.py), `process_mercari_deal`, presents it instead of the seller title. Valid listing IDs do not prove a model match.

**Required outcome:** separate search targets from observed listings. Verify product type, model code, variant, included items, quantity, region and condition before attaching a valuation. These five examples must be regression fixtures. A new listing ID must not inherit the previous listing's condition or comparables.

### F02 — Observed prices can be replaced by desired prices

The harvesting script explicitly clamps camera/lens prices to 3,800 JPY when no cheap result exists, in both marketplaces. Yahoo harvesting updates `current_price_jpy`, while exporters/costs use `price_jpy`; **68 of 73** raw records have conflicting values. The separate [`scripts/apply_time_and_price_calibration.py`](../scripts/apply_time_and_price_calibration.py) assigns hand-written prices and countdowns and requires positive margins before saving.

**Required outcome:** observations are immutable facts. A budget cap rejects an opportunity; it never edits the market price. Retain over-budget and loss-making observations for diagnostics. Keep demo/calibration inputs outside production data.

### F03 — Expired auctions become active again

[`watcher/time_utils.py`](../watcher/time_utils.py), `calculate_auction_timing`, discards end times more than two minutes in the past, then sets a new future deadline from old remaining minutes. At feed generation, **54 raw auctions already had past deadlines; all 54 still appeared in the active feed**. A deterministic probe turns yesterday's end time into one hour from now. Fixed UTC+1 also misrepresents Poland during summer time.

**Required outcome:** preserve source end time, use timezone-aware parsing and `Europe/Warsaw`, distinguish expired from confirmed sold, and accept extensions only from a new source observation. Missing deadlines mean unknown. Rebuilding a report must not refresh listing freshness.

### F04 — Polish sale evidence is missing from the valuation chain

`est_pl_value`, `closed_price_*`, `allegro_archive_pln` and `olx_haggled_pln` are stored estimates with no linked comparable records, observation dates or sample sizes. Exporter fallbacks manufacture Allegro/OLX values from `est_pl_value × 1.08/0.90`; the lot inspector uses similar multipliers. The links lead to current searches. They do not prove completed sales or negotiated OLX cash prices.

[`POLAND_REAL_SALES_AUDIT.md`](../POLAND_REAL_SALES_AUDIT.md) claims a recent 90-day transaction audit without supplying the underlying transactions. Allegro's [official notice](https://allegro.pl/pomoc/aktualnosci/zamkniemy-archiwum-allegro-O36m6egKPcm) announced closure of its public archive in March 2026 and earlier redirects to active listings. The November claim therefore needs a different, auditable source; the repo supplies none.

**Required outcome:** distinguish sold evidence, asking prices and assumptions. Use model/condition/region-matched evidence with date and sample size. When sold evidence is unavailable, show a research candidate and an explicit owner-entered estimate, not a verified market price.

### F05 — Unknown condition and risk increase apparent attractiveness

`classify_condition('')` returns `standard_good` and `is_working=True`. `ConditionAnalyzer.detect_condition({})` claims confirmed 100% working and very good appearance. Polish editorial notes are mixed with seller evidence. [`watcher/deal_analyzer.py`](../watcher/deal_analyzer.py) gives untested items a bonus, uses hand-assigned category “liquidity” weights, and adds passed-check labels without running all those checks. Its “optimal” basket takes two battery and four non-battery records without requiring `is_worth_buying`, budget or parcel feasibility.

**Required outcome:** unknown remains unknown; seller assertions and physical inspection are distinct. Apply hard eligibility gates before ranking. Untested hardware needs downside economics and an explicit risk profile. A score must never compensate for the wrong product or missing price evidence.

### F06 — “Net” and “guaranteed” profit omit important costs

[`watcher/costs.py`](../watcher/costs.py) calculates resale estimate minus import estimate, without Polish selling fees, returns, repairs, labour, holding cost or product-specific duty/clearance treatment. Fixed 800 JPY domestic freight plus 2 EUR proxy fee does not match the current [ZenMarket fee structure](https://zenmarket.jp/en/fees.aspx): 800 JPY service fee for Mercari/JDirectItems, with domestic freight separately dependent on the seller. Errors can overstate or understate costs; they are not uniformly conservative.

`docs/app.js:runCalculator` also applies a different deposit/VAT formula from Python and its own cart. At 10,000 JPY, 0.025 PLN/JPY, 4.35 PLN/EUR and 30 PLN freight, Python returns **390.50 PLN** and the browser formula **391.70 PLN**. [`watcher/closure_predictor.py`](../watcher/closure_predictor.py) caps forecast market prices to the owner's camera/lens budget, artificially improving the forecast. Its 1.08 near-close multiplier is a heuristic, not a calibrated prediction.

**Required outcome:** one versioned cost model, channel-specific scenarios and explicit unknowns. Budget limits constrain bids, never forecasts. Replace “guaranteed”, “sure arbitrage” and “net profit” with accurately scoped estimates. See [the proposed model](recommendation-model.md).

### F07 — Market events are presented as realized trading results

[`watcher/history_tracker.py`](../watcher/history_tracker.py), `record_scan`, considers every non-active state sold/ended, including connection errors, 404s and broken exclusions. Of **188 sales-log records**, 54 are 404s, 18 broken exclusions and 11 in-progress transactions. Even the other 105 sold-labelled marketplace events do not prove the owner bought or resold anything. A first-seen inactive listing gets one day on market and “under 24h” speed.

[`watcher/finished_auctions_tracker.py`](../watcher/finished_auctions_tracker.py) seeds eight curated records, copies the last observed price into final price, and computes `realized_margin_pln = est_pl_value - landed_cost_pln`. The PWA's eight-record archive totals **3,048.80 PLN** in such margins. Its header ROI is a hardcoded **+82.8%** in `docs/index.html`.

**Required outcome:** separate market observation history from the owner's purchase/sale ledger. Only a confirmed settlement can create realized profit. Missing outcomes and unsold stock stay visible. Japanese listing disappearance cannot measure Polish demand or Polish days-to-sale.

### F08 — “AI Vision” does not inspect images

[`watcher/lot_vision_inspector.py`](../watcher/lot_vision_inspector.py), `inspect_lot_photo_contents`, matches text against a dictionary and defaults to 30 items plus 6 PLN per filler. It accepts prefilled inspection metadata without checking provenance. No image is required. A text-only `Pokemon emerald` probe returns `inspected=True`, “AI Vision”, 30 items and a 269 PLN lot value. The PSP branch contains fixed good-buy language and an assumed yield.

**Required outcome:** label text parsing truthfully. A visual finding must reference an actual image/crop and confidence; unknown objects contribute no confirmed resale value. Lot proceeds must include unsold units, failure rate, replacement parts and per-item handling.

### F09 — Parcel suitability is oversimplified

[`watcher/config.py`](../watcher/config.py), [`watcher/consolidation.py`](../watcher/consolidation.py) and [`watcher/checks.py`](../watcher/checks.py) model batteries largely as one boolean per listing and freight as category shares or approximate weight tiers. Bundles may contain several devices. A wired/battery-free category is not proof of every listing's contents. Storage starts from one global date, not each warehouse receipt.

Generated advice says sea mail removes battery limits and older advice says battery removal is free. [Japan Post's rules](https://www.post.japanpost.jp/service/send/oversea/attention/restriction/index_en.html) apply dangerous-goods restrictions to sea mail too; its [battery conditions](https://www.post.japanpost.jp/service/send/oversea/attention/restriction/restriction02_en.pdf?210226=) distinguish cells and assembled batteries, installation, capacity and destination. [ZenMarket](https://zenmarket.jp/en/fees.aspx) lists paid battery disposal.

**Required outcome:** per-device quantities and battery evidence, carrier/destination rules, actual packing and shipping quotes, and dated warehouse arrivals. Unknown eligibility blocks an executable parcel plan. Removing batteries needs cost, service confirmation and replacement allowance.

## P1/P2: product and engineering quality

| ID / priority | Evidence and consequence | Recommended outcome |
|---|---|---|
| F10 / P1 — excessive reading | Eight root Markdown reports total 609,345 bytes and approximately 47,610 whitespace-delimited words. Mobile first card: 208 words, eight actions, 1,375px high. First title/profit below initial viewport; phone page overflows horizontally. Repeated navigation, predictions, badges and prices compete. | Compact qualified shortlist; expandable evidence; single primary action; [specific UX acceptance](product-and-roadmap.md). |
| F11 / P1 — unsafe HTML interpolation | `docs/app.js:renderDealCard` and other card functions interpolate model, notes and links into `innerHTML`. A harmless model field injected into a local test feed executed an event handler. No live exploit was attempted or observed. | Use text nodes, safe attribute construction and validated URL protocols/hosts. Add malicious-string fixtures, then CSP as defence in depth. Fix before expanding external ingestion. |
| F12 / P1 — inconsistent archives and writes | `main.py` uses `data/finished_auctions.json` (62 records), then passes `output_file` to the exporter, which selects `docs/data/finished_auctions.json` (eight records). The workflow stages neither the main finished archive nor `MYSTERY_LOTS_ANALYSIS.md`, despite generation. JSON writes are in-place; failed history loads initialize empty/seed data. | One authoritative archive; export only; atomic publication; quarantine corrupt input and preserve last valid state. Explicit complete output manifest. |
| F13 / P1 — refresh claims exceed ingestion | Hourly workflow runs `main.py`, which rescans tracked Mercari IDs but reads Yahoo data from disk. The separate discovery script is not scheduled. It has no exact-model validation. PWA fetches at startup; a ticking countdown is not a refreshed bid. Service worker caching plus timestamped query keys has no reliable stale-age contract. | Independent observed-at times, source health, permitted discovery adapters, failure/backoff policy, stale warnings and pre-action rechecks. No “live” label solely from export time. |
| F14 / P1 — green tests validate wrong contracts | 104 tests and strict audit pass. Tests require capped predictions and seeded realized margins. Link checks only inspect strings while claiming zero 404s; currency audit uses fallback constants while labelled live. No browser test is in CI. | Correct contracts first; test the defects above and real decision paths. Name format checks honestly. Add fixture-based integration and browser smoke coverage. |
| F15 / P2 — duplication and automation debt | Python/browser repeat cost, freight and category rules; app/export version strings differ. Dependency is `mercapi>=0.5.0` without a lock. No PR test workflow; current push paths omit frontend-only/tests-only/dependency changes. Rebase uses `-X ours --autostash`. Generated README is rewritten hourly. `main.py` overwrites fixed-date absolute vault report paths. | One configuration/schema contract; reproducible dependency constraints; CI independent from scanning; conflict failures surfaced; static README; opt-in report destinations; remove implicit personal vault writes. |
| F16 / P1 — no actual resale feedback | Cart is localStorage planning state, not an order ledger. No owner purchase costs, Polish sale settlements, refunds, actual handling time or inventory aging dataset was found. Repo is public despite “Private Deal Watcher” text. | Private local ledger with export/backup, aggregate-only public metrics; evaluate realized return and time-to-cash, not number of deals generated. |

No source code, scoring policy, data or deployment behaviour was changed in this review. Two historical hand-maintained audits receive supersession notices; generated reports need a coordinated generator change when recommendation 3 is selected.
