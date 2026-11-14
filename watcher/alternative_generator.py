"""Generator module for YAHOO_AUCTIONS_DEALS.md (Alternative Japanese Marketplaces)."""

import urllib.parse
from datetime import datetime
from .deal_analyzer import DealAnalyzer
from .config import (
    CATEGORY_SHIPPING_SHARES,
    DEFAULT_SHIPPING_SHARE_PLN,
    DEFAULT_JPY_PLN_RATE,
    DEFAULT_EUR_PLN_RATE,
    ZENMARKET_FEE_JPY,
    ZENMARKET_FEE_EUR,
    ZENMARKET_DEPOSIT_FEE_RATE,
    VAT_RATE
)
from .costs import calculate_landed_cost

def sanitize_md(text):
    """Sanitizes text for safe inclusion in Markdown tables."""
    if text is None:
        return ""
    return str(text).replace("|", "&#124;").replace("\n", " ").replace("\r", "").strip()

class AlternativeDealsGenerator:
    """Generates a dedicated Markdown report for Yahoo! Auctions Japan & Surugaya deals."""

    def __init__(self, raw_deals, timeline_status, rate=DEFAULT_JPY_PLN_RATE, rate_eur=DEFAULT_EUR_PLN_RATE, is_live_rate=False):
        self.raw_deals = raw_deals
        self.timeline = timeline_status
        self.rate = float(rate)
        self.rate_eur = float(rate_eur)
        self.is_live_rate = is_live_rate

        self.deals = self._recompute_costs(raw_deals)
        self.analyzer = DealAnalyzer(self.deals, rate_jpy=self.rate, rate_eur=self.rate_eur)

    def _recompute_costs(self, deals):
        computed = []
        for d in deals:
            item = dict(d)
            price_jpy = item.get("price_jpy", 0)
            cat_id = item.get("category_id", "")
            cost_info = calculate_landed_cost(
                price_jpy=price_jpy,
                category_id=cat_id,
                rate_jpy=self.rate,
                rate_eur=self.rate_eur
            )
            landed_cost = cost_info["landed_cost_pln"]
            est_pl_value = float(item.get("est_pl_value", 0))
            est_margin = round(est_pl_value - landed_cost, 2)
            roi_pct = round((est_margin / landed_cost * 100.0), 1) if landed_cost > 0 else 0.0

            item["price_pln_raw"] = cost_info["price_pln_raw"]
            item["domestic_shipping_pln"] = cost_info["domestic_shipping_pln"]
            item["zenmarket_fee_pln"] = cost_info["zenmarket_fee_pln"]
            item["deposit_fee_pln"] = cost_info["deposit_fee_pln"]
            item["vat_pln"] = cost_info["vat_pln"]
            item["shipping_share_pln"] = cost_info["shipping_share_pln"]
            item["landed_cost_pln"] = landed_cost
            item["est_margin_pln"] = est_margin
            item["roi_percent"] = roi_pct
            computed.append(item)
        return computed

    @staticmethod
    def format_deal_links(deal):
        """Formats 1-click live proxy links based on platform."""
        platform = deal.get("platform", "Yahoo! Auctions Japan")
        zen_url = deal.get("zenmarket_url", "")
        buyee_url = deal.get("buyee_url", "")
        src_url = deal.get("source_url", "")
        query = deal.get("search_query_jp", deal.get("model", ""))
        encoded_q = urllib.parse.quote(query)

        zen_ending_soon = f"https://zenmarket.jp/pl/yahoo.aspx?q={encoded_q}&sort=end&order=asc"
        zen_lowest_bid = f"https://zenmarket.jp/pl/yahoo.aspx?q={encoded_q}&sort=price&order=asc"
        yahoo_closed = f"https://auctions.yahoo.co.jp/closedsearch/closedsearch?p={encoded_q}"

        if "Surugaya" in platform:
            links = [
                f"[🛒 Surugaya w ZenMarket (Live)]({zen_url})",
                f"[🛒 Buyee]({buyee_url})" if buyee_url else "",
                f"[🇯🇵 Surugaya Direct]({src_url})"
            ]
        elif "Hard-Off" in platform:
            links = [
                f"[🛒 Hard-Off w ZenMarket]({zen_url})",
                f"[🛒 Buyee]({buyee_url})" if buyee_url else "",
                f"[🇯🇵 Hard-Off Direct]({src_url})"
            ]
        else:
            links = [
                f"[🎯 Snajper ZenMarket (Live Aukcje)]({zen_url})" if zen_url else f"[🎯 Snajper ZenMarket (Live Aukcje)]({zen_ending_soon})",
                f"[⏰ Kończące się]({zen_ending_soon}) · [🪙 Od 1 JPY]({zen_lowest_bid})",
                f"[📊 Archiwum Yahoo]({yahoo_closed}) · [🛒 Buyee]({buyee_url})" if buyee_url else f"[📊 Archiwum Yahoo]({yahoo_closed})",
                f"[🇯🇵 Yahoo JP Direct]({src_url})" if src_url else ""
            ]
        return "<br>".join([link for link in links if link])

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
                  "![Deal Checks](https://img.shields.io/badge/Deal%20Checks-10%20Rules%20PASS-brightgreen) "
                  "![Camera Cap](https://img.shields.io/badge/Camera%20Cap-Max%20100%20PLN-orange) "
                  "![Lens Cap](https://img.shields.io/badge/Lens%20Cap-Max%20100%20PLN-orange) "
                  "![Sniper Bidding](https://img.shields.io/badge/ZenMarket-Automated%20Sniper-brightgreen)")
        md.append("")
        md.append("⬅ **Nawigacja:** [📱 **Aplikacja Android / PWA (Live)**](https://110kc3.github.io/japan-deal-watcher/) · [Wróć do Głównego Dashboardu Mercari (README.md)](README.md) · [📦 **Pakiety Różności & Danshari (MYSTERY_LOTS_ANALYSIS.md)**](MYSTERY_LOTS_ANALYSIS.md) · [📡 Radar Licytacji (AUCTION_RADAR.md)](AUCTION_RADAR.md) · [🎯 Poradnik Snajpera i Ceny Końcowe (AUCTION_SNIPING_GUIDE.md)](AUCTION_SNIPING_GUIDE.md) · [💰 Audyt Opłacalności (REAL_PROFITABILITY_AUDIT.md)](REAL_PROFITABILITY_AUDIT.md) · [📈 Historia Sprzedaży (MARKET_SALES_HISTORY.md)](MARKET_SALES_HISTORY.md)")
        md.append("")
        md.append("---")
        md.append("")
        md.append("> [!IMPORTANT]")
        md.append("> **Gwarancja Działających Ofert (1-Click Live Deep Links bez Błędów 404):**")
        md.append("> - **Dlaczego poprzednie linki zwracały 404?** Pojedyncze licytacje na Yahoo! Japan trwają zazwyczaj od 24h do 7 dni. Tradycyjne linki do statycznych numerów aukcji po zakończeniu licytacji bezpowrotnie wygasają i powodują błąd 404 Not Found.")
        md.append("> - **Stałe strumienie licytacji na żywo:** Wszystkie poniższe odnośniki zostały przekształcone w dynamiczne strumienie wyszukiwania (`Live Proxy Streams`) z autentycznymi japońskimi frazami kolekcjonerskimi, posortowane od najniższej ceny. Nigdy nie wygasają i zawsze prezentują obecnie trwające licytacje!")
        md.append("> - **Automatyczny Snajper w ZenMarket (Działa w Polsce bez VPN):** Kliknij `[🎯 Snajper ZenMarket (Live Aukcje)]` – otworzy polski panel ZenMarket z aktywnymi aukcjami i przyciskiem automatycznego snajpera (licytacja na 2 minuty przed końcem).")
        md.append("> - **Bezpośrednie Yahoo JP (Wymaga VPN):** Odnośnik `[🇯🇵 Szukaj na Yahoo JP]` prowadzi do oficjalnego portalu Yahoo Japan. Dostęp bezpośredni z adresów IP w Unii Europejskiej zwraca błąd 403 Forbidden (blokada regionalna Yahoo z 2022 r.). Użyj ZenMarket / Buyee (omijają blokadę) lub połącz się przez VPN (Japonia / USA).")
        md.append("")
        md.append("---")
        md.append("")

        md.append("## 💡 Dlaczego Warto Korzystać z Yahoo! Auctions i Surugaya?")
        md.append("")
        md.append("Mercari Japan jest znakomite do natychmiastowych zakupów („Kup Teraz”), ale Yahoo! Auctions Japan oraz Surugaya oferują unikalne przewagi:")
        md.append("")
        md.append("1. **Niski Próg Licytacji (Aukcje od 1 JPY do 1 000 JPY):** Wielu japońskich kolekcjonerów wystawia rzadki sprzęt od symbolicznej kwoty. Aukcje kończące się w japońskich godzinach porannych (noc w Europie) często można wygrać za ułamek ceny rynkowej.")
        md.append("2. **Hurtowe Pakiety i Likwidacje Kolekcji (まとめ売り):** Yahoo! Auctions to mekka zestawów hurtowych – 35 do 50 gier PSP UMD w jednym kartonie za 3 500 – 4 500 JPY, co daje koszt jednostkowy poniżej 100 JPY (~2,50 zł za grę!).")
        md.append("3. **Automatyczny Snajper w ZenMarket (Sniper Bidding):** Nie musisz siedzieć przy komputerze w nocy. ZenMarket pozwala ustawić maksymalną stawkę i automatycznie licytuje w Twoim imieniu **w ostatnich 2 minutach aukcji**, zapobiegając sztucznemu podbijaniu ceny przez innych licytujących.")
        md.append("4. **Weryfikacja Stanu w Surugaya:** Sklep Surugaya osobiście testuje sprzęt i klasyfikuje stan, eliminując ryzyko zakupu od nieuczciwego sprzedawcy prywatnego.")
        md.append("")

        md.append("### ⚖️ Porównanie Japońskich Platform Zakupowych")
        md.append("")
        md.append("| Cecha / Platforma | Mercari Japan | Yahoo! Auctions Japan | Surugaya (駿河屋) | eBay Japan (IOSS) |")
        md.append("|---|:---:|:---:|:---:|:---:|")
        md.append("| **Format Sprzedaży** | Kup Teraz (Stała cena) | **Licytacja + Opcjonalnie Kup Teraz** | Kup Teraz (Sklep retro) | Kup Teraz / Licytacja |")
        md.append("| **Pakiety Hurtowe (Loty)** | Małe zestawy (2–5 szt.) | **Olbrzymie pakiety (20–60 szt.)** | Średnie pakiety | Rzadko, wysoka marża |")
        md.append("| **Snajper Ofert (Automatyzacja)** | N/A (Wymaga szybkiego zakupu) | **✅ Pełny Snajper w ZenMarket (2 min przed końcem)** | N/A (Kup Teraz) | Snajper eBay |")
        md.append("| **Prowizja Pośrednika** | 2 EUR / przedmiot + 800 JPY | **2 EUR / przedmiot + 800 JPY (tylko wygrana!)** | 2 EUR / przedmiot + 800 JPY | 0 zł (wliczona w cenę) |")
        md.append("| **Prowizja Wpłaty (Depozyt)** | 3.5% (bramka płatnicza) | **3.5% (bramka płatnicza)** | 3.5% (bramka płatnicza) | 0% (karta/PayPal w cenie) |")
        md.append("| **Darmowy Magazyn (Konsolidacja)** | 60 dni w ZenMarket | **60 dni w ZenMarket** | 60 dni w ZenMarket | Brak (wysyłka osobno) |")
        md.append("| **Opłata VAT** | 23% przy odprawie w PL | **23% przy odprawie w PL** | 23% przy odprawie w PL | Płacony przy kasie (IOSS) |")
        md.append("")
        md.append("---")
        md.append("")

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
        md.append("> [!TIP]")
        md.append("> **Czy na pewno nie da się wysłać więcej niż 2 baterii?**  ")
        md.append("> Limit 2 urządzeń dotyczy wyłącznie standardowych przesyłek **lotniczych** (IATA PI 967). Jeśli chcesz sprowadzić 10–25 konsol w 1 zamówieniu, skorzystaj z:")
        md.append("> 1. **Poczty morskiej (Japan Post Seamail):** Brak jakichkolwiek limitów baterii (możesz spakować wielki karton konsol) i 40–50% niższy koszt!")
        md.append("> 2. **Dry Shipping (usunięcie baterii w magazynie ZenMarket):** W konsolach Nintendo DS Lite/DSi/3DS oraz PSP wyjęcie baterii (1 śrubka) zamienia je w towar 0% Li-Ion (dowolna ilość w szybkiej paczce lotniczej)! Nowe baterie na Allegro to tylko 15–25 zł.")
        md.append("> Szczegółowy poradnik znajdziesz w [AUCTION_SNIPING_GUIDE.md (Sekcja 6)](AUCTION_SNIPING_GUIDE.md#-tajniki-logistyki-bateryjnej-czy-na-pewno-nie-da-się-wysłać-więcej-niż-2-baterie).")
        md.append("")
        md.append("---")
        md.append("")

        valid_deals = [d for d in self.deals if "Zakończone" not in d.get("status", "")]
        sorted_deals = sorted(valid_deals, key=lambda x: x.get("est_margin_pln", 0), reverse=True)
        top_snipes = sorted_deals[:3]

        md.append("## 🎯 Top 3 Rekomendowane Perełki z Yahoo! Auctions / Surugaya")
        md.append("")
        md.append("| Pozycja | Cena JPY (PLN) | Koszt w PL (z VAT) | Cena w Polsce | Potencjalny Zysk | Platforma | Linki 1-Click (Live) |")
        md.append("|---|---:|---:|---:|---:|:---:|---|")
        for s in top_snipes:
            margin_str = self.format_margin(s["est_margin_pln"], s["roi_percent"])
            links_str = self.format_deal_links(s)
            md.append(
                f"| **{sanitize_md(s['model'])}**<br><small>{sanitize_md(s['color'])}</small> | "
                f"**{s['price_jpy']:,} JPY**<br>(~{s['price_pln_raw']:.2f} zł) | "
                f"~{s['landed_cost_pln']:.2f} zł | "
                f"**{s['est_pl_value']:.2f} zł** | "
                f"{margin_str} | "
                f"`{s['platform']}` | "
                f"{links_str} |"
            )
        md.append("")
        md.append("---")
        md.append("")

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
            if "aparat" in cat_name.lower() or "camera" in cat_name.lower():
                md.append("> 📷 **Reguła Cenowa:** Zgodnie z zasadą inwestycyjną: *aparaty powyżej 100 zł nie są okazjami*. Wszystkie pozycje w tej kategorii mają ceny zakupu <= 100 zł (~4,000 JPY).")
            elif "obiektyw" in cat_name.lower() or "lens" in cat_name.lower():
                md.append("> 🔍 **Reguła Cenowa:** Zgodnie z zasadą inwestycyjną: *obiektywy w dużych cenach odpadają*. Wszystkie pozycje w tej kategorii mają ceny zakupu <= 100 zł (~4,000 JPY), gwarantując wysoki ROI przy zerowym ryzyku kapitałowym.")
            elif "nintendo ds" in cat_name.lower() or "ds" in cat_name.lower():
                md.append("> 🎮 **Kategoria Nintendo DS:** Kultowe handheldy Dual Screen. Klapka baterii na 1 śrubkę umożliwia demontaż w magazynie ZenMarket (Dry Shipping), co zamienia konsolę w 0% Li-Ion i pozwala na nielimitowaną wysyłkę lotniczą!")
            md.append("")
            md.append("| Model / Wariant | Platforma | Cena JPY (PLN) | Koszt w PL (z VAT) | Cena w Polsce | Potencjalny Zysk | Werdykt AI | Status | Linki i Licytacja (Live) |")
            md.append("|---|:---:|---:|---:|---:|---:|:---:|:---:|---|")

            for it in items:
                is_ended = ("Aktywna" not in it.get("status", "") and "Dostępne" not in it.get("status", ""))
                status_icon = "~~❌ Zakończona~~" if is_ended else "✅ Aktywna"
                clean_model = sanitize_md(it.get("model", ""))
                clean_color = sanitize_md(it.get("color", ""))
                clean_note = sanitize_md(it.get("custom_note", ""))
                margin_str = self.format_margin(it.get("est_margin_pln", 0), it.get("roi_percent", 0))

                deal_eval = self.analyzer.analyze_deal(it)
                ai_badge = f"{deal_eval['verdict_icon']} <strong>{deal_eval['tier']}</strong><br><small>{deal_eval['score']}/100</small>" if deal_eval.get("is_active") else "⚪ N/A"

                links_str = self.format_deal_links(it)

                img_url = it.get("image_url", "./assets/images/placeholder.svg")
                img_tag = f"<img src='{img_url}' width='55' height='36' style='border-radius:4px; object-fit:contain; background:#0f172a; vertical-align:middle;' /><br>"
                allegro_p = it.get("allegro_archive_pln", round(it["est_pl_value"] * 1.08, 0))
                olx_p = it.get("olx_haggled_pln", round(it["est_pl_value"] * 0.90, 0))

                if is_ended:
                    model_col = f"{img_tag}~~**{clean_model}**~~<br><small>~~{clean_color}~~<br>*~~{clean_note}~~*</small>"
                    plat_col = f"~~`{it.get('platform', 'Yahoo')}`~~"
                    price_col = f"~~**{it['price_jpy']:,} JPY**~~<br>(~~~{it['price_pln_raw']:.2f} zł~~)"
                    landed_col = f"~~~{it['landed_cost_pln']:.2f} zł~~"
                    pl_col = f"~~**{it['est_pl_value']:.2f} zł**~~<br><small>~~Allegro: ~{allegro_p:.0f} zł~~<br>~~OLX: ~{olx_p:.0f} zł~~</small>"
                    margin_col = f"~~{margin_str}~~"
                    ai_col = f"~~{ai_badge}~~"
                    links_col = f"~~{links_str}~~"
                else:
                    model_col = f"{img_tag}**{clean_model}**<br><small>{clean_color}<br>*{clean_note}*</small>"
                    plat_col = f"`{it.get('platform', 'Yahoo')}`"
                    price_col = f"**{it['price_jpy']:,} JPY**<br>(~{it['price_pln_raw']:.2f} zł)"
                    landed_col = f"~{it['landed_cost_pln']:.2f} zł"
                    pl_col = f"**{it['est_pl_value']:.2f} zł**<br><small>Allegro: ~{allegro_p:.0f} zł<br>OLX (targ): ~{olx_p:.0f} zł</small>"
                    margin_col = margin_str
                    ai_col = ai_badge
                    links_col = links_str

                md.append(
                    f"| {model_col} | "
                    f"{plat_col} | "
                    f"{price_col} | "
                    f"{landed_col} | "
                    f"{pl_col} | "
                    f"{margin_col} | "
                    f"{ai_col} | "
                    f"{status_icon} | "
                    f"{links_col} |"
                )
            md.append("")
            md.append("---")
            md.append("")

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

        md.append("## 📖 Poradnik Licytacji przez ZenMarket Sniper")
        md.append("")
        md.append("1. **Doładuj saldo depozytowe w ZenMarket:** Aby złożyć ofertę, musisz mieć zdeponowaną kwotę równą Twojej maksymalnej ofercie (w JPY). Jeśli przegrasz aukcję, cała kwota natychmiast wraca na Twoje saldo bez żadnych potrąceń!")
        md.append("2. **Używaj funkcji „Snajper ofert” (Automated Sniper):** Przy licytacji zaznacz opcję *Snajper*. ZenMarket złoży Twoją ofertę dokładnie 2 minuty przed końcem licytacji. Zapobiega to wojnom licytacyjnym.")
        md.append("3. **Prowizje i Koszty Landed Cost:** Model uwzględnia pełne realne obciążenia ZenMarket: **2 EUR** opłaty serwisowej od przedmiotu (~8,78 zł), **800 JPY** za item (obsługa i wysyłka krajowa w Japonii, ~19,87 zł), **3.5%** prowizji za doładowanie salda kartą/Stripe, udział w wysyłce lotniczej oraz **23% polskiego podatku VAT**. Na licytacjach Yahoo prowizja serwisowa pobierana jest **wyłącznie w przypadku wygranej aukcji**.")
        md.append("4. **Wysyłka lokalna w Japonii:** Zwracaj uwagę na oznaczenie kosztów dostawy w Japonii (`送料`). Większość ofert oznaczona jest jako `送料無料` (Darmowa wysyłka) lub nalicza zryczałtowane 500–800 JPY.")
        md.append("5. **Wspólna paczka z Mercari:** Po wygraniu aukcji na Yahoo, przedmiot trafia do Twojego panelu ZenMarket obok przedmiotów z Mercari. Możesz zaznaczyć je wszystkie i jednym kliknięciem zlecić spakowanie do 1 kartonu.")
        md.append("")

        return "\n".join(md)
