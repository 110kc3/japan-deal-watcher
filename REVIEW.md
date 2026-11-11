# Project review — start here

Reviewed **2026-11-11**, against `bbc7a51`. Goal: buy worthwhile deals in Japan for resale in Poland.

**The biggest problem is incorrect product matching.** The feed values PS4 games as a limited console, a Mju Zoom as a Mju-II prime, a silicone cover as a DS, and children's shoes as a PSP. Those recommendations are unreliable.

Clutter: eight reports contain about **47,600 words**; the first mobile card has **208 words and eight actions**. Target: five concise, qualified opportunities with details on demand.

## Recommended choices

**Suggestions, not accepted tasks.** Stable numbers for choices such as `do 1,3`:

1. **Reliable listings:** exact product matching, observed prices, genuine expiry.
2. **Honest profit:** Polish sale evidence, full costs, downside and maximum bid.
3. **Less clutter:** five opportunities, expandable details, short permanent README.
4. **Reliable pipeline:** safe rendering, consistent archives, meaningful tests.
5. **Selective alerts:** new listings and price drops that meet buying criteria.
6. **Resale ledger:** purchases, actual costs, refunds, inventory and realized profit.
7. **Parcel-aware buying:** marginal freight, batteries, budget and deadlines.
8. **Lot assessment:** confirmed contents, unsold stock and handling time.
9. **Local comparison:** check whether buying in Poland beats importing.

Suggested order: **1 + 4 → 2 + 3 → 5 + 6**. Consider 7–9 after the first verified resale cycle.

## Read only what you need

| Document | Purpose |
|---|---|
| [Findings](review/findings.md) | What is wrong, examples, affected code and severity |
| [Recommendation model](review/recommendation-model.md) | Poland economics, evidence rules, buying gates and a validation experiment |
| [Product and roadmap](review/product-and-roadmap.md) | UX, cleanup, effort, dependencies and acceptance for choices 1–9 |
| [Evidence and verification](review/evidence.md) | Reproduction commands, browser observations, current official sources and limits |

## Current work state

### Switch categories — 2026-11-11

Owner-selected scope: separate **Nintendo Switch Lite** and **Nintendo Switch**
categories in **Aukcje** and **Kup teraz**. Implemented filters, source-specific
search links, watchlist/catalogue registration, and calculator planning estimates.
No verified Switch listings were present, so these categories have empty tracked
lists and link to searches; no synthetic offers or resale prices were added.

Local verification: **162 tests**, strict audit, JavaScript syntax checks, and
Chromium at **390×844 / 1440×1000** passed. Browser checks covered the current empty
categories and temporary exported fixtures: separate filters in both tabs, correct
Yahoo/Mercari search queries, battery filtering and Python/browser calculator parity.
The existing staged scan data/report changes remain outside this scoped commit.

Delivery on `main`; [Actions verification pending after push](https://github.com/110kc3/japan-deal-watcher/actions?query=branch%3Amain).
Do not wait for CI; check the delivered commit once next session. No further
implementation task is selected by this addition.

### Earlier review snapshot

Review and proposals complete. **No implementation selected; no profitable resale verified.**

**104 tests and strict audit pass**, but miss the major defects. Browser flows, documentation links and diff checked; limitations are in the evidence record.

Delivery on `main`; [remote verification pending](https://github.com/110kc3/japan-deal-watcher/actions?query=branch%3Amain). Markdown-only changes do not trigger this workflow. Check once next session. Review files survive subsequent scans.
