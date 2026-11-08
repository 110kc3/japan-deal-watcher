"""Generates comprehensive, live GitHub README.md for Japan Deal Watcher."""

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
        self.analyzer = DealAnalyzer(deals)

    @staticmethod
    def format_margin(margin, roi):
        """Formats margin and ROI with proper colors and signs."""
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
        md.append("# 🇯🇵 Japan Deal Watcher & Consolidation Dashboard")
        md.append("")
        md.append(f"> **Automated Private Deal Watcher for Retro Consoles, Handhelds, UMD Bundles & Analog Lenses**  ")
        md.append(f"> *Live tracking Mercari Japan, Yahoo Auctions & ZenMarket consolidation timeline.*")
        md.append("")
        md.append("![Status](https://img.shields.io/badge/Watcher-Active-brightgreen) "
                  f"![Last Scan](https://img.shields.io/badge/Last%20Scan-{now_str.replace(' ', '%20')}-blue) "
                  f"![Exchange Rate](https://img.shields.io/badge/{rate_badge_label}-100%20JPY%20%E2%89%88%20{self.rate * 100:.2f}%20PLN-{rate_badge_color}) "
                  f"![Storage Window](https://img.shields.io/badge/ZenMarket%20Storage-{days_rem}%20Days%20Left-orange) "
                  "![Update Cycle](https://img.shields.io/badge/Cycle-Hourly%20(1h)-purple)")
        md.append("")
        md.append("> 🔨 **Alternatywne rynki:** Sprawdź dedykowany katalog licytacji i ofert ze sklepów retro: [**YAHOO_AUCTIONS_DEALS.md** (Yahoo! Auctions, Surugaya, Hard-Off)](YAHOO_AUCTIONS_DEALS.md)  ")
        md.append("> 📊 **Obsidian Vault:** [2026-11-07-ps-vita-blue-market-report.md](file:///home/borg/docker/obsidian/vault/20-reports/adhoc/2026-11-07-ps-vita-blue-market-report.md)")
        md.append("")
        md.append("---")
        md.append("")
        md.append("## 📦 60-Day Warehouse Packing & Consolidation Timeline")
        md.append("")
        md.append(f"ZenMarket provides **60 days of free warehouse storage** from the moment an item is delivered to Osaka. After 60 days, storage fees incur (50 JPY/item/day).")
        md.append("")
        md.append("| Metric | Status | Details |")
        md.append("|---|---|---|")
        md.append(f"| **Storage Cycle Started** | `{self.timeline['start_date']}` | Initial tracking cycle started |")
        md.append(f"| **Free Storage Deadline** | **`{deadline}`** | Must create & ship package before this date |")
        md.append(f"| **Days Remaining** | **`{days_rem} dni`** | {status_badge} |")
        md.append(f"| **IATA Li-Ion Limit** | **Maks. 2 urządzenia** | Baterie litowe: tylko 2 sztuki na przesyłkę lotniczą! |")
        md.append(f"| **No-Battery Items** | **Bez limitu (0%)** | Gry PSP UMD, Game Boy DMG, WonderSwan (1x AA), konsole stacjonarne |")
        md.append("")

        # Visual progress bar for 60 days
        total_days = 60
        passed = max(0, min(total_days, self.timeline['days_passed']))
        percent_used = int((passed / total_days) * 100)
        filled_blocks = int(passed / 3)
        empty_blocks = 20 - filled_blocks
        bar = "█" * filled_blocks + "░" * empty_blocks
        md.append(f"**Consolidation Window Progress ({percent_used}% passed):**")
        md.append(f"```text\n[{bar}] {passed}/60 Days used ({days_rem} days remaining until {deadline})\n```")
        md.append("")
        md.append("### 💰 Realna Formuła Kalkulacji Kosztów „Landed Cost” w Polsce")
        md.append("")
        md.append("Każda kwota w kolumnie **Szacowany Koszt w PL (z VAT)** zawiera kompletny, zaktualizowany łańcuch opłat:")
        md.append(f"- **Cena zakupu w Japonii:** Przeliczona bezpośrednio po kursie NBP (`100 JPY ≈ {self.rate * 100:.2f} zł`).")
        md.append(f"- **Obsługa i wysyłka krajowa w Japonii (+800 JPY / item):** Koszt dostawy od sprzedawcy do magazynu w Osace (`~{800 * self.rate:.2f} zł`).")
        md.append(f"- **Prowizja ZenMarket (+2.00 EUR / item):** Stała opłata serwisowa za zakup przedmiotu (`~{2.0 * self.rate_eur:.2f} zł`).")
        md.append("- **Udział w przesyłce międzynarodowej:** Koszt transportu w paczce zbiorczej (20–65 zł zależnie od wagi kategorii).")
        md.append("- **Prowizja doładowania salda (+3.5%):** Opłata manipulacyjna bramki płatniczej (karta/Stripe/PayPal) przy zasileniu konta ZenMarket.")
        md.append("- **Polski podatek VAT (+23%):** Należność celno-skarbowa naliczana przy odprawie w Polsce od wartości towaru i przesyłki.")
        md.append("")
        md.append("---")
        md.append("")

        # AI Worth-Buying Evaluation Section
        if top_worth_buying:
            md.append("## 🤖 Automatyczna Analiza Opłacalności AI (Worth-Buying Score)")
            md.append("")
            md.append("> Algorytm scoringowy ocenia każdą ofertę w skali 0–100 na podstawie: **czystego zysku w PLN**, **ROI %**, **płynności rynkowej w Polsce** oraz **wygody logistycznej (0% Li-Ion = brak restrykcji IATA)**.")
            md.append("")
            md.append("### 🌟 Top 5 Ofert \"Kupuj Natychmiast\" (Najwyższy Wskaźnik Opłacalności)")
            md.append("")
            md.append("| Werdykt AI | Wynik | Przedmiot / Model | Szacowany Koszt | Wartość w PL | Zysk Netto (ROI) | Uzasadnienie Zakupu (AI Rationale) | Akcja |")
            md.append("|:---:|:---:|---|---:|---:|---:|---|---|")
            for tw in top_worth_buying:
                clean_m = sanitize_md(tw.get('model', ''))
                clean_c = sanitize_md(tw.get('color', ''))
                margin_str = self.format_margin(tw.get('est_margin_pln', 0), tw.get('roi_percent', 0))
                clean_rat = sanitize_md(tw.get('rationale', ''))
                md.append(
                    f"| {tw['verdict_icon']}<br><strong>{tw['tier']}</strong> | "
                    f"**{tw['score']}/100** | "
                    f"**{clean_m}**<br><small>{clean_c}</small> | "
                    f"~{tw['landed_cost_pln']:.2f} zł | "
                    f"~{tw['est_pl_value']:.2f} zł | "
                    f"{margin_str} | "
                    f"<small>{clean_rat}</small> | "
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

        # Render each category
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
            md.append("")
            md.append("| Model / Wariant | Stan / Weryfikacja | Cena JPY (PLN) | Koszt w PL (z VAT) | Cena w Polsce | Potencjalny Zysk | Werdykt AI | Status | Linki |")
            md.append("|---|:---:|---:|---:|---:|---:|:---:|:---:|---|")
            
            for it in items:
                status_icon = "✅ Dostępne" if "Dostępne" in it.get("status", "") else "❌ Zakończone / 404"
                if it.get("is_broken") or "Wykluczone" in it.get("status", ""):
                    status_icon = "🚫 Wykluczone (Uszkodzone)"
                
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
                elif it.get("is_broken") or cond_type == "broken":
                    cond_html = "❌ <strong>Uszkodzony</strong><br><small style='color:#ef4444;'>Wykluczony</small>"
                else:
                    cond_html = "✅ <strong>Stan Dobry</strong>"

                deal_eval = self.analyzer.analyze_deal(it)
                ai_badge = f"{deal_eval['verdict_icon']} <strong>{deal_eval['tier']}</strong><br><small>{deal_eval['score']}/100</small>" if deal_eval.get("is_active") else "⚪ N/A"

                md.append(
                    f"| **{clean_model}**<br><small>{clean_color}<br>*{clean_note}*</small> | "
                    f"{cond_html} | "
                    f"**{it['price_jpy']:,} JPY**<br>(~{it['price_pln_raw']:.2f} zł) | "
                    f"~{it['landed_cost_pln']:.2f} zł | "
                    f"**{it['est_pl_value']:.2f} zł** | "
                    f"{margin_str} | "
                    f"{ai_badge} | "
                    f"{status_icon} | "
                    f"[🛒 ZenMarket 1-Click]({it['zenmarket_url']})<br>[🇯🇵 Mercari Oferta]({it['mercari_url']}) |"
                )
            md.append("")
            md.append("---")
            md.append("")

        # Dynamic Consolidation simulation box
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
        md.append(f"> **Oszczędność na wysyłce:** {len(b_items)} przesyłek osobno = ~{len(b_items) * 110} zł. Jedna paczka skonsolidowana EMS/Airmail (~2.4 kg) = **~175 zł**.  ")
        md.append(f"> 💰 **Czysta oszczędność na samej logistyce konsolidacyjnej: ~{(len(b_items) * 110) - 175} zł w kieszeni!**")
        md.append("")
        md.append("---")
        md.append("")

        # Inspection cheatsheet
        md.append("## 🛡️ Formułki Inspekcji Zdjęciowej ZenMarket (500 JPY za 3 zdjęcia)")
        md.append("")
        md.append("Po zakupieniu przedmiotu w panelu ZenMarket kliknij *Order Photos* i wklej:")
        md.append("- **Dla PS Vita / PSP:**")
        md.append("  > *\"Please turn on the console and take 1 clear photo of the screen displaying the main menu (to check for dead pixels or screen yellowing). Please take 1 photo of the open battery compartment, and 1 photo of the back serial label.\"*")
        md.append("- **Dla obiektywów analogowych:**")
        md.append("  > *\"Please shine a flashlight through the lens elements and take 1 photo of the glass clarity (checking for fungus or haze), 1 photo of the front element, and 1 photo of the rear mount.\"*")
        md.append("- **Dla konsol stacjonarnych (Saturn, Dreamcast, PS2, GameCube):**")
        md.append("  > *\"Please take 1 photo of the overall front and top shell, 1 photo of the bottom label with serial number, and 1 photo of the controller ports.\"*")
        md.append("")
        md.append("---")
        md.append("")

        # Automation details
        md.append("## ⚙️ How This Watcher Works")
        md.append("")
        md.append("- **Automated Refresh:** GitHub Actions runs every hour (`cron: '0 * * * *'`) and on manual trigger (`workflow_dispatch`).")
        md.append("- **AI Worth-Buying Valuation:** Real-time scoring of margin, ROI, and logistics suitability for each listing.")
        md.append("- **Live Verification:** Queries Mercari Japan directly for price changes, item removal, or sale status.")
        md.append("- **Local Run:**")
        md.append("  ```bash")
        md.append("  python3 main.py")
        md.append("  ```")
        md.append("- **Adding New Items:** Edit `data/watchlist.json` and push to `main`.")
        md.append("")
        md.append("---")
        md.append(f"*Dashboard automatically maintained by GitHub Actions & Antigravity Agent. Last updated: {now_str}.*")
        
        return "\n".join(md)
