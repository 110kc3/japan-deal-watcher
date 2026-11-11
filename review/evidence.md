# Evidence and verification record

[Start here](../REVIEW.md) · [Findings](findings.md)

Review date: **2026-11-11**. Author: **Codex**. Baseline: `bbc7a511268bb1efa607cc8598a19846877a30dd` on `main`, clean working tree at start. Statements refer to that snapshot unless identified as external policy or a proposal.

## Coverage and boundaries

| Area | Inspected evidence |
|---|---|
| Ingestion and identity | `main.py`, both `scripts/` refresh/calibration utilities, `watcher/fetcher.py`, watchlist and current Yahoo/Mercari records |
| Decision logic | `deal_analyzer.py`, `closure_predictor.py`, `checks.py`, `market_queries.py`, search stream configuration |
| Import/parcel economics | `config.py`, `costs.py`, `consolidation.py`, `currency.py`, browser calculator/cart |
| History and lots | Both trackers, history generator, lot inspector and `inspect_lot.py`; source versus exported archives |
| Output and clutter | Markdown generators, eight root reports, exporter, PWA HTML/CSS/JS/service worker/manifest |
| Reliability and testing | Workflow, dependency declaration, Git history, 104 tests, strict audit and deterministic defect probes |
| Runtime interface | Local Chromium: phone/desktop, four feed tabs, calculator/cart/search and harmless rendering-injection probe |
| External assumptions | Official ZenMarket, Japan Post, Allegro, UOKiK and Ministry of Finance material below |

This is a product/engineering/business-model review, not certification of every external listing, tax status or production service. No market-wide sale-price dataset, owner purchase receipts or Polish payout records were provided or verified. Direct browser-source retrieval of the two leading Mercari item pages was unavailable; identity findings use the repository's captured seller titles. No marketplace purchase, bid, message or marketplace-account change was performed.

The scheduled scanner and mutation scripts were not executed: they overwrite data/reports and some fixed-path personal reports. Baseline tests and strict audit ran in an isolated Git archive. Browser work used that local snapshot; it does not prove the current hosted Pages build, native Android installation or all offline behaviour.

## Baseline observations

| Observation | Result |
|---|---|
| Tracked files before review | 82 |
| Root reports before review | Eight; 609,345 bytes; 47,610 whitespace-delimited words (HTML/table tokens included) |
| Watchlist | 13 categories / 99 items |
| Current Mercari dataset | 99 records: 59 available, 17 transaction-in-progress, 14 broken exclusions, nine 404s |
| Raw alternative dataset | 73 records: 71 active-auction-labelled, two Surugaya fixed-price-labelled |
| Exported feed | 73 auctions, 59 Mercari, 26 search streams, eight finished records |
| Conflicting Yahoo prices | 68 records with `price_jpy != current_price_jpy` |
| Past raw end times at feed generation | 54; all 54 IDs still in active exported auctions |
| Sales history | 358 tracked identities; 188 sales entries: 54 404s, 18 broken exclusions, 11 in-progress, 105 sold-labelled |
| Finished archives | `data/finished_auctions.json`: 62; `docs/data/finished_auctions.json`: eight |
| Item provenance | No per-listing fetched/verified/observed timestamps or confidence fields found in current raw datasets; `source_url` exists in alternatives |
| Repository visibility | GitHub reports public, despite README's private-watcher wording |

Counts are snapshot facts, not live purchasing inventory. A summary “generated at” time is not a source verification time.

## Checks actually run

