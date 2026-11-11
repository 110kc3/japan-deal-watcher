# Product simplification and feature choices

[Start here](../REVIEW.md) · [Findings](findings.md) · [Model](recommendation-model.md)

All choices below are **proposed, unselected work**. Estimates are focused engineering days for one developer after inputs/access are available, not deadlines; collecting real resale outcomes takes longer. This document is a proposal catalogue, not an executable task queue.

## Default experience: answer “what is worth checking today?”

Use three primary destinations: **Okazje**, **Obserwowane**, **Moje zakupy**. Put the parcel and calculator inside the relevant decision flow. Keep raw source searches, rejected offers, ended listings and diagnostics behind secondary links.

The first view shows **up to five eligible opportunities across sources**. Include a concise reason when there are none. Let the user request more. Display the source as metadata; separate Yahoo and Mercari pages should not be required to compare economics. Do not copy the current feed into the new view until identity and costs are trustworthy.

Proposed default row, using illustrative values only:

```text
[actual thumbnail]  Exact model · tested · JP variant
                   Cost to prepare in PL: 260–290 PLN
                   Contribution: 80–110 PLN · evidence: medium
                   Max bid: 4,200 JPY · checked 3 min ago
                   Risk: charger missing
                   [Check listing]  [Details]  [Hide]
```

Details show the original Japanese title, included contents, seller claims and evidence, valuation comparables, full cost scenarios, source time, deadline and max-bid calculation. A prominent discrepancy suppresses the buy suggestion. For auctions, distinguish current bid, buy-now price, forecast and personal maximum; avoid presenting four different “profits” on the collapsed card.

Remove repeated platform/battery badges, duplicated countdowns, “sure profit” language, large prediction prose, permanent storage/ROI ticker and extra marketplace actions from the default card. Display storage only when there are actually owned warehouse items. Retain one primary source action; alternative proxies and price research belong in details. Cart inclusion means planning, not purchased.

Mobile acceptance: at **390×844**, title, cost, conservative contribution and primary action visible without scrolling past the first card; collapsed row ≤240px tall; no page-level horizontal overflow; keyboard-accessible details and visible focus; allow pinch zoom and 200% text sizing. Aim for two useful candidates visible after compact header controls. On desktop, use aligned compact rows or a comparison table. Keep one navigation system per viewport. Modal close/escape, focus restoration and labelled icon controls need explicit checks.

## Documentation cleanup without losing evidence

Keep `REVIEW.md` as the short review entrypoint. Its four linked files contain optional detail and are not touched by the scan. The current README is generated, so hand-editing it for concision would be undone by `main.py`.

When choice 3 is selected, make this coordinated change:

| Current material | Proposed destination/behaviour |
|---|---|
| `README.md` (hourly generated catalogue) | Permanent ≤120-line introduction: purpose, status/limits, app link, setup, commands, current review/queue link |
| README/`YAHOO_AUCTIONS_DEALS.md`/`AUCTION_RADAR.md` overlapping deal tables | One generated `reports/latest.md`, max five qualified candidates and one compact health summary |
| `AUCTION_SNIPING_GUIDE.md` | Short durable buying procedure; per-deal limits live in feed/details, not repeated tables |
| `MYSTERY_LOTS_ANALYSIS.md` | On-demand lot detail; no full duplicate catalogue on each run |
| `MARKET_SALES_HISTORY.md` | Source-event report explicitly separate from owned sales; summaries only after history correction |
| `POLAND_REAL_SALES_AUDIT.md`, `REAL_PROFITABILITY_AUDIT.md` | Retain historical evidence under a dated archive with supersession notice; current facts point to the model/source register |
| JSON and PWA assets | Keep machine feed separate from authored documentation; do not publish private receipts/customer data |

Update generator destinations, relative links, workflow staging, checks and tests together. Keep compatibility stubs for old document links where useful. Do not delete source/history files to make the repo look tidy. Store original observations and publish compact summaries; discuss retention before moving historical data out of Git. The current review only adds notices to the two hand-maintained audits, preserving their contents.

## Numbered choices

### 1. Reliable listing identity and freshness — P0, 3–5 days

**Outcome:** recommendations refer to the actual item at the actual observed price. Addresses F01–F03 and F05.

