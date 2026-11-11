# A useful recommendation for resale in Poland

[Start here](../REVIEW.md) · [Findings](findings.md) · [Roadmap](product-and-roadmap.md)

This is a proposed decision model, not current behaviour. Numerical thresholds below are trial settings, not owner-approved risk limits or verified market prices. The existing camera/lens **100 PLN item-price caps** and PC35AF-M exclusion remain constraints unless changed explicitly.

## Decide whether the item is eligible before ranking it

| Gate | Evidence needed | If missing or failed |
|---|---|---|
| Identity | Seller listing ID and original title; product type; exact model/variant; unit count; included accessories; region/language; important authenticity checks | Research or reject; no inherited template resale value |
| Availability | Successful observation, source timestamp, price type, end time where applicable; error separate from sold | Unknown/stale; no buy recommendation |
| Condition | Seller's exact claim with source excerpt; tested functions; known defects; inspection provenance | Unknown/untested risk case; never default “working” |
| Polish exit value | Comparable evidence for the same product, region, condition and bundle; channel, date and sample size | Asking-price estimate only; no high-confidence recommendation |
| Costs and logistics | Fees, shipping basis, weight/size, battery count and transport eligibility; tax/accounting profile | Cost range or blocked decision, never silent zero |
| Commercial fit | Conservative profit, maximum loss, capital tied up, owner's budget/time constraints | Watch or skip; no need to fill a top-five quota |

Suggested initial freshness targets: 15 minutes for fixed-price purchase candidates, five minutes for near-ending auction candidates, and a fresh source check before any bid/purchase action. These require ingestion improvements; the hourly GitHub job cannot deliver them reliably. If a source does not permit/offer that access, show its actual age and require opening the source. Do not work around access controls.

Use four user-facing outcomes: **Sprawdź i kup do limitu**, **Do sprawdzenia**, **Obserwuj**, **Odrzucone**. The first still means a manually confirmed buying decision. The software should never promise a sale or automatically bid as part of this roadmap.

## Keep evidence types separate

Minimum conceptual records:

| Record | Essential fields |
|---|---|
| Search target | Exact product identifiers, aliases, exclusions, owner cap and enabled sources |
| Listing observation | `source`, `listing_id`, `observed_at`, original title/description, source URL, price/currency/type, shipping payer, quantity, end time, status and parser version |
| Product match | Target ID, observed model/type/region, included items, mismatch reasons, confidence and reviewer |
| Comparable | Product identity, channel, price, currency, condition, quantity, date, URL/document reference, `asking` / `sold_confirmed` / `owner_settlement`, exclusions |
| Valuation | Comparable IDs, date window, sample size, low/base/high proceeds, fees and uncertainty reasons |
| Decision | Observation ID, valuation/model version, cost profile, downside/base results, max bid, eligibility reasons |
| Owned item | Purchase receipt, actual landed costs, test/repair history, listing date, settlement/refund events and current state |

Separate an unavailable source from an unavailable listing. Store original observations unchanged; revised valuations can be recomputed. Every inferred field should identify its source or assumption. A placeholder image is not evidence of the item or condition.

For Polish comparables, start with owner-confirmed sales, then independently verifiable completed transactions. Treat active Allegro/OLX listings as supply/asking-price evidence only. A disappeared listing does not reveal negotiated cash proceeds. Do not create archive prices by multiplying another estimate.

A provisional confidence rule could require **five independent comparable sold observations within 90 days**, matched by region, model, condition and contents. This is a quality gate to test, not a statistical guarantee. Below it, show sample size and low confidence. Sparse collectibles may remain manual research indefinitely. Deduplicate relistings and exclude boxes, accessories, reproductions, broken units and multi-item lots from single working-unit comparisons. Preserve rejected comparables and the reason.

Use a robust median as a base estimate and a conservative lower scenario; report observed range and sample size. A percentile from five observations is not a calibrated confidence interval. Japanese sales can inform acquisition expectations; they cannot substitute for Polish exit evidence.

## Calculate the money the deal can leave

Maintain separate **cash required**, **estimated contribution before income tax**, and **contribution after valuing the owner's time**. Show realized results only after settlement. A VAT-registered accounting profile must handle recoverable input VAT and output VAT consistently; an unknown tax profile is not permission to advertise take-home net profit.

```text
Cash required to acquire and prepare
  = item price at actual funding FX
  + seller-specific Japanese shipping
  + source-specific proxy fee
  + deposit/FX costs (without counting the same spread twice)
  + inspection/removal/repacking/storage charges
  + allocated international freight and insurance
  + applicable duty, import VAT and clearance costs
  + testing, parts and preparation paid in cash

Estimated cash contribution before income tax
  = conservative Polish proceeds
  - acquisition/preparation cash costs
  - channel/payment/promotion fees
  - seller-paid domestic delivery and packing
  - expected incremental refund/return/repair losses

Decision contribution
  = estimated cash contribution
  - handling hours × owner's chosen hourly value
  - cost of capital while purchasing, shipping and waiting to sell
```

The cash view includes cash paid even if some tax is later recoverable. An accounting contribution view subtracts only nonrecoverable costs and uses a consistent net/gross revenue basis. Keep these two views explicit; do not count recoverable import VAT as a permanent expense or ignore sale-side VAT. Exact tariff classification, origin evidence, tax recoverability and business status need the owner's actual profile and appropriate professional confirmation before executable buying limits depend on them. This review does not establish that profile.