| Check | Result and interpretation |
|---|---|
| Python 3.11.2 / installed `mercapi` 0.5.0 | Matches workflow's Python 3.11 baseline; dependency declaration allows unbounded newer versions |
| `.venv/bin/python -m unittest discover -s tests -q` | **104 passed**, 0.136 seconds; success does not validate market evidence or matching |
| `.venv/bin/python check_deals.py --strict` | Exit 0; ten named system checks plus camera/lens/defect summaries; its live/link/realized labels overstate what is tested |
| Node 18.20.4 `--check docs/app.js` and `docs/sw.js` | Both exit 0; syntax only |
| Four feed tabs at 390×844 and 1440×900 | Rendered without uncaught JavaScript errors in the checked flows |
| Calculator, cart and search at phone width | Calculation rendered; adding a hypothetical calculation updated cart count to one, persisted across reload and opened in cart modal; unmatched search showed empty state |
| Harmless local model-field injection | `window.__reviewInjected` became true; demonstrates unsafe HTML interpolation, not a production compromise |
| Documentation closeout | Relative Markdown targets, recommendation-number consistency, snapshot metrics and `git diff --check` checked before commit |

Browser tooling: temporary Playwright Python 1.65.0 installation outside the repo and existing Chromium build `chromium-1248`. Service workers blocked for deterministic UI/injection probes. External image loading differed between captures; images were not a pass/fail condition. Screenshots were inspected locally; only their measurements and conclusions are retained in Markdown.

| Layout measurement | Phone 390×844 | Desktop 1440×900 |
|---|---:|---:|
| Rendered initial cards | 73 | 73 |
| First card starts at y | 374px | 292px |
| First card height | 1,375px | 1,115px |
| First card words | 208 | 208 |
| First card anchors/buttons | 8 | 8 |
| Page-level horizontal overflow | Yes (626px scroll width) | No |

The initial phone viewport displays navigation, filters, image and badges; the first title and profit require further scrolling. Desktop repetition is also substantial. `maximum-scale=1.0, user-scalable=no` and missing modal accessibility semantics are source-inspection findings; a complete assistive-technology audit was not performed.

### Reproduce the baseline checks safely

From the repository root, using its existing virtualenv:

```bash
set -euo pipefail
review_python="$PWD/.venv/bin/python"
review_dir="$(mktemp -d /tmp/jdw-review.XXXXXX)"
git archive bbc7a511268bb1efa607cc8598a19846877a30dd | tar -x -C "$review_dir"
cd "$review_dir"
"$review_python" -m unittest discover -s tests -q
"$review_python" check_deals.py --strict
node --check docs/app.js
node --check docs/sw.js
```

No tests were added for the documentation changes. Existing tests were run to evaluate the project's baseline. Fixing the defects needs new behavioural regression tests, listed in the roadmap.

### Small deterministic defect probes

Run in the isolated copy. The history example writes only to a temporary directory:

```python
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from watcher.time_utils import calculate_auction_timing
from watcher.fetcher import classify_condition
from watcher.history_tracker import HistoryTracker
from watcher.lot_vision_inspector import LotVisionInspector

timing = calculate_auction_timing(
    {"ends_at": "2026-11-10 12:00 UTC", "time_remaining_minutes": 60},
    datetime(2026, 11, 11, 12, tzinfo=timezone.utc),
)
print(timing["ends_at"])  # 2026-11-11 13:00 UTC: resurrected
print(classify_condition("")["is_working"])  # True without evidence
with TemporaryDirectory() as tmp:
    history = HistoryTracker(Path(tmp) / "history.json")
    history.record_scan([{"id": "review-error", "status": "Błąd połączenia"}])
    print(len(history.data["sales_log"]))  # 1: error recorded as sale
inspection = LotVisionInspector.inspect_lot_photo_contents({"model": "Pokemon emerald"})
print(inspection["inspected"], inspection["total_items_spotted"])
# True, 30: no image supplied
```

Browser reproduction: serve the isolated `docs/` with `python3 -m http.server --bind 127.0.0.1 --directory docs 8765`, open localhost at the two viewport sizes, wait for cards and measure:

```javascript
const card = document.querySelector('.deal-card');
({
  height: card.getBoundingClientRect().height,
  words: card.innerText.split(/\s+/).length,
  actions: card.querySelectorAll('a,button').length,
  overflow: document.documentElement.scrollWidth > innerWidth
});
```