Separate targets/listings; preserve raw values; match exact type/model/variant/quantity; unknown conditions remain unknown; use explicit availability states and per-listing timestamps; fix expiry and Warsaw timezone handling. Quarantine current suspect records and stop manual calibration scripts writing production observations. Preserve the owner's caps as eligibility rules.

**Acceptance:** all five mismatch examples are rejected; above-cap prices remain unchanged; unavailable sources never become sold; expired auctions stay expired across repeated exports; model changes invalidate valuation/condition; no synthetic/search-target records enter purchasable feeds. Zero known mismatches in a hand-labelled 30-candidate sample.

**Excludes:** fresh category expansion, automated purchases and a general AI classifier. **Dependencies:** none; coordinate safe rendering with 4 before broadening ingestion.

### 2. Evidence-backed Polish resale and contribution — P0, 4–7 days plus evidence collection

**Outcome:** every proposed buy limit explains both expected proceeds and all material costs. Addresses F04, F06 and misleading parts of F07/F08.

Implement [the model](recommendation-model.md): comparable records with provenance, asking/sold separation, channel/account cost profiles, low/base/high scenarios, transparent max-bid solving. Retire “guaranteed” wording, synthetic transaction prices and profit metrics based on market disappearance. Keep image-free parsing labelled as text analysis.

**Acceptance:** no strong recommendation without qualifying evidence; same input yields matching Python/browser amounts to the chosen rounding rule; sell-side fees, repairs, returns and labour affect the result; zero feasible bid is rejected; forecast can exceed budget; every displayed realized figure links to owned settlements (otherwise absent). Worked scenarios and missing-data cases covered.

**Excludes:** invented Polish sale data, universal tax/legal assumptions, new subscription data purchases. **Dependencies:** 1. Owner supplies selling channel/accounting profile before actionable limits; until then output stays scenario/research-only.

### 3. Five useful opportunities and concise documentation — P1, 2–4 days

**Outcome:** decide what to inspect in under two minutes without reading guides. Addresses F10 and documentation parts of F15.

Build the compact view above, details on demand, empty/no-eligible state, stale indicators, hide/save actions, and the documentation migration. Keep Polish UI wording consistent and plain.

**Acceptance:** 390×844 and desktop checks meet the sizing/accessibility criteria; five candidates maximum by default; title/cost/contribution/action visible immediately; no duplicate price narratives; README ≤120 lines and generated shortlist ≤100 lines; next scan preserves authored docs and links. In a timed five-item review, record decision time and errors rather than claiming usability from screenshots alone.

**Excludes:** rebranding, native Android app and framework rewrite. **Dependencies:** 1 + 2 for trustworthy default recommendations; layout can be prototyped independently.

### 4. Safe rendering, consistent storage and meaningful CI — P1, 2–4 days

**Outcome:** inputs cannot execute HTML, failed scans preserve evidence, and passing checks mean what their labels say. Addresses F11–F15.

Escape/render text safely, allowlist link protocols/hosts, unify the finished archive, publish atomically, quarantine corrupt JSON, remove implicit vault writes, pin tested dependencies and test PR/frontend/dependency changes. Keep network scanning separate from deterministic CI. Replace silent conflict resolution with explicit safe failure/retry behaviour. Show source-specific freshness, failure and FX dates; distinguish reference FX from paid FX.

**Acceptance:** local injection probe becomes inert; corrupted input cannot erase history or seed fake outcomes; complete generated output manifest is consistent; missing data fails honestly; mocked 403/429/timeout paths retain last-known data as stale; browser smoke + decision regression tests run without contacting marketplaces; CI does not mutate production data during PR checks.

**Excludes:** backend rewrite, new infrastructure and broad security certification. **Dependencies:** none; update tests alongside 1/2 rather than preserving wrong contracts.

### 5. Selective discovery and alerts — P2, 3–5 days

**Outcome:** surface new qualifying candidates quickly instead of repeatedly rescanning a static list. Addresses F13.

Saved searches by exact model; permitted source adapters; deduplicate listing IDs/reposts; price-drop and newly-qualified alerts; configurable source rate/backoff; digest for lower-priority research. Save an alert event with evidence and max price. Deliver only to an owner-selected channel after separate configuration; this review sends none.

**Acceptance:** new fixture listing found once; duplicates do not alert; stale/mismatched/over-budget candidates never send buy alerts; recheck before notification; opt-out/quiet hours work; pilot records useful-alert precision and response time. Target ≥80% useful alerts over two weeks and a user-set daily cap.

