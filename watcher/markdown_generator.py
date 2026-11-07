"""Generates comprehensive, live GitHub README.md for Japan Deal Watcher."""

from datetime import datetime

class MarkdownGenerator:
    def __init__(self, deals, timeline_status, rate=0.024832):
        self.deals = deals
        self.timeline = timeline_status
        self.rate = rate

    def generate(self):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
        days_rem = self.timeline["days_remaining"]
        deadline = self.timeline["deadline"]
        status_badge = self.timeline["status_badge"]

        # Filter top snipes (highest margin/ROI)
        valid_deals = [d for d in self.deals if "404" not in d.get("status", "") and "Zakończone" not in d.get("status", "")]
        sorted_deals = sorted(valid_deals, key=lambda x: x.get("est_margin_pln", 0), reverse=True)
        top_snipes = sorted_deals[:3]

        md = []
        md.append("# 🇯🇵 Japan Deal Watcher & Consolidation Dashboard")
        md.append("")
        md.append(f"> **Automated Private Deal Watcher for Retro Consoles, Handhelds, UMD Bundles & Analog Lenses**  ")
        md.append(f"> *Live tracking Mercari Japan, Yahoo Auctions & ZenMarket consolidation timeline.*")
        md.append("")
        md.append("![Status](https://img.shields.io/badge/Watcher-Active-brightgreen) "
                  f"![Last Scan](https://img.shields.io/badge/Last%20Scan-{now_str.replace(' ', '%20')}-blue) "
                  f"![Exchange Rate](https://img.shields.io/badge/Rate-100%20JPY%20%E2%89%88%202.48%20PLN-informational) "
                  f"![Storage Window](https://img.shields.io/badge/ZenMarket%20Storage-{days_rem}%20Days%20Left-orange)")
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
        md.append("---")
        md.append("")

        md.append("## 🎯 Top 3 Snipes (Highest Polish Market Profit)")
        md.append("")
        md.append("| Model / Przedmiot | Cena w Japonii | Szacowany Koszt w PL | Wartość w Polsce | Zysk na Czysto | Akcja |")
        md.append("|---|---:|---:|---:|---:|---|")
        for s in top_snipes:
            md.append(
                f"| **{s['model']}** ({s['color']}) | {s['price_jpy']:,} JPY (~{s['price_pln_raw']} zł) | "
                f"~{s['landed_cost_pln']} zł | ~{s['est_pl_value']} zł | "
                f"**+{s['est_margin_pln']} zł** (+{s['roi_percent']}%) | "
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
            first_item = items[0]
            b_type = first_item.get("battery_type", "none")
            
            b_badge = "🔴 Li-Ion (Zajmuje 1 slot bateryjny, max 2 na paczkę)" if b_type == "li-ion" else "🟢 No-Battery / Dry Cell (Brak limitu w paczce)"
            
            md.append(f"## {cat_name}")
            md.append(f"> **Typ zasilania / IATA:** {b_badge}")
            md.append("")
            md.append("| Model / Wariant | Cena JPY (PLN) | Koszt w PL (z VAT) | Cena w Polsce | Potencjalny Zysk | Status | Linki |")
            md.append("|---|---:|---:|---:|---:|:---:|---|")
            
            for it in items:
                status_icon = "✅ Dostępne" if "Dostępne" in it.get("status", "") else "❌ Zakończone / 404"
                md.append(
                    f"| **{it['model']}**<br><small>{it['color']}<br>*{it['custom_note']}*</small> | "
                    f"**{it['price_jpy']:,} JPY**<br>(~{it['price_pln_raw']} zł) | "
                    f"~{it['landed_cost_pln']} zł | "
                    f"**{it['est_pl_value']} zł** | "
                    f"<strong style='color:green;'>+{it['est_margin_pln']} zł</strong><br>(+{it['roi_percent']}%) | "
                    f"{status_icon} | "
                    f"[🛒 ZenMarket 1-Click]({it['zenmarket_url']})<br>[🇯🇵 Mercari Oferta]({it['mercari_url']}) |"
                )
            md.append("")
            md.append("---")
            md.append("")

        # Consolidation simulation box
        md.append("## 💡 Symulator Paczki Zbiorczej (Oszczędność na Wysyłce)")
        md.append("")
        md.append("Zamiast wysyłać każdy przedmiot osobno (gdzie minimalny koszt paczki kurierskiej to ~110 zł):")
        md.append("")
        md.append("| Skład Paczki Konsolidacyjnej | Baterie Li-Ion | Koszt Zakupu (JPY) | Szacowany Zysk w Polsce |")
        md.append("|---|:---:|---:|---:|")
        md.append("| 1× **PS Vita Neon Orange** (Slim ZA24) | 1 (Slot 1/2) | 13 333 JPY (~331 zł) | +380 zł |")
        md.append("| 1× **Sony PSP-3000** (Piano Black) | 1 (Slot 2/2) | 7 980 JPY (~198 zł) | +170 zł |")
        md.append("| 1× **Mega Pakiet 20 Gier PSP UMD** | 0 (Bez limitu) | 2 780 JPY (~69 zł) | +330 zł |")
        md.append("| 1× **Obiektyw SMC Pentax-M 50mm f/1.4** | 0 (Bez limitu) | 6 800 JPY (~168 zł) | +210 zł |")
        md.append("| **Łącznie w 1 kartonie transportowym** | **2 / 2 (100% IATA OK)** | **30 893 JPY (~766 zł)** | **+1 090 zł zysku!** |")
        md.append("")
        md.append("> **Oszczędność na wysyłce:** 4 przesyłki osobno = ~440 zł. Jedna paczka zbiorcza FedEx/Airmail (~2.2 kg) = **~175 zł**.  ")
        md.append("> 💰 **Czysta oszczędność na samej logistyce: ~265 zł w kieszeni!**")
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
        md.append("- **Dla konsol stacjonarnych (Saturn, Dreamcast, PS2):**")
        md.append("  > *\"Please take 1 photo of the overall front and top shell, 1 photo of the bottom label with serial number, and 1 photo of the controller ports.\"*")
        md.append("")
        md.append("---")
        md.append("")

        # Automation details
        md.append("## ⚙️ How This Watcher Works")
        md.append("")
        md.append("- **Automated Refresh:** GitHub Actions runs every 6 hours (`cron: '0 */6 * * *'`) and on manual trigger (`workflow_dispatch`).")
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