Exact counts depend on source snapshot, time and font rendering. The injection test intercepted the local `data/deals.json` response and changed one auction's model to a harmless image element whose error handler set a test boolean. It never wrote to a live feed or accessed third-party accounts.

## Official source register

Checked **2026-11-11**. Policies can change; refresh them before implementing live fee/shipping profiles. These sources validate operating rules, not product resale prices.

| Source | What it supports / limitation |
|---|---|
| [ZenMarket fees](https://zenmarket.jp/en/fees.aspx) | Platform-specific JPY service fees; seller-dependent domestic freight; payment-method-dependent deposits; 60-day storage policy; paid photo/disposal options. Not a quote for a particular parcel. |
| [Japan Post restrictions](https://www.post.japanpost.jp/service/send/oversea/attention/restriction/index_en.html) | Dangerous-goods restrictions apply even to sea mail; battery exceptions have conditions. |
| [Japan Post battery conditions](https://www.post.japanpost.jp/service/send/oversea/attention/restriction/restriction02_en.pdf?210226=) | Installed batteries, capacity, quantity and destination requirements; four cells/two assembled batteries distinction. Document's destination table dated 2025-08-22; obtain current route confirmation. |
| [Allegro archive closure notice](https://allegro.pl/pomoc/aktualnosci/zamkniemy-archiwum-allegro-O36m6egKPcm) | Published 2025-07-17: announced March 2026 closure and earlier redirects. Does not supply current sold-price observations. |
| [Allegro sales commission](https://help.allegro.com/pl/sell/a/jak-obliczamy-prowizje-od-sprzedazy-lL5oexBd7U8) | Fee depends on category/price and delivery circumstances; use calculator/API for the actual listing. |
| [Allegro Lokalnie selling information](https://allegrolokalnie.pl/o/sprzedaj-teraz) | Distinct electronics/other-category fees and occasional-private-seller positioning. Does not authorize a business to use a private account. |
| [UOKiK nonconformity](https://prawakonsumenta.uokik.gov.pl/reklamacja/niezgodnosc/) | Business-seller complaint responsibility; contradicts blanket “cash pickup means zero complaint risk.” |
| [EU used-goods consumer rights](https://europa.eu/youreurope/citizens/consumers/shopping/shopping-consumer-rights/index_pl.htm) | Distinguishes professional/private sellers and used goods; not an individualized determination of the owner's status. |
| [Ministry of Finance VAT guide](https://www.podatki.gov.pl/media/eulinfzg/przewodnik-podatkowy-inwestora-podatek-vat.pdf) | Official indexed excerpt describes customs-value/duty/additional-cost basis. Direct PDF retrieval failed in the browsing tool; precise item-specific tax treatment remains unverified. |

Older `post.japanpost.jp/int/...` battery PDF links returned 404; the current linked document above was retrieved successfully. Mercari source pages were not retrievable through the browsing tool, so no claim of live item verification is made. Business-status, tariff, customer-rights and accounting inputs remain conditional; there is no blanket “zero risk” resale channel.

## CI and delivery record

The latest Actions run visible at review start was [43003870061](https://github.com/110kc3/japan-deal-watcher/actions/runs/43003870061), completed successfully for **`4d4988e`**, created 2026-11-11 10:28 UTC. It is not proof for baseline `bbc7a51` or the review commit. Baseline local verification is recorded above.

The existing workflow has hourly/manual triggers and path-limited pushes to `main`; no PR trigger. A Markdown-only review does not match its push paths. Review push verification remains **pending** at [branch Actions](https://github.com/110kc3/japan-deal-watcher/actions?query=branch%3Amain); no waiting/polling after push. Commit SHA is reported in the delivery message rather than creating a recursive documentation commit.

The repository had no canonical accepted queue or local instruction mirrors. `REVIEW.md` records completion of this review and the absence of accepted implementation tasks. These proposals do not authorize running calibration, buying stock or changing the deployment.
