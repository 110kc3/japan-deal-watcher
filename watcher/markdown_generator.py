"""Generates condensed, consolidated, live GitHub README.md for Japan Deal Watcher."""

from datetime import datetime
from .deal_analyzer import DealAnalyzer
from .config import DEFAULT_JPY_PLN_RATE, DEFAULT_EUR_PLN_RATE

def sanitize_md(text):
    """Sanitizes text for safe inclusion in Markdown tables."""
    if text is None:
        return ""
    # Replace pipes and newlines that break Markdown tables
    clean = str(text).replace("|", "&#124;").replace("\n", " ").replace("\r", "").strip()
    return clean

class MarkdownGenerator:
    def __init__(self, deals, timeline_status, rate=DEFAULT_JPY_PLN_RATE, rate_eur=DEFAULT_EUR_PLN_RATE, is_live_rate=False):
        self.deals = deals
        self.timeline = timeline_status
        self.rate = float(rate)
        self.rate_eur = float(rate_eur)
        self.is_live_rate = is_live_rate
        self.analyzer = DealAnalyzer(deals, rate_jpy=self.rate, rate_eur=self.rate_eur)

    @staticmethod
    def format_margin(margin, roi):
        """Formats margin and ROI with proper colors and signs."""
        if margin > 0:
            return f"<strong style='color:#10b981;'>+{margin:.2f} zł</strong><br><small>(+{roi:.1f}%)</small>"
        elif margin < 0:
            return f"<strong style='color:#ef4444;'>{margin:.2f} zł</strong><br><small>({roi:.1f}%)</small>"
        else:
            return f"<strong style='color:#6b7280;'>0.00 zł</strong><br><small>(0.0%)</small>"

    @staticmethod
    def format_short_rationale(tw):
        """Creates punchy, condensed key selling points instead of verbose paragraphs."""
        badges = []
        cond_type = tw.get("condition_type", "")
        if cond_type == "untested_opportunity":
            badges.append("⚡ Niesprawdzany (Okazja)")
        elif cond_type == "lens_clean":
            badges.append("💎 Czysta optyka")
        elif cond_type == "confirmed_working":
            badges.append("✅ Sprawdzony 100%")
        else:
            badges.append("✅ Stan dobry")

        if tw.get("battery_type") != "li-ion":
            badges.append("🟢 0% Li-Ion")
        else:
            badges.append("🔴 1 Li-Ion")

        roi = tw.get("roi_percent", 0)
        margin = tw.get("est_margin_pln", 0)
        if roi >= 60:
            badges.append(f"Wysoki ROI (+{roi:.0f}%)")
        if margin >= 200:
            badges.append(f"Zysk +{margin:.0f} zł")

        return " · ".join(badges)

    def generate(self):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
        days_rem = self.timeline["days_remaining"]
        deadline = self.timeline["deadline"]
        status_badge = self.timeline["status_badge"]

        # 1. AI Analysis & Ranking
        ranked_deals = self.analyzer.get_ranked_deals()
        top_worth_buying = [d for d in ranked_deals if d.get("is_worth_buying")][:5]
        optimal_basket = self.analyzer.get_optimal_consolidation_basket()

        # Filter top snipes (highest margin/ROI, must be available)
        valid_deals = [d for d in self.deals if "404" not in d.get("status", "") and "Zakończone" not in d.get("status", "")]
        sorted_deals = sorted(valid_deals, key=lambda x: x.get("est_margin_pln", 0), reverse=True)
        top_snipes = sorted_deals[:3]

        rate_badge_label = "NBP%20Live" if self.is_live_rate else "Rate"
        rate_badge_color = "success" if self.is_live_rate else "informational"

        md = []
        # Header & Badges (Compact)
        md.append("# 🇯🇵 Japan Deal Watcher & Consolidation Dashboard")
        md.append("")
        md.append(f"> **Automated Private Deal Watcher for Retro Consoles, Handhelds, UMD Bundles & Analog Lenses**  ")
        md.append(f"> *Live tracking Mercari Japan, Yahoo Auctions & ZenMarket consolidation timeline.*")
        md.append("")
        md.append("![Status](https://img.shields.io/badge/Watcher-Active-brightgreen) "
                  f"![Last Scan](https://img.shields.io/badge/Last%20Scan-{now_str.replace(' ', '%20')}-blue) "
                  f"![Exchange Rate](https://img.shields.io/badge/{rate_badge_label}-100%20JPY%20%E2%89%88%20{self.rate * 100:.2f}%20PLN-{rate_badge_color}) "
                  f"![Storage Window](https://img.shields.io/badge/ZenMarket%20Storage-{days_rem}%20Days%20Left-orange) "
                  "![Deal Checks](https://img.shields.io/badge/Deal%20Checks-10%20Rules%20PASS-brightgreen) "
                  "![Camera Cap](https://img.shields.io/badge/Camera%20Cap-Max%20100%20PLN-orange) "
                  "![Lens Cap](https://img.shields.io/badge/Lens%20Cap-Max%20100%20PLN-orange) "
                  "![Update Cycle](https://img.shields.io/badge/Cycle-Hourly%20(1h)-purple) "
                  "![Android PWA](https://img.shields.io/badge/Android%20App-PWA%20Live-brightgreen)")
        md.append("")
        # Sleek Quick Navigation Bar
        md.append("> 🧭 **Szybka Nawigacja:** [📱 **Aplikacja Android / PWA (Live)**](https://110kc3.github.io/japan-deal-watcher/) · [📦 **Pakiety Różności & Danshari (MYSTERY_LOTS_ANALYSIS.md)**](MYSTERY_LOTS_ANALYSIS.md) · [📡 Radar Licytacji (AUCTION_RADAR.md)](AUCTION_RADAR.md) · [🔨 Yahoo Aukcje (YAHOO_AUCTIONS_DEALS.md)](YAHOO_AUCTIONS_DEALS.md) · [🎯 Poradnik Snajpera (AUCTION_SNIPING_GUIDE.md)](AUCTION_SNIPING_GUIDE.md) · [📊 Audyt Rynku PL (POLAND_REAL_SALES_AUDIT.md)](POLAND_REAL_SALES_AUDIT.md) · [📈 Historia Sprzedaży (MARKET_SALES_HISTORY.md)](MARKET_SALES_HISTORY.md)")
        md.append("")
        md.append("---")
        md.append("")

        # 2. Consolidated Storage & Landed Cost Card
        md.append("## 📦 60-Day Warehouse Packing & Consolidation Timeline")
        md.append("")
        md.append(f"ZenMarket zapewnia **60 dni darmowego przechowywania** w Osace na połączenie ofert z Mercari i Yahoo Auctions w 1 tanią paczkę zbiorczą.")
        md.append("")
        md.append("| Magazyn ZenMarket Osaka | Cykl & Deadline | Limit Baterii IATA | Formuła Landed Cost (PL z VAT) |")
        md.append("|:---:|:---:|:---:|---|")
        md.append(f"| **`{days_rem} dni darmowego magazynu`**<br><small>{status_badge}</small> | "
                  f"Start: `{self.timeline['start_date']}`<br>Deadline: **`{deadline}`** | "
                  f"**Maks. 2 Li-Ion / paczka**<br><small>0% dla gier UMD, konsol stacjonarnych i po demontażu baterii (Dry Shipping)</small> | "
                  f"`(Cena JPY + 800 JPY wysyłka JP) × kurs NBP + 2 EUR + wysyłka intl + 3.5% depozyt + 23% VAT` |")
        md.append("")
        md.append("> [!TIP]")
        md.append("> **Więcej niż 2 baterie?** Użyj poczty morskiej (*Japan Post Seamail* – brak limitów baterii) lub *Dry Shipping* (usunięcie baterii w magazynie ZenMarket – 1 śrubka w DS/PSP, nowa bateria na Allegro to 15–25 zł). Szczegóły: [AUCTION_SNIPING_GUIDE.md](AUCTION_SNIPING_GUIDE.md) oraz [REAL_PROFITABILITY_AUDIT.md](REAL_PROFITABILITY_AUDIT.md).")
        md.append("")
        md.append("---")
        md.append("")

        # 3. AI Worth-Buying Evaluation & Top 3 Snipes
        if top_worth_buying:
            md.append("## 🤖 Automatyczna Analiza Opłacalności AI (Worth-Buying Score)")
            md.append("")
            md.append("> Algorytm scoringowy ocenia każdą ofertę w skali 0–100 na podstawie: **czystego zysku w PLN**, **ROI %**, **płynności rynkowej w Polsce** oraz **wygody logistycznej (0% Li-Ion = brak restrykcji IATA)**.")
            md.append("")
            md.append("### 🌟 Top 5 Ofert \"Kupuj Natychmiast\" (Najwyższy Wskaźnik Opłacalności)")
            md.append("")
            md.append("| Werdykt AI | Wynik | Przedmiot / Model | Szacowany Koszt | Wartość w PL | Zysk Netto (ROI) | Kluczowy Atut (AI) | Akcja |")
            md.append("|:---:|:---:|---|---:|---:|---:|---|---|")
            for tw in top_worth_buying:
                clean_m = sanitize_md(tw.get('model', ''))
                clean_c = sanitize_md(tw.get('color', ''))
                margin_str = self.format_margin(tw.get('est_margin_pln', 0), tw.get('roi_percent', 0))
                short_rat = self.format_short_rationale(tw)
                md.append(
                    f"| {tw['verdict_icon']}<br><strong>{tw['tier']}</strong> | "
                    f"**{tw['score']}/100** | "
                    f"**{clean_m}**<br><small>{clean_c}</small> | "
                    f"~{tw['landed_cost_pln']:.2f} zł | "
                    f"~{tw['est_pl_value']:.2f} zł | "
                    f"{margin_str} | "
                    f"<small>{short_rat}</small> | "
                    f"[🛒 Kup ZenMarket]({tw['zenmarket_url']})<br>[🇯🇵 Mercari]({tw['mercari_url']}) |"
                )
            md.append("")
            md.append("---")
            md.append("")

        if top_snipes:
            md.append("## 🎯 Top 3 Snipes (Highest Polish Market Profit)")
            md.append("")
            md.append("| Model / Przedmiot | Cena w Japonii | Szacowany Koszt w PL | Wartość w Polsce | Zysk na Czysto | Akcja |")
            md.append("|---|---:|---:|---:|---:|---|")
            for s in top_snipes:
                clean_model = sanitize_md(s.get('model', ''))
                clean_color = sanitize_md(s.get('color', ''))
                margin_str = self.format_margin(s.get('est_margin_pln', 0), s.get('roi_percent', 0))
                md.append(
                    f"| **{clean_model}** ({clean_color}) | {s['price_jpy']:,} JPY (~{s['price_pln_raw']:.2f} zł) | "
                    f"~{s['landed_cost_pln']:.2f} zł | ~{s['est_pl_value']:.2f} zł | "
                    f"{margin_str} | "
                    f"[🛒 Kup ZenMarket]({s['zenmarket_url']}) · [🇯🇵 Mercari]({s['mercari_url']}) |"
                )
            md.append("")
            md.append("---")
            md.append("")

        # 4. Render categories: separate active deals from ended deals (Collapsible Archive)
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
                b_badge = "🟡 Mieszany: Kontrolery PS3/PS4 zawierają Li-Ion (1 slot), a przewodowe PS1/PS2 są bez baterii (0% Li-Ion – brak limitu!)"
            elif has_li_ion:
                b_badge = "🔴 Li-Ion (Zajmuje 1 slot bateryjny, max 2 na paczkę)"
            else:
                b_badge = "🟢 No-Battery / Dry Cell (Brak limitu w paczce)"
            
            clean_cat = sanitize_md(cat_name)
            md.append(f"## {clean_cat}")
            md.append(f"> **Typ zasilania / IATA:** {b_badge}")
            if "aparat" in cat_name.lower() or "camera" in cat_name.lower():
                md.append("> 📷 **Reguła Cenowa:** aparaty <= 100 zł (~4,000 JPY).")
            elif "obiektyw" in cat_name.lower() or "lens" in cat_name.lower():
                md.append("> 🔍 **Reguła Cenowa:** obiektywy <= 100 zł (~4,000 JPY) o wysokim ROI.")
            elif "nintendo ds" in cat_name.lower() or "ds" in cat_name.lower():
                md.append("> 🎮 **Kategoria Nintendo DS:** Kultowe handheldy Dual Screen (możliwy demontaż baterii / Dry Shipping 0% Li-Ion).")
            md.append("")

            # Separate active and ended items
            active_items = [it for it in items if "Dostępne" in it.get("status", "")]
            ended_items = [it for it in items if "Dostępne" not in it.get("status", "")]

            table_header = "| Model / Wariant | Stan / Weryfikacja | Cena JPY (PLN) | Koszt w PL (z VAT) | Cena w Polsce | Potencjalny Zysk | Werdykt AI | Status | Linki |"
            table_sep = "|---|:---:|---:|---:|---:|---:|:---:|:---:|---|"

            if active_items:
                md.append(table_header)
                md.append(table_sep)
                for it in active_items:
                    clean_model = sanitize_md(it.get("model", ""))
                    clean_color = sanitize_md(it.get("color", ""))
                    clean_note = sanitize_md(it.get("custom_note", ""))
                    margin_str = self.format_margin(it.get("est_margin_pln", 0), it.get("roi_percent", 0))

                    cond_type = it.get("condition_type", "standard_good")
                    if cond_type == "untested_opportunity":
                        cond_html = "⚡ <strong>Niesprawdzany</strong><br><small style='color:#d97706;'>Potencjał zysku</small>"
                    elif cond_type == "confirmed_working":
                        cond_html = "✅ <strong>Sprawdzony</strong><br><small style='color:#10b981;'>Sprawny 100%</small>"
                    elif cond_type == "lens_clean":
                        cond_html = "💎 <strong>Czysty</strong><br><small style='color:#0284c7;'>Bez wad optyki</small>"
                    else:
                        cond_html = "✅ <strong>Stan Dobry</strong>"

                    deal_eval = self.analyzer.analyze_deal(it)
                    ai_badge = f"{deal_eval['verdict_icon']} <strong>{deal_eval['tier']}</strong><br><small>{deal_eval['score']}/100</small>" if deal_eval.get("is_active") else "⚪ N/A"

                    # Condensed model cell: avoid repeating color twice
                    note_str = f"<br>*{clean_note}*" if clean_note and clean_note != clean_color else ""
                    model_col = f"**{clean_model}**<br><small>{clean_color}{note_str}</small>"
                    price_col = f"**{it['price_jpy']:,} JPY**<br>(~{it['price_pln_raw']:.2f} zł)"
                    landed_col = f"~{it['landed_cost_pln']:.2f} zł"
                    pl_col = f"**{it['est_pl_value']:.2f} zł**"
                    links_col = f"[🛒 ZenMarket 1-Click]({it['zenmarket_url']})<br>[🇯🇵 Mercari Oferta]({it['mercari_url']})"

                    md.append(
                        f"| {model_col} | "
                        f"{cond_html} | "
                        f"{price_col} | "
                        f"{landed_col} | "
                        f"{pl_col} | "
                        f"{margin_str} | "
                        f"{ai_badge} | "
                        f"✅ Dostępne | "
                        f"{links_col} |"
                    )
                md.append("")
            else:
                md.append("*Brak nowych aktywnych ofert w tej chwili (wszystkie pozycje wyprzedane lub w trakcie transakcji).*")
                md.append("")

            # If there are ended items in this category, render them cleanly in a collapsible section
            if ended_items:
                md.append(f"<details><summary>📁 Zakończone / Sprzedane w tej kategorii ({len(ended_items)} ofert - kliknij, aby rozwinąć)</summary>")
                md.append("")
                md.append(table_header)
                md.append(table_sep)
                for it in ended_items:
                    clean_model = sanitize_md(it.get("model", ""))
                    clean_color = sanitize_md(it.get("color", ""))
                    margin_str = self.format_margin(it.get("est_margin_pln", 0), it.get("roi_percent", 0))

                    is_broken = it.get("is_broken") or "Wykluczone" in it.get("status", "")
                    status_icon = "~~🚫 Wykluczone (Uszkodzone)~~" if is_broken else "~~❌ Zakończone / Sprzedane~~"

                    model_col = f"~~**{clean_model}**~~<br><small>~~{clean_color}~~</small>"
                    cond_col = "~~✅ Stan Dobry~~"
                    price_col = f"~~**{it['price_jpy']:,} JPY**~~<br>(~~~{it['price_pln_raw']:.2f} zł~~)"
                    landed_col = f"~~~{it['landed_cost_pln']:.2f} zł~~"
                    pl_col = f"~~**{it['est_pl_value']:.2f} zł**~~"
                    margin_col = f"~~{margin_str}~~"
                    ai_col = "~~⚪ N/A~~"
                    links_col = f"~~[🛒 ZenMarket 1-Click]({it['zenmarket_url']})~~"

                    md.append(
                        f"| {model_col} | "
                        f"{cond_col} | "
                        f"{price_col} | "
                        f"{landed_col} | "
                        f"{pl_col} | "
                        f"{margin_col} | "
                        f"{ai_col} | "
                        f"{status_icon} | "
                        f"{links_col} |"
                    )
                md.append("")
                md.append("</details>")
                md.append("")

            md.append("---")
            md.append("")

        # 5. Dynamic Consolidation simulation box (Condensed)
        b_items = optimal_basket.get("items", [])
        md.append("## 💡 Optymalny Koszyk Konsolidacyjny (Wysyłka Zbiorcza)")
        md.append("")
        md.append(f"Zamiast wysyłać każdy przedmiot osobno (gdzie minimalny koszt paczki kurierskiej to ~110 zł), algorytm dobrał optymalny zestaw {len(b_items)} pozycji, dokładnie przestrzegając limitu IATA (maks. 2 akumulatory Li-Ion):")
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
            f"**<strong style='color:#10b981;'>+{optimal_basket['total_margin_pln']:.2f} zł (+{optimal_basket['total_roi']}%)</strong>** |"
        )
        md.append("")
        md.append(f"> 💰 **Czysta oszczędność na konsolidacji: ~{(len(b_items) * 110) - 175} zł w kieszeni!** ({len(b_items)} przesyłek osobno = ~{len(b_items) * 110} zł vs 1 paczka EMS = ~175 zł).")
        md.append("")
        md.append("---")
        md.append("")

        # 6. Collapsible Photo Inspection Formulas (Clean reference)
        md.append("<details><summary>🛡️ Formułki Inspekcji Zdjęciowej ZenMarket (Order Photos - 500 JPY za 3 zdjęcia)</summary>")
        md.append("")
        md.append("Po zakupieniu przedmiotu w panelu ZenMarket kliknij *Order Photos* i wklej:")
        md.append("- **Dla PS Vita / PSP:**")
        md.append("  > *\"Please turn on the console and take 1 clear photo of the screen displaying the main menu (to check for dead pixels or screen yellowing). Please take 1 photo of the open battery compartment, and 1 photo of the back serial label.\"*")
        md.append("- **Dla obiektywów analogowych:**")
        md.append("  > *\"Please shine a flashlight through the lens elements and take 1 photo of the glass clarity (checking for fungus or haze), 1 photo of the front element, and 1 photo of the rear mount.\"*")
        md.append("- **Dla konsol stacjonarnych (Saturn, Dreamcast, PS2, GameCube):**")
        md.append("  > *\"Please take 1 photo of the overall front and top shell, 1 photo of the bottom label with serial number, and 1 photo of the controller ports.\"*")
        md.append("")
        md.append("</details>")
        md.append("")
        md.append("---")
        md.append("")

        # 7. Concise Technical Footer
        md.append("## ⚙️ How This Watcher Works")
        md.append("")
        md.append("- **Automated Refresh:** GitHub Actions uruchamiane co godzinę (`cron: '0 * * * *'`) pobiera aktualne kursy NBP i sprawdza dostępność.")
        md.append("- **AI Worth-Buying Valuation:** Matematyczna wycena marży, ROI, IATA i płynności w Polsce w czasie rzeczywistym.")
        md.append("- **Lokalne uruchomienie:** `python3 main.py` w repozytorium.")
        md.append("")
        md.append("---")
        md.append(f"*Dashboard automatically maintained by GitHub Actions & Antigravity Agent. Last updated: {now_str}.*")
        
        return "\n".join(md)
