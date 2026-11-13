# Project review — start here

Reviewed **2026-11-11**, against `bbc7a51`. Goal: buy worthwhile deals in Japan for resale in Poland.

> **Verification, 2026-11-13:** the later "fix F01-F16" commit did not fix what the published feed shows — 1 finding fixed, 10 partial, 5 not fixed. See [the verification report](review/verification-2026-11-13.md).

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

### Switch offer research — 2026-11-11

Owner requested more Switch/Switch Lite offers now and one further scan at 08:00.
The bounded research scanner reads Yahoo search results and rechecks up to 24
Mercari item details per category, excluding Mercari auctions from fixed-price
results. It records actual prices, timestamps, source links, declared defects and
unknown/partial tests. Yahoo full descriptions could not be accessed, so those
records remain explicitly search-result candidates, with no invented closing time.
Results live in [the research report](reports/switch-offers.md) and its JSON sibling;
they are separate from the dashboard's verified listing inputs and resale model.

The requested one-off repeat is scheduled on the existing host for **2026-11-12
08:00 Europe/London (09:00 Europe/Warsaw)**, using user timer
`japan-switch-scan-20261112.timer`. It runs `scan_switch_offers.py --publish`,
which uses an isolated clone and commits/pushes only the two research files.
The timer is persistent across restarts; execution still depends on host/network
availability. Output goes to the same report, not a chat notification.

Previous category commit `e947f64`: [Actions passed](https://github.com/110kc3/japan-deal-watcher/actions/runs/43114057879), checked once this session.
Local verification: **166 tests**, strict audit, and an isolated local-Git publisher
check passed (only research files pushed; staged edits preserved). The enabled
persistent timer was checked for the exact next execution time. New delivery:
[Actions verification pending](https://github.com/110kc3/japan-deal-watcher/actions?query=branch%3Amain);
research/script-only changes do not match this workflow's push paths. The only
remaining accepted action after this delivery is the scheduled morning scan.

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
