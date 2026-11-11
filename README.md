# 🇯🇵 Japan Deal Watcher

> **Private Deal Watcher & Consolidation Engine for Japanese Retro Consoles, Handhelds & Analog Optics**  
> Tracks Mercari Japan and Yahoo! Auctions via ZenMarket proxy with evidence-based Polish resale economics.

[![Watcher CI](https://img.shields.io/badge/Audit-Strict%20PASS-brightgreen)](check_deals.py)
[![Unit Tests](https://img.shields.io/badge/Tests-162%20PASS-brightgreen)](tests/)
[![PWA Live](https://img.shields.io/badge/PWA-Webapp%20Live-blue)](https://110kc3.github.io/japan-deal-watcher/)
[![Roadmap](https://img.shields.io/badge/Roadmap-Choices%201--9%20Complete-success)](review/product-and-roadmap.md)

---

## 🎯 Purpose & Core Guarantees

Japan Deal Watcher automates deal discovery, strict authenticity matching, landed cost simulation, and shipping consolidation for sourcing retro gaming gear and cameras from Japan to Poland.

- **Strict Identity Matching (`ProductMatcher`):** Automatically rejects accessories, empty boxes, manuals, mismatched console editions, and zoom vs prime lens traps (F01).
- **Evidence-Based Resale Model (`recommendation_model.py`):** Multi-scenario financial projections (Base, Downside -15% sale / +10% cost, Upside) with transparent max-bid solving against hard hurdle constraints (F04, Choice 2).
- **Physical Lifecycle Ledger (`resale_ledger.py`):** Honest tracking (`planned` → `bought` → `in_warehouse` → `shipped` → `received_tested` → `listed` → `sold`/`returned`). Zero realized profit is claimed prior to actual settlement; returns dynamically adjust capital at risk (F07, Choice 6).
- **Logistics & Safety (`consolidation.py`):** Marginal freight pricing, IATA 2-battery parcel compliance, ZenMarket 60-day warehouse arrival deadlines, and 2,000g Avia Small Packet boundary optimization (F05, F09, Choice 7).
- **Safe Web Rendering & Storage:** Full XSS input escaping, URL allowlisting, atomic JSON persistence, and corrupt data quarantine (F11, F12, Choice 4).

---

## 🧭 Navigation & Reports

- 🌟 **[Latest Opportunities (`reports/latest.md`)](reports/latest.md)** — Filtered Top 5 qualified opportunities with landed costs and max bids.
- 📱 **[Android PWA Web Application](https://110kc3.github.io/japan-deal-watcher/)** — Responsive mobile (390×844) & desktop deal terminal.
- 📋 **[Roadmap & Strategy Review (`REVIEW.md`)](REVIEW.md)** — Engineering choices 1–9 and findings F01–F16.
- 📐 **[Financial Valuation Model (`review/recommendation-model.md`)](review/recommendation-model.md)** — Mathematical specifications and Polish resale model.
- 🎯 **[Sniping Guide (`AUCTION_SNIPING_GUIDE.md`)](AUCTION_SNIPING_GUIDE.md)** — Tactical bid pacing and hard cap rules.
- 📡 **[Auction Radar (`AUCTION_RADAR.md`)](AUCTION_RADAR.md)** — Live auction tracking and closing predictions.
- 📦 **[Mystery Lots Analysis (`MYSTERY_LOTS_ANALYSIS.md`)](MYSTERY_LOTS_ANALYSIS.md)** — Danshari and bundle inventory evaluation.
- 📈 **[Market Sales History (`MARKET_SALES_HISTORY.md`)](MARKET_SALES_HISTORY.md)** — Source-event observations and market intelligence.

---

## 🛠️ Quickstart & Commands

```bash
# 1. Run full test suite (162 tests)
.venv/bin/python -m unittest discover -s tests -v

# 2. Run strict system audit
.venv/bin/python check_deals.py --strict

# 3. Execute deal scan, feeds sync, and report generation
.venv/bin/python main.py
```

---

## ⚙️ Configuration & Policy Limits

**Nintendo Switch Lite** and **Nintendo Switch** have separate filters in both
**Aukcje** (Yahoo) and **Kup teraz** (Mercari), plus category search links through
ZenMarket. Switch covers LCD/OLED models; Lite is separate. Both categories
are registered in `data/watchlist.json` and the exported catalogue. They start with
no tracked listings: add verified Mercari IDs to `tracked_items` or verified Yahoo
records to `data/yahoo_deals.json` using the corresponding category ID
(`nintendo_switch_lite` / `nintendo_switch`). Searches are not verified offers and
do not imply a price or resale value. Calculator weights and shipping shares are
planning estimates, to be replaced with actual parcel data.

| Category / Parameter | Hard Limit / Policy | Enforcement Mechanism |
|---|---|---|
| **Compact Cameras** | Max 100.00 PLN purchase price | `watcher/checks.py` & `ProductMatcher` |
| **Manual Lenses** | Max 100.00 PLN purchase price | `watcher/checks.py` & `ProductMatcher` |
| **IATA Li-Ion Air Parcel** | Max 2 batteries per shipment | `watcher/consolidation.py` & Dry Shipping |
| **ZenMarket Storage** | 60 days free in Osaka warehouse | `watcher/consolidation.py` deadline monitor |
| **Air Parcel Max Weight** | 2,000g (Avia Small Packet limit) | `watcher/consolidation.py` marginal freight |
| **Hurdle Constraint** | Min 75 PLN contribution, 25% cash ROI | `watcher/recommendation_model.py` solver |

---
*Maintained by Japan Deal Watcher Engine. Autonomous hourly review configured.*
