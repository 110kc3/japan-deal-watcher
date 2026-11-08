"""Generator module for YAHOO_AUCTIONS_DEALS.md (Alternative Japanese Marketplaces)."""

from datetime import datetime
from .deal_analyzer import DealAnalyzer
from .config import (
    CATEGORY_SHIPPING_SHARES,
    DEFAULT_SHIPPING_SHARE_PLN,
    ZENMARKET_FEE_JPY,
    VAT_RATE
)

def sanitize_md(text):
    """Sanitizes text for safe inclusion in Markdown tables."""
    if text is None:
        return ""
    return str(text).replace("|", "&#124;").replace("\n", " ").replace("\r", "").strip()

class AlternativeDealsGenerator:
    """Generates a dedicated Markdown report for Yahoo! Auctions Japan & Surugaya deals."""

    def __init__(self, raw_deals, timeline_status, rate=0.024832, is_live_rate=False):
        self.raw_deals = raw_deals
        self.timeline = timeline_status
        self.rate = float(rate)
        self.is_live_rate = is_live_rate

        # Re-calculate landed costs with current live rate
        self.deals = self._recompute_costs(raw_deals)
        self.analyzer = DealAnalyzer(self.deals)

    def _recompute_costs(self, deals):
        computed = []
        for d in deals:
            item = dict(d)
            price_jpy = item.get("price_jpy", 0)
            cat_id = item.get("category_id", "")
            shipping_share = CATEGORY_SHIPPING_SHARES.get(cat_id, DEFAULT_SHIPPING_SHARE_PLN)
            price_pln_raw = round(price_jpy * self.rate, 2)

            # (Price + 500 JPY proxy fee) * JPY/PLN * 1.23 VAT + category shipping share
            landed_cost = round(((price_jpy + ZENMARKET_FEE_JPY) * self.rate * (1.0 + VAT_RATE)) + shipping_share, 2)
            est_pl_value = float(item.get("est_pl_value", 0))
            est_margin = round(est_pl_value - landed_cost, 2)
            roi_pct = round((est_margin / landed_cost * 100.0), 1) if landed_cost > 0 else 0.0

            item["price_pln_raw"] = price_pln_raw
            item["shipping_share_pln"] = shipping_share
            item["landed_cost_pln"] = landed_cost
            item["est_margin_pln"] = est_margin
            item["roi_percent"] = roi_pct
            computed.append(item)
        return computed

    @staticmethod
    def format_margin(margin, roi):
        if margin > 0:
            return f"<strong style='color:#10b981;'>+{margin:.2f} zł</strong><br><small>(+{roi:.1f}%)</small>"
        elif margin < 0:
            return f"<strong style='color:#ef4444;'>{margin:.2f} zł</strong><br><small>({roi:.1f}%)</small>"
        else:
            return f"<strong style='color:#6b7280;'>0.00 zł</strong><br><small>(0.0%)</small>"

    def generate(self):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
        days_rem = self.timeline["days_remaining"]
        deadline = self.timeline["deadline"]
        status_badge = self.timeline["status_badge"]

        ranked_deals = self.analyzer.get_ranked_deals()
        optimal_basket = self.analyzer.get_optimal_consolidation_basket()

        rate_badge_label = "NBP%20Live" if self.is_live_rate else "Rate"
        rate_badge_color = "success" if self.is_live_rate else "informational"

        md = []
        md.append("# 🔨 Yahoo! Auctions Japan & Alternative Deals Dashboard")
        md.append("")
        md.append("> **Katalog Alternatywnych Ofert z Yahoo! Japan Auctions (ヤフオク!), Surugaya (駿河屋) i Hard-Off Net Mall**  ")
        md.append("> *Dedykowane źródło licytacji z niskim progiem wejścia, hurtowych lotów gier retro oraz rzadkich wydań konsol i aparatów analogowych.*")
        md.append("")
        md.append("![Platforms](https://img.shields.io/badge/Platforms-Yahoo!%20Auctions%20%7C%20Surugaya%20%7C%20Hard--Off-orange) "
                  f"![Last Scan](https://img.shields.io/badge/Last%20Scan-{now_str.replace(' ', '%20')}-blue) "
                  f"![Exchange Rate](https://img.shields.io/badge/{rate_badge_label}-100%20JPY%20%E2%89%88%20{self.rate * 100:.2f}%20PLN-{rate_badge_color}) "
                  f"![Storage Window](https://img.shields.io/badge/ZenMarket%20Storage-{days_rem}%20Days%20Left-orange) "
                  "![Sniper Bidding](https://img.shields.io/badge/ZenMarket-Automated%20Sniper-brightgreen)")
        md.append("")
        md.append("⬅ **Nawigacja:** [Wróć do Głównego Dashboardu Mercari (README.md)](README.md) · [Kompleksowy Raport Rynkowy w Obsidian](file:///home/borg/docker/obsidian/vault/20-reports/adhoc/2026-11-07-ps-vita-blue-market-report.md)")
        md.append("")
        md.append("---")
        md.append("")

        # Strategic value proposition
        md.append("## 💡 Dlaczego Warto Korzystać z Yahoo! Auctions i Surugaya?")
        md.append("")
        md.append("Mercari Japan jest znakomite do natychmiastowych zakupów („Kup Teraz”), ale Yahoo! Auctions Japan oraz Surugaya oferują unikalne przewagi:")
        md.append("")
        md.append("1. **Niski Próg Licytacji (Aukcje od 1 JPY do 1 000 JPY):** Wielu japońskich kolekcjonerów wystawia rzadki sprzęt od symbolicznej kwoty. Aukcje kończące się w japońskich godzinach porannych (noc w Europie) często można wygrać za ułamek ceny rynkowej.")
        md.append("2. **Hurtowe Pakiety i Likwidacje Kolekcji (まとめ売り):** Yahoo! Auctions to mekka zestawów hurtowych – 35 do 50 gier PSP UMD w jednym kartonie za 3 500 – 4 500 JPY, co daje koszt jednostkowy poniżej 100 JPY (~2,50 zł za grę!).")
        md.append("3. **Automatyczny Snajper w ZenMarket (Sniper Bidding):** Nie musisz siedzieć przy komputerze w nocy. ZenMarket pozwala ustawić maksymalną stawkę i automatycznie licytuje w Twoim imieniu **w ostatnich 2 minutach aukcji**, zapobiegając sztucznemu podbijaniu ceny przez innych licytujących.")
        md.append("4. **Weryfikacja Stanu w Surugaya:** Sklep Surugaya osobiście testuje sprzęt i klasyfikuje stan, eliminując ryzyko zakupu od nieuczciwego sprzedawcy prywatnego.")
        md.append("")

        # Platform comparison table
        md.append("### ⚖️ Porównanie Japońskich Platform Zakupowych")
        md.append("")
        md.append("| Cecha / Platforma | Mercari Japan | Yahoo! Auctions Japan | Surugaya (駿河屋) | eBay Japan (IOSS) |")
        md.append("|---|:---:|:---:|:---:|:---:|")
        md.append("| **Format Sprzedaży** | Kup Teraz (Stała cena) | **Licytacja + Opcjonalnie Kup Teraz** | Kup Teraz (Sklep retro) | Kup Teraz / Licytacja |")
        md.append("| **Pakiety Hurtowe (Loty)** | Małe zestawy (2–5 szt.) | **Olbrzymie pakiety (20–60 szt.)** | Średnie pakiety | Rzadko, wysoka marża |")
        md.append("| **Snajper Ofert (Automatyzacja)** | N/A (Wymaga szybkiego zakupu) | **✅ Pełny Snajper w ZenMarket (2 min przed końcem)** | N/A (Kup Teraz) | Snajper eBay |")
        md.append("| **Prowizja Pośrednika** | 500 JPY / przedmiot | **500 JPY tylko przy wygranej aukcji!** | 500 JPY / zamówienie | 0 zł (wliczona w cenę) |")
        md.append("| **Darmowy Magazyn (Konsolidacja)** | 60 dni w ZenMarket | **60 dni w ZenMarket** | 60 dni w ZenMarket | Brak (wysyłka osobno) |")
        md.append("| **Opłata VAT** | 23% przy odprawie w PL | **23% przy odprawie w PL** | 23% przy odprawie w PL | Płacony przy kasie (IOSS) |")
        md.append("")
        md.append("---")
        md.append("")

        # 60-Day Timeline
        md.append("## 📦 60-Day Warehouse Consolidation Timeline")
        md.append("")
        md.append(f"Wszystkie przedmioty wygrane na Yahoo! Auctions oraz kupione w Surugaya trafiają do wspólnego magazynu **ZenMarket w Osace**. Masz **{days_rem} dni darmowego przechowywania** na połączenie ich z ofertami z Mercari w 1 bezpieczną paczkę.")
        md.append("")
        md.append("| Parametr | Wartość | Uwagi |")
        md.append("|---|---|---|")
        md.append(f"| **Start Konsolidacji** | `{self.timeline['start_date']}` | Początek bieżącego 60-dniowego cyklu |")
        md.append(f"| **Termin Wysyłki (Deadline)** | **`{deadline}`** | Przed tą datą należy zlecić zapakowanie kartonu |")
        md.append(f"| **Pozostały Czas** | **`{days_rem} dni`** | {status_badge} |")
        md.append(f"| **Limit Baterii IATA** | **Maks. 2 Li-Ion na paczkę** | Konsole stacjonarne, gry UMD, aparaty na baterie AA/CR123 = **0% Li-Ion (Bez limitu!)** |")
        md.append("")
        md.append("---")
        md.append("")

        # Top Snipes
        valid_deals = [d for d in self.deals if "Zakończone" not in d.get("status", "")]
        sorted_deals = sorted(valid_deals, key=lambda x: x.get("est_margin_pln", 0), reverse=True)
        top_snipes = sorted_deals[:3]

        md.append("## 🎯 Top 3 Rekomendowane Perełki z Yahoo! Auctions / Surugaya")
        md.append("")
        md.append("| Pozycja | Cena JPY (PLN) | Koszt w PL (z VAT) | Cena w Polsce | Potencjalny Zysk | Platforma | Linki 1-Click |")
        md.append("|---|---:|---:|---:|---:|:---:|---|")
        for s in top_snipes:
            margin_str = self.format_margin(s["est_margin_pln"], s["roi_percent"])
            md.append(
                f"| **{sanitize_md(s['model'])}**<br><small>{sanitize_md(s['color'])}</small> | "
                f"**{s['price_jpy']:,} JPY**<br>(~{s['price_pln_raw']:.2f} zł) | "
                f"~{s['landed_cost_pln']:.2f} zł | "
                f"**{s['est_pl_value']:.2f} zł** | "
                f"{margin_str} | "
                f"`{s['platform']}` | "
                f"[🎯 Snajper ZenMarket]({s['zenmarket_url']})<br>[🇯🇵 Źródło]({s['source_url']}) |"
            )
        md.append("")
        md.append("---")
        md.append("")

        # Category tables
        categories = {}
        for d in self.deals:
            cname = d.get("category_name", "Inne")
            if cname not in categories:
                categories[cname] = []
            categories[cname].append(d)

        for cat_name, items in categories.items():
            has_li_ion = any(it.get("battery_type") == "li-ion" for it in items)
            has_no_bat = any(it.get("battery_type") != "li-ion" for it in items)
            if has_li_ion and has_no_bat:
                b_badge = "🟡 Mieszany: Pozycje bezprzewodowe posiadają Li-Ion (1 slot), a przewodowe/mechaniczne to 0% Li-Ion (brak limitu w paczce!)"
            elif has_li_ion:
                b_badge = "🔴 Li-Ion (Zajmuje 1 slot bateryjny, max 2 na paczkę lotniczą)"
            else:
                b_badge = "🟢 No-Battery / Dry Cell (Brak limitu w paczce lotniczej!)"

            clean_cat = sanitize_md(cat_name)
            md.append(f"## {clean_cat}")
            md.append(f"> **Typ zasilania / IATA:** {b_badge}")
            md.append("")
            md.append("| Model / Wariant | Platforma | Cena JPY (PLN) | Koszt w PL (z VAT) | Cena w Polsce | Potencjalny Zysk | Werdykt AI | Status | Linki i Licytacja |")
            md.append("|---|:---:|---:|---:|---:|---:|:---:|:---:|---|")

            for it in items:
                status_icon = "✅ Aktywna" if "Aktywna" in it.get("status", "") or "Dostępne" in it.get("status", "") else "❌ Zakończona"
                clean_model = sanitize_md(it.get("model", ""))
                clean_color = sanitize_md(it.get("color", ""))
                clean_note = sanitize_md(it.get("custom_note", ""))
                margin_str = self.format_margin(it.get("est_margin_pln", 0), it.get("roi_percent", 0))

                deal_eval = self.analyzer.analyze_deal(it)
                ai_badge = f"{deal_eval['verdict_icon']} <strong>{deal_eval['tier']}</strong><br><small>{deal_eval['score']}/100</small>" if deal_eval.get("is_active") else "⚪ N/A"

                md.append(
                    f"| **{clean_model}**<br><small>{clean_color}<br>*{clean_note}*</small> | "
                    f"`{it.get('platform', 'Yahoo')}` | "
                    f"**{it['price_jpy']:,} JPY**<br>(~{it['price_pln_raw']:.2f} zł) | "
                    f"~{it['landed_cost_pln']:.2f} zł | "
                    f"**{it['est_pl_value']:.2f} zł** | "
                    f"{margin_str} | "
                    f"{ai_badge} | "
                    f"{status_icon} | "
                    f"[🎯 Snajper ZenMarket]({it['zenmarket_url']})<br>[🛒 Buyee Link]({it['buyee_url']})<br>[🇯🇵 Oferta Źródłowa]({it['source_url']}) |"
                )
            md.append("")
            md.append("---")
            md.append("")

        # Consolidation simulation box
        b_items = optimal_basket.get("items", [])
        md.append("## 💡 Optymalny Koszyk Konsolidacyjny (Yahoo! Auctions + Surugaya)")
        md.append("")
        md.append(f"Zestawienie optymalnego kartonu konsolidacyjnego {len(b_items)} pozycji z Yahoo! Auctions i Surugaya przestrzegające ściśle limitu IATA (maks. 2 akumulatory Li-Ion):")
        md.append("")
        md.append("| Skład Paczki Konsolidacyjnej | Baterie Li-Ion | Koszt Zakupu (JPY) | Koszt w PL (z VAT) | Wartość w Polsce | Szacowany Zysk Netto |")
        md.append("|---|:---:|---:|---:|---:|---:|")
        for bi in b_items:
            b_li = "1 (Slot Li-Ion)" if not bi["is_no_battery"] else "0 (Bez limitu)"
            md.append(
                f"| 1× **{sanitize_md(bi['model'])}** ({sanitize_md(bi['color'])}) | {b_li} | "
                f"{bi['price_jpy']:,} JPY (~{bi['price_pln_raw']:.2f} zł) | ~{bi['landed_cost_pln']:.2f} zł | "
                f"~{bi['est_pl_value']:.2f} zł | **+{bi['est_margin_pln']:.2f} zł** |"
            )
        md.append(
            f"| **ŁĄCZNIE W 1 KARTONIE ({optimal_basket['total_items']} poz.)** | "
            f"**{optimal_basket['li_ion_count']} / 2 Li-Ion (100% OK)** | "
            f"**{optimal_basket['total_jpy']:,} JPY** | "
            f"**~{optimal_basket['total_landed_pln']:.2f} zł** | "
            f"**~{optimal_basket['total_est_pln']:.2f} zł** | "
            f"**<strong style='color:#10b981;'>+{optimal_basket['total_margin_pln']:.2f} zł (+{optimal_basket['total_roi']:.1f}%)</strong>** |"
        )
        md.append("")
        md.append("---")
        md.append("")

        # Practical Guide on Sniper Bidding
        md.append("## 📖 Poradnik Licytacji przez ZenMarket Sniper")
        md.append("")
        md.append("1. **Doładuj saldo depozytowe w ZenMarket:** Aby złożyć ofertę, musisz mieć zdeponowaną kwotę równą Twojej maksymalnej ofercie (w JPY). Jeśli przegrasz aukcję, cała kwota natychmiast wraca na Twoje saldo bez żadnych potrąceń!")
        md.append("2. **Używaj funkcji „Snajper ofert” (Automated Sniper):** Przy licytacji zaznacz opcję *Snajper*. ZenMarket złoży Twoją ofertę dokładnie 2 minuty przed końcem licytacji. Zapobiega to wojnom licytacyjnym.")
        md.append("3. **Prowizja 500 JPY:** Prowizja proxy (500 JPY / ~12,40 zł) jest pobierana **wyłącznie w przypadku wygrania aukcji**. Licytowanie na 10 różnych przedmiotach, z których wygrasz 1, kosztuje dokładnie 500 JPY.")
        md.append("4. **Wysyłka lokalna w Japonii:** Zwracaj uwagę na oznaczenie kosztów dostawy w Japonii (`送料`). Większość ofert oznaczona jest jako `送料無料` (Darmowa wysyłka) lub nalicza zryczałtowane 500–800 JPY.")
        md.append("5. **Wspólna paczka z Mercari:** Po wygraniu aukcji na Yahoo, przedmiot trafia do Twojego panelu ZenMarket obok przedmiotów z Mercari. Możesz zaznaczyć je wszystkie i jednym kliknięciem zlecić spakowanie do 1 kartonu.")
        md.append("")

        return "\n".join(md)
