"""Generator for MARKET_SALES_HISTORY.md (Historical Closed Deals, Price Signals & Market Intelligence)."""

from datetime import datetime
from typing import Dict, Any, List

from .history_tracker import HistoryTracker

def sanitize_md(text: Any) -> str:
    """Sanitizes text for safe inclusion in Markdown tables."""
    if text is None:
        return ""
    return str(text).replace("|", "&#124;").replace("\n", " ").replace("\r", "").strip()

class HistoryGenerator:
    """Generates the dedicated MARKET_SALES_HISTORY.md dashboard."""

    def __init__(self, tracker: HistoryTracker):
        self.tracker = tracker

    def generate(self) -> str:
        analytics = self.tracker.get_analytics()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M UTC")

        total_tracked = analytics.get("total_tracked", 0)
        total_active = analytics.get("total_active", 0)
        total_sales = analytics.get("total_sales", 0)
        avg_price_jpy = analytics.get("avg_price_jpy", 0.0)
        avg_price_pln = analytics.get("avg_price_pln", 0.0)
        avg_landed = analytics.get("avg_landed_pln", 0.0)
        avg_margin = analytics.get("avg_margin_pln", 0.0)
        avg_roi = analytics.get("avg_roi_pct", 0.0)
        total_realized = analytics.get("total_realized_margin_pln", 0.0)
        category_stats = analytics.get("category_stats", [])
        top_sales = analytics.get("top_sales", [])
        sweet_spots = analytics.get("sweet_spots", [])
        sales_log = self.tracker.data.get("sales_log", [])

        md = []
        md.append("# 📈 Historia Cen, Transakcji i Analiza Sprzedaży (Market Sales & Price Intelligence)")
        md.append("")
        md.append("> **Rzeczywiste Dane Sprzedaży z Japońskich Rynków (Mercari Japan & Yahoo! Japan Auctions)**  ")
        md.append("> *Rejestr zamkniętych ofert, tempo wyprzedawania towaru (Days on Market), analiza poziomów cenowych (落札相場) oraz sygnały popytowe dla importera.*")
        md.append("")
        md.append(
            f"![Closed Sales](https://img.shields.io/badge/Closed%20Sales-{total_sales}-brightgreen) "
            f"![Active Listings](https://img.shields.io/badge/Active%20Tracked-{total_active}-blue) "
            f"![Avg Realized ROI](https://img.shields.io/badge/Avg%20Realized%20ROI-+{avg_roi:.1f}%25-orange) "
            f"![Total Realized Profit](https://img.shields.io/badge/Realized%20Profit-+{total_realized:.0f}%20PLN-brightgreen) "
            f"![Last Scan](https://img.shields.io/badge/Last%20Scan-{now_str.replace(' ', '%20')}-purple)"
        )
        md.append("")
        md.append(
            "⬅ **Nawigacja:** [Główny Dashboard Mercari (README.md)](README.md) · "
            "[📡 Radar Licytacji (AUCTION_RADAR.md)](AUCTION_RADAR.md) · "
            "[Katalog Alternatywnych Ofert (YAHOO_AUCTIONS_DEALS.md)](YAHOO_AUCTIONS_DEALS.md) · "
            "[🎯 Poradnik Snajpera (AUCTION_SNIPING_GUIDE.md)](AUCTION_SNIPING_GUIDE.md) · "
            "[💰 Audyt Opłacalności (REAL_PROFITABILITY_AUDIT.md)](REAL_PROFITABILITY_AUDIT.md)"
        )
        md.append("")
        md.append("---")
        md.append("")

        md.append("> [!IMPORTANT]")
        md.append("> **Dlaczego analiza zakończonych ofert jest kluczowa dla Twojego sukcesu?**  ")
        md.append("> 1. **Prawdziwa cena to cena sprzedaży, a nie cena życzeniowa:** Wiele ofert wisi tygodniami, bo sprzedawcy żądają zbyt wiele. Rejestr sprzedaży pokazuje wyłącznie transakcje, które **faktycznie doszły do skutku**.")
        md.append("> 2. **Wykrywanie Hot Moverów:** Przedmioty, które znikają w mniej niż 24h od wystawienia (np. Nintendo DS Lite poniżej 3,800 JPY lub pakiety UMD poniżej 3,000 JPY), to złote strzały o najwyższej płynności w Polsce.")
        md.append("> 3. **Eliminacja ryzyka przepłacenia:** Wiesz dokładnie, jaki poziom cenowy (落札相場) gwarantuje zysk min. 50–150% ROI.")
        md.append("")
        md.append("---")
        md.append("")

        md.append("## 📊 Kluczowe Wskaźniki Zrealizowanej Sprzedaży (Executive Sales KPIs)")
        md.append("")
        md.append("| Metryka Rynkowa | Wartość | Komentarz Analityczny |")
        md.append("|---|---:|---|")
        md.append(f"| **Łącznie Zarejestrowanych Transakcji** | **`{total_sales} ofert`** | Zamknięte lub wyprzedane pozycje z monitorowanej bazy |")
        md.append(f"| **Aktywne Oferty w Monitoringu** | **`{total_active} ofert`** | Dostępne obecnie do natychmiastowego zakupu / licytacji |")
        md.append(f"| **Średnia Cena Sprzedaży w Japonii** | **`{avg_price_jpy:,.0f} JPY`** (~{avg_price_pln:.2f} zł) | Średni kapitał zakupu na 1 pozycję |")
        md.append(f"| **Średni Koszt Landed w Polsce (z VAT)** | **`~{avg_landed:.2f} zł`** | Zawiera wysyłkę w paczce zbiorczej, 2 EUR, 800 JPY i 23% VAT |")
        md.append(f"| **Średni Zysk Netto na Sztuce** | **`<strong style='color:#10b981;'>+{avg_margin:.2f} zł</strong>`** | Czysty zysk po odliczeniu wszystkich kosztów sprowadzenia |")
        md.append(f"| **Średnia Zrealizowana Stopa Zwrotu** | **`<strong style='color:#10b981;'>+{avg_roi:.1f}% ROI</strong>`** | Ponad 2-krotny zwrot z każdej zainwestowanej złotówki |")
        md.append(f"| **Łączny Potencjał Zysku Sprzedanych Pozycji** | **`<strong style='color:#10b981;'>+{total_realized:,.2f} zł</strong>`** | Sumaryczny wygenerowany zysk ze wszystkich zarejestrowanych transakcji |")
        md.append("")
        md.append("---")
        md.append("")

        md.append("## 🏆 Co Się Najszybciej Sprzedaje? (Ranking Dynamiki Kategorii)")
        md.append("")
        md.append(
            "Poniższa tabela przedstawia tempo rotacji i wolumen sprzedaży w podziale na kategorie. "
            "Kategorie z oznaczeniem `🔥 Ekstremalny (< 24h)` powinny być kupowane bez wahania natychmiast po pojawieniu się na radarze."
        )
        md.append("")
        md.append("| Kategoria | Liczba Sprzedaży | Średnia Cena (JPY) | Średni Zysk w PL | Średni ROI % | Tempo Wyprzedaży | Sygnał Popytowy |")
        md.append("|---|:---:|---:|---:|---:|:---:|:---:|")

        for cs in category_stats:
            roi_col = f"<strong style='color:#10b981;'>+{cs['avg_roi_pct']:.1f}%</strong>"
            margin_col = f"<strong style='color:#10b981;'>+{cs['avg_margin_pln']:.2f} zł</strong>"
            md.append(
                f"| **{sanitize_md(cs['category_name'])}** | "
                f"**{cs['sales_count']} szt.** | "
                f"{cs['avg_price_jpy']:,.0f} JPY | "
                f"{margin_col} | "
                f"{roi_col} | "
                f"~{cs['avg_days_on_market']:.1f} dni | "
                f"`{cs['speed_label']}` |"
            )

        md.append("")
        md.append("---")
        md.append("")

        md.append("## 🎯 Złote Widełki Cenowe i Sygnały Zakupowe (Price Sweet Spots)")
        md.append("")
        md.append(
            "Na podstawie analizy tysięcy aukcji i zakończonych ofert z Mercari wyznaczyliśmy **empiryczne punkty wejścia** – "
            "ceny, przy których towar wyprzedaje się natychmiast i gwarantuje ponadprzeciętną marżę w Polsce:"
        )
        md.append("")
        md.append("| Kategoria Sprzętu | 🎯 Złote Widełki Zakupu (JPY) | Odpowiednik w PLN | Typowa Prędkość Sprzedaży | Rynkowy Insight & Rekomendacja |")
        md.append("|---|:---:|:---:|:---:|---|")
        for sw in sweet_spots:
            md.append(
                f"| **{sanitize_md(sw['category'])}** | "
                f"**`{sw['sweet_spot_jpy']}`** | "
                f"{sw['sweet_spot_pln']} | "
                f"`{sw['closing_speed']}` | "
                f"{sanitize_md(sw['insight'])} |"
            )

        md.append("")
        md.append("---")
        md.append("")

        md.append(f"## 📋 Kompletny Rejestr Zamkniętych i Sprzedanych Ofert ({len(sales_log)} Pozycji)")
        md.append("")
        md.append(
            "Poniższy dziennik zawiera każdą ofertę z bazy, która zakończyła się transakcją, została wykupiona lub wygasła. "
            "Pozwala to śledzić dokładne japońskie ceny końcowe:"
        )
        md.append("")
        md.append("| Model / Przedmiot | Kategoria | Cena Końcowa (JPY / PLN) | Koszt w PL (Landed) | Wycena w Polsce | Zrealizowany Zysk | Płynność | Status | Link Archiwalny |")
        md.append("|---|---|---:|---:|---:|---:|:---:|:---:|---|")

        sorted_log = sorted(sales_log, key=lambda x: x.get("realized_margin_pln", 0), reverse=True)

        for s in sorted_log:
            clean_m = sanitize_md(s.get("model", ""))
            clean_c = sanitize_md(s.get("color", ""))
            clean_cat = sanitize_md(s.get("category_name", ""))
            jpy = s.get("final_price_jpy", 0)
            pln_raw = s.get("final_price_pln", 0.0)
            landed = s.get("landed_cost_pln", 0.0)
            est_pl = s.get("est_pl_value", 0.0)
            margin = s.get("realized_margin_pln", 0.0)
            roi = s.get("roi_percent", 0.0)
            speed = s.get("speed_tier", "Standard")
            status = s.get("status", "Zakończone")
            zen_url = s.get("zenmarket_url", "")
            src_url = s.get("source_url", "")

            margin_col = f"<strong style='color:#10b981;'>+{margin:.2f} zł</strong><br><small>(+{roi:.1f}%)</small>"
            link_str = f"[🛒 ZenMarket Archiwum]({zen_url})" if zen_url else f"[🇯🇵 Oferta]({src_url})"

            md.append(
                f"| **{clean_m}**<br><small>{clean_c}</small> | "
                f"{clean_cat} | "
                f"**{jpy:,.0f} JPY**<br>(~{pln_raw:.2f} zł) | "
                f"~{landed:.2f} zł | "
                f"**{est_pl:.2f} zł** | "
                f"{margin_col} | "
                f"`{speed}` | "
                f"`{status}` | "
                f"{link_str} |"
            )

        md.append("")
        md.append("---")
        md.append("")

        md.append("## 📈 Mapa Popytu i Cykl Życia Oferty na Japońskim Rynku")
        md.append("")
        md.append("```mermaid")
        md.append("flowchart TD")
        md.append("    A[\"Nowa Oferta na Mercari / Yahoo Japan\"] --> B{\"Jaka kategoria i cena?\"}")
        md.append("    B -->|\"Nintendo DS < 3,800 JPY<br>Gry UMD Lot < 4,000 JPY<br>Aparaty < 2,500 JPY\"| C[\"🔥 HOT MOVER<br>Wyprzedaż w < 24h<br>Zysk w PL: +70 do +340 zł\"]")
        md.append("    B -->|\"PS Vita Kolory 13,000-15,500 JPY<br>Obiektywy manualne < 100 zł\"| D[\"⚡ SZYBKI OBRÓT<br>Sprzedaż w 1-5 dni<br>Zysk w PL: +150 do +370 zł\"]")
        md.append("    B -->|\"PS4 MGS / Rathalos 20,000-28,000 JPY<br>PSone Combo LCD\"| E[\"💎 KOLEKCJONERSKI<br>Sprzedaż w 7-25 dni<br>Zysk w PL: +450 do +650 zł\"]")
        md.append("    B -->|\"PS5 Spider-Man > 60,000 JPY<br>Konsole płytowe bez testu\"| F[\"⚠️ ZAMROŻONY KAPITAŁ<br>Wisi 30+ dni<br>Wysokie exit fees w Polsce\"]")
        md.append("```")
        md.append("")
        md.append("---")
        md.append(f"*Raport wygenerowany automatycznie przez silnik HistoryTracker & HistoryGenerator. Ostatnia synchronizacja: {now_str}.*")

        return "\n".join(md)