For import estimates, use current tariff/clearance inputs for the actual product and shipment. The [Ministry of Finance guide](https://www.podatki.gov.pl/media/eulinfzg/przewodnik-podatkowy-inwestora-podatek-vat.pdf) describes import VAT based on customs value plus duty and relevant additional costs. Do not implement a blanket duty-free assumption, assume Japan is the manufacturing origin, double-charge prepaid VAT, or treat a shipping fee table as a customs ruling.

Maintain dated fee profiles with URLs and account/category assumptions. [ZenMarket's fee page](https://zenmarket.jp/en/fees.aspx) separates service fees, domestic freight, deposit costs and optional services. [Allegro's calculator guidance](https://help.allegro.com/pl/sell/a/jak-obliczamy-prowizje-od-sprzedazy-lL5oexBd7U8) supports category-specific calculations rather than one universal rate. [Allegro Lokalnie](https://allegrolokalnie.pl/o/sprzedaj-teraz) currently lists 4.9% for Electronics and 7.9% elsewhere for its relevant transaction types, but describes the service as for occasional private sellers; do not assume it is the suitable channel for an organized resale business.

Include return/defect allowances based on actual outcomes as they become available. The older claim that cash pickup eliminates complaint liability is unsound: [UOKiK](https://prawakonsumenta.uokik.gov.pl/reklamacja/niezgodnosc/) describes business-seller responsibility for nonconformity. Distinguish distance-contract withdrawal from complaints about defects; payment method alone does not settle either question. These are operating-cost inputs, not a reason to add legal boilerplate to every card.

## A worked example of why gross margin misleads

Illustration only: no particular product or marketplace fee is being quoted. Assume a nonrecoverable-tax cost basis, resale 400 PLN, landed cost 240 PLN, an illustrative 8% selling fee, delivery/packing 15 PLN, parts 20 PLN, expected additional return loss 25 PLN, and half an hour valued at 60 PLN/hour.

| Measure | Base scenario | Downside: sale −15%, landed cost +10% |
|---|---:|---:|
| Sale proceeds | 400.00 | 340.00 |
| Landed cost | 240.00 | 264.00 |
| Selling fee | 32.00 | 27.20 |
| Delivery/packing + parts + return allowance | 60.00 | 60.00 |
| Cash contribution before income tax | **68.00** | **−11.20** |
| Owner time | 30.00 | 30.00 |
| Decision contribution | **38.00** | **−41.20** |

The existing headline calculation would show **+160 PLN**. Under a proposed 75 PLN minimum contribution and nonnegative downside rule, this illustrative deal is skipped. Do not double-count repairs already included in condition-adjusted costs or returns already deducted from proceeds.

## Maximum bid and ordering

Use the same cost engine to solve for the largest bid that meets all chosen constraints. Round **down** to an allowed bid increment; recompute the result after rounding. Reject “no feasible bid”; zero is not a free deal. The price forecast may exceed the budget—show that as a reason to pass.

Provisional trial constraints: base decision contribution at least **75 PLN**, cash ROI at least **25%**, and nonnegative downside decision contribution. Define ROI's denominator as the cash committed to acquiring/preparing the item, not just Japanese purchase price. These defaults are hypotheses and must be editable. Do not enable a personal-loss limit until the owner sets it.

Sort qualified opportunities by conservative contribution, then evidence confidence and time to cash. Offer optional return per capital-month and contribution per work-hour after enough outcome data exists. Show the two main reasons and largest unresolved risk. Avoid another opaque 0–100 score until its calibration adds measurable value.

For parcels, compute **incremental** freight and preparation cost when adding an item to the current parcel. Evaluate full parcel eligibility and landed cost again after every addition. A heavy “filler” that crosses a shipping tier can erase its own margin. Unknown batteries are not zero batteries.

## Validate a narrow strategy before expanding categories

Start by evaluating **two exact product families already covered**, with clearly identifiable models and test procedures. This is an experiment choice, not evidence that a category is profitable. For example, a specified manual lens and a specified tested handheld could provide different logistics profiles; choose only after collecting Polish comparable evidence. Keep existing broader watchlists as opt-in research.

For lenses, distinguish mount, optical defects, aperture and included accessories. For handhelds, verify model/region, language limitations, screens, charging, battery and shell authenticity. Rare editions, untested hardware, Japanese-language game lots and unknown bulk contents need separate assumptions; do not rank them highly merely because their theoretical total value is large.

Proposed validation sequence:

- **Paper stage:** review 30 newly observed candidates over at least two weeks. Label exact match, availability, condition, costs and resale evidence. Require zero known product-type substitutions in the qualified list and at least 90% agreement with human eligibility decisions. Count low/no-deal days honestly.
- **Limited purchase stage, only when separately authorized:** owner sets total budget, per-item exposure and maximum acceptable loss; try at most five units meeting the selected gates. No auto-buying. Reconcile quotes against invoices and keep unsold/returned units in the denominator.
- **Outcome gate:** for at least five settled outcomes, compare predicted and actual landed cost/proceeds, contribution, refund loss, hours and time from payment to cash recovery. Initial targets: median absolute landed-cost error ≤10%, proceeds error ≤15%, positive total contribution after valued labour, and most stock sold within the chosen horizon (trial: 45 days after ready-for-sale). Five outcomes are directional evidence, not proof of scalability.
- **Stop/adjust:** pause category expansion if matching failures recur, profit depends on unsupported resale prices, inventory ages beyond the chosen horizon, or actual contribution is negative. Revise the assumptions before adding more categories or alerts.

Operational metrics are qualified opportunities and decision time; commercial metrics are actual purchases, sold units, realized contribution and capital days. Scanner runs, generated cards, requests/bots and page views are not revenue or evidence of human adoption. No human-use, conversion or revenue dataset was established in this review.
