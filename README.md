# Japan Deal Watcher

Automated deal discovery and parcel consolidation engine for sourcing retro gaming consoles, handhelds, and analog optics from Japanese marketplaces (Mercari Japan & Yahoo! Auctions via ZenMarket) with evidence-based Polish resale economics.

## Highlights

- **Strict Identity Matching**: Programmatic rejection of junk listings, empty boxes, mismatched console revisions, and accessories.
- **Landed Cost & Margin Modeling**: Real-time NBP currency conversion, Japanese domestic fees, proxy commission, international freight tiers, VAT, and Polish marketplace fees.
- **Parcel Consolidation**: Optimizes shipments under Avia Small Packet limits (2,000g) while enforcing IATA lithium-ion battery transport safety rules.
- **PWA Dashboard**: Offline-first web application for reviewing live deals, auction closing countdowns, and candidate watchlists.

## Quick Start

```bash
# Run unit test suite (166 tests)
.venv/bin/python -m unittest discover -s tests -q

# Run strict system audit
.venv/bin/python check_deals.py --strict

# Run deal scan and regenerate reports
.venv/bin/python main.py

# Research Switch / Switch Lite offers without changing dashboard observations
.venv/bin/python scripts/scan_switch_offers.py
# Scan and publish only the two research files from an isolated clone
.venv/bin/python scripts/scan_switch_offers.py --publish
```

Switch and Switch Lite category searches are not verified offers and do not imply a price or resale value. Calculator weights and shipping shares are planning estimates, to be replaced with actual parcel data.

## Documentation & Reports

- [Live Web Terminal](https://110kc3.github.io/japan-deal-watcher/)
- [Strategy & Roadmap Review](REVIEW.md)
- [Financial Valuation Model](review/recommendation-model.md)
- [Sniping & Bidding Guide](AUCTION_SNIPING_GUIDE.md)
- [Auction Radar](AUCTION_RADAR.md)