**Excludes:** bypassing platform restrictions, automatic bids, seller outreach and extra categories. **Dependencies:** 1, 2, 4; verify access and realistic polling interval first.

### 6. Purchase-to-resale ledger and learning — P1, 3–5 days

**Outcome:** know whether the system actually makes money in Poland. Addresses F07/F16.

Track planned → bought → warehouse → shipped → received/tested → listed → sold/returned, actual cost allocation, hours, sale settlement and refund events. Model unsold inventory and partial sales of lots. Export a private CSV/JSON backup; publish only deliberate aggregates.

**Acceptance:** no “realized” profit before settlement; returns adjust totals; a five-unit pilot reconciles to receipts/payouts; unsold units remain in capital-at-risk metrics; import/export round trip preserves IDs and numbers. Show prediction error by category without automatically changing thresholds on tiny samples.

**Excludes:** accounting software replacement, publishing personal/customer data or a paid SaaS product. **Dependencies:** 2/4 shared cost/state contracts. Actual purchases remain separate owner decisions.

### 7. Parcel-aware buying and deadlines — P2, 2–4 days

**Outcome:** buy an item only if it improves the actual shipment's economics. Addresses F09 and basket selection in F05.

Marginal freight calculator, actual item weights/dimensions and battery quantities, quote/version dates, individual arrival/deadline tracking, capital budget and category concentration limits. Allow “wait for another item” versus “ship now” only when storage cost and stale availability are considered.

**Acceptance:** weight-tier crossing can turn a candidate into a skip; multi-device lots consume all battery quantities; unknown transport eligibility blocks recommendation; freight allocation sums to parcel invoice; adding an over-budget/loss-making item is never described as optimal. No universal sea-mail exemption.

**Excludes:** carrier booking or packing optimization infrastructure. **Dependencies:** 2 + 6 and current carrier quotes/rules.

### 8. Evidence-based lot breakdown — P3, 3–6 days, access-dependent

**Outcome:** value what can actually be identified and sold in a lot. Addresses F08.

Start with human-confirmed contents and image references. Optional OCR/vision later proposes labels with crop/confidence; corrections remain explicit. Estimate sold/unsold/broken quantities, authenticity/region uncertainty, per-unit listing time and replacement costs. Compare selling together with breaking up the lot.

**Acceptance:** text alone cannot claim visual inspection; uncertain objects carry no confirmed value; no default 30-unit contents; totals reconcile to confirmed quantities; “filler” can have zero/negative contribution; an owner-labelled lot sample measures precision before any purchase recommendation.

**Excludes:** mandatory paid vision integration and blanket positive verdicts for junk. **Dependencies:** 1, 2, 6; pilot only after reliable single-item economics.

### 9. Local-versus-import sourcing comparison — P3, 2–3 days plus evidence

**Outcome:** show when buying the same item in Poland is a better use of money/time.

Compare equivalent condition/contents from permitted local sources or manual candidate entry, domestic delivery, testing, return rights and cash timing against the Japanese landed scenario. Add “skip import” when appropriate.

**Acceptance:** a Japanese low sticker price can lose to a local candidate after full costs; identity/region/condition mismatches cannot be compared as equal; prices carry source/date; evidence remains asking or sold as observed.

**Excludes:** building a new Polish marketplace crawler before a manual comparison proves useful. **Dependencies:** 1 + 2, ideally actual cycle-time data from 6.

## Delivery order and boundaries

Repair the decision inputs and safety first (**1 + 4**). Build honest economics and the concise decision interface next (**2 + 3**). Then run the paper validation and add discovery/outcome tracking (**5 + 6**). Use measured problems to select **7–9**.

Defer more categories, more daily reports, “AI” prose, paid data/model subscriptions, auto-bidding, social/community features, a native app and a SaaS monetization plan. None improves the current product mismatch problem. Existing features such as category filters, a cart, calculator and search links need correction/integration rather than being proposed again as new features.

Owner inputs before real-money validation: capital budget and maximum loss, acceptable handling/repair time, selling channel/accounting profile, product families and purchase horizon. These are not blockers for the completed review, and are not silently set by its illustrative numbers. No new implementation is accepted by this document.
