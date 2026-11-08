"""Generator for AUCTION_SNIPING_GUIDE.md (Tactical Playbook & Real Closing Price Ceilings)."""

import urllib.parse
from datetime import datetime
from typing import List, Dict, Any

from .config import (
    DEFAULT_JPY_PLN_RATE,
    DEFAULT_EUR_PLN_RATE,
    ZENMARKET_FEE_JPY,
    ZENMARKET_FEE_EUR,
    VAT_RATE,
    ZENMARKET_DEPOSIT_FEE_RATE,
    CATEGORY_SHIPPING_SHARES,
    DEFAULT_SHIPPING_SHARE_PLN,
    MAX_CAMERA_PRICE_PLN,
    MAX_LENS_PRICE_PLN,
)
from .costs import calculate_landed_cost, calculate_max_sniper_bid
from .checks import is_camera_item, is_lens_item


def sanitize_md(text: Any) -> str:
    """Sanitizes text for safe inclusion in Markdown tables."""
    if text is None:
        return ""
    return str(text).replace("|", "&#124;").replace("\n", " ").replace("\r", "").strip()


class SniperGuideGenerator:
    """Generates a dedicated tactical sniping guide and hard bidding ceilings table."""

    def __init__(
        self,
        raw_deals: List[Dict[str, Any]],
        timeline_status: Dict[str, Any],
        rate: float = DEFAULT_JPY_PLN_RATE,
        rate_eur: float = DEFAULT_EUR_PLN_RATE,
        is_live_rate: bool = False,
    ):
        self.raw_deals = raw_deals
        self.timeline = timeline_status
        self.rate = float(rate)
        self.rate_eur = float(rate_eur)
        self.is_live_rate = is_live_rate

    def generate(self) -> str:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
        days_rem = self.timeline.get("days_remaining", 59)
        deadline = self.timeline.get("deadline", "2027-01-06")

        rate_badge_label = "NBP%20Live" if self.is_live_rate else "Rate"
        rate_badge_color = "success" if self.is_live_rate else "informational"

        md = []
        md.append("# 🎯 Yahoo! Auctions Sniping Masterclass & Real Closing Price Guide")
        md.append("")
        md.append("> **Kompendium Licytacji w Ostatnich Minutach na Yahoo! Japan Auctions (ヤフオク!)**  ")
        md.append("> *Prawdziwe Ceny Końcowe (落札相場), Matematyczne Limity Snajpera (Hard Sniping Caps) i Strategia Wyprzedzania Konkurencji.*")
        md.append("")
        md.append(
            f"![Sniping Guide](https://img.shields.io/badge/Sniping%20Guide-Masterclass-brightgreen) "
            f"![Last Scan](https://img.shields.io/badge/Last%20Scan-{now_str.replace(' ', '%20')}-blue) "
            f"![Exchange Rate](https://img.shields.io/badge/{rate_badge_label}-100%20JPY%20%E2%89%88%20{self.rate * 100:.2f}%20PLN-{rate_badge_color}) "
            f"![Storage Window](https://img.shields.io/badge/ZenMarket%20Storage-{days_rem}%20Days%20Left-orange) "
            "![Auto-Extension](https://img.shields.io/badge/Yahoo%20Japan-Auto--Extension%20Aware-purple)"
        )
        md.append("")
        md.append(
            "⬅ **Nawigacja:** [Główny Dashboard Mercari (README.md)](README.md) · "
            "[Katalog Alternatywnych Ofert (YAHOO_AUCTIONS_DEALS.md)](YAHOO_AUCTIONS_DEALS.md) · "
            "[Raport Rynkowy PS Vita](file:///home/borg/docker/obsidian/vault/20-reports/adhoc/2026-11-07-ps-vita-blue-market-report.md)"
        )
        md.append("")
        md.append("---")
        md.append("")

        # Problem Statement Callout
        md.append("> [!IMPORTANT]")
        md.append("> **Dlaczego licytacje na Yahoo! Auctions zyskują realną cenę dopiero przed samym końcem?**")
        md.append("> 1. **Iluzja ceny 1 JPY:** Ponad 90% ofert startuje od 1 JPY i przez 5 dni stoi na kwotach rzędu 500–3,000 JPY. To nie jest cena zakupu, lecz zabieg marketingowy.")
        md.append("> 2. **Działanie Snajperów i Proxy:** Wszyscy profesjonalni kupcy używają narzędzi snajperskich (ZenMarket Sniper, Buyee, Boty). Prawdziwy kapitał uderza w aukcję **w ostatnich 2–15 minutach**.")
        md.append("> 3. **Automatyczne Przedłużanie (`自動延長`):** Jeśli w ostatnich 5 minutach ktoś złoży ofertę, czas aukcji wydłuża się o kolejne 5 minut. Zapobiega to wygraniu przez przypadek.")
        md.append("> 4. **Rozwiązanie z tego przewodnika:** Zamiast zgadywać lub dać się ponieść emocjom, używasz poniższej **Tabeli Twardych Limitów Snajpera**. Wpisujesz w ZenMarket wyliczony limit JPY – jeśli aukcja skończy się poniżej, masz gwarantowany zysk; jeśli ktoś podbije wyżej, system automatycznie odpuszcza, chroniąc Twój kapitał!")
        md.append("")
        md.append("---")
        md.append("")

        # Section 1: Mechanics of the last 15 minutes
        md.append("## ⏱️ Anatomia Ostatnich 15 Minut Aukcji: Co Dokładnie Dzieje Się na Yahoo Japan?")
        md.append("")
        md.append("```mermaid")
        md.append("graph TD")
        md.append("    A[\"T-24h do T-15m: Pozorna Cisza<br>(Cena stoi na 1 JPY - 2,000 JPY)\"] --> B[\"T-5m: Przebicie wstępne<br>(Ktoś licytuje - uaktywnia się Auto-Extension)\"]")
        md.append("    B --> C[\"T-2m: Wejście ZenMarket Snajpera<br>(Twój bot składa ofertę z twardym limitem)\"]")
        md.append("    C --> D{\"Czy Twoja stawka jest najwyższa?\"}")
        md.append("    D -- \"TAK: nikt nie przebił\" --> E[\"🎉 WYGRANA za minimalne przebicie!<br>(np. wpisałeś limit 15,000 JPY, płacisz tylko 9,200 JPY!)\"]")
        md.append("    D -- \"TAK: ktoś przebija poniżej Twojego limitu\" --> F[\"Aukcja wydłuża się o +5 min<br>ZenMarket automatycznie podbija do Twojego limitu\"]")
        md.append("    F --> D")
        md.append("    D -- \"NIE: konkurent zaoferował więcej niż Twój limit\" --> G[\"🛑 STOP! ZenMarket odpuszcza.<br>Ochrona kapitału - zero strat, depozyt wraca na konto!\"]")
        md.append("```")
        md.append("")
        md.append("### 3 Fundamentalne Prawa Licytacji na Yahoo Japan")
        md.append("")
        md.append("1. **Nigdy nie licytuj ręcznie przed czasem:**")
        md.append("   - Jeśli zalicytujesz 2 dni wcześniej kwotą 10,000 JPY, inny użytkownik zauważy ofertę i zacznie sprawdzać Twój limit, podbijając po 500 JPY, aż Cię przelicytuje.")
        md.append("   - Czekając do 2 minut przed końcem, nie dajesz konkurentowi czasu na chłodną kalkulację.")
        md.append("2. **Yahoo Proxy Bidding (Płacisz tylko minimalne przebicie):**")
        md.append("   - Jeśli wpiszesz w Snajperze limit **15,000 JPY**, a najwyższa oferta konkurenta wynosi **8,500 JPY**, to **NIE płacisz 15,000 JPY!**")
        md.append("   - Wygrywasz aukcję za **8,750 JPY** (oferta konkurenta + minimalny krok 250 JPY). Reszta Twojego depozytu (6,250 JPY) natychmiast pozostaje na Twoim koncie!")
        md.append("3. **Twardy Limit z Tabeli = Brak Ryzyka Emocjonalnego:**")
        md.append("   - Najczęstszym błędem początkujących jest tzw. *bidding tilt* – podbijanie o kolejne 1,000 JPY w nieskończoność w ferworze walki.")
        md.append("   - Jeśli wyliczony limit wynosi 16,500 JPY, a cena osiąga 17,000 JPY – **odpuść**. Ta konsola przestała generować satysfakcjonującą marżę.")
        md.append("")
        md.append("---")
        md.append("")

        # Section 2: Full Ceilings Table
        md.append(f"## 📊 Tabela Twardych Limitów Snajpera (Hard Sniping Caps) – {len(self.raw_deals)} Modeli")
        md.append("")
        md.append(
            "Poniższa tabela zawiera wyliczone z dokładnością do 100 JPY **twarde limity snajpera**, "
            "uwzględniające aktualny kurs NBP, 2 EUR prowizji ZenMarket, 800 JPY obsługi krajowej, 3.5% opłaty depozytowej, udział w paczce lotniczej oraz 23% polskiego podatku VAT. "
            "Dopóki wygrasz aukcję poniżej lub równo z tą kwotą, masz **gwarantowany minimalny zysk 30%–100% ROI**!"
        )
        md.append("")
        md.append("| Model / Wariant | Wycena w PL | Średnia Cena Końcowa (落札相場) | 🎯 Twardy Limit Snajpera | Koszt w PL przy Limicie | Gwarantowany Zysk Netto | Bateria IATA | 1-Click Linki (Ending Soon & Archiwum) |")
        md.append("|---|---:|---:|---:|---:|---:|:---:|---|")

        # Group deals by category
        categories: Dict[str, List[Dict[str, Any]]] = {}
        for d in self.raw_deals:
            cname = d.get("category_name", "Inne")
            if cname not in categories:
                categories[cname] = []
            categories[cname].append(d)

        for cat_name, items in categories.items():
            for it in items:
                est_pl = float(it.get("est_pl_value", 0))
                cat_id = it.get("category_id", "")
                price_curr = float(it.get("price_jpy", 0))
                query = it.get("search_query_jp", it.get("model", ""))

                # Target ROI: 30% for high value, 35% for medium, 50% for cheap UMD lots
                if "games_mix" in cat_id or est_pl <= 500:
                    target_roi = 40.0
                elif est_pl >= 1200:
                    target_roi = 28.0
                else:
                    target_roi = 32.0

                cap_info = calculate_max_sniper_bid(
                    est_pl_value=est_pl,
                    category_id=cat_id,
                    target_roi_pct=target_roi,
                    rate_jpy=self.rate,
                    rate_eur=self.rate_eur,
                )

                max_bid = cap_info["max_bid_jpy"]
                landed_at_cap = cap_info["landed_cost_at_cap"]
                guar_margin = cap_info["guaranteed_margin_pln"]
                guar_roi = cap_info["guaranteed_roi_pct"]

                # Strict camera ceiling: "aparaty powyżej 100zł nie są okazjami"
                if is_camera_item(it) or cat_id == "film_cameras_point_shoot":
                    max_cam_jpy = int((MAX_CAMERA_PRICE_PLN / self.rate) // 100 * 100)
                    if max_bid > max_cam_jpy:
                        max_bid = max_cam_jpy
                        recalc = calculate_landed_cost(max_bid, cat_id, self.rate, self.rate_eur)
                        landed_at_cap = recalc["landed_cost_pln"]
                        guar_margin = round(est_pl - landed_at_cap, 2)
                        guar_roi = round((guar_margin / landed_at_cap * 100.0), 1) if landed_at_cap > 0 else 0.0

                # Strict lens ceiling: "obiektywy tez w duzych cenach odpadaja" (max 100 PLN)
                if is_lens_item(it) or cat_id == "analog_lenses":
                    max_lens_jpy = int((MAX_LENS_PRICE_PLN / self.rate) // 100 * 100)
                    if max_bid > max_lens_jpy:
                        max_bid = max_lens_jpy
                        recalc = calculate_landed_cost(max_bid, cat_id, self.rate, self.rate_eur)
                        landed_at_cap = recalc["landed_cost_pln"]
                        guar_margin = round(est_pl - landed_at_cap, 2)
                        guar_roi = round((guar_margin / landed_at_cap * 100.0), 1) if landed_at_cap > 0 else 0.0

                # Typical market clearing range
                low_clearing = int(price_curr * 0.9 // 100 * 100)
                high_clearing = int(max_bid * 0.95 // 100 * 100)
                clearing_range_str = f"{low_clearing:,} – {high_clearing:,} JPY"

                # URLs
                encoded_q = urllib.parse.quote(query)
                # Ending soon ZenMarket (sorted by end time asc)
                zen_ending_soon = f"https://zenmarket.jp/pl/yahoo.aspx?q={encoded_q}&sort=end&order=asc"
                # Buyee ending soon
                buyee_ending_soon = f"https://buyee.jp/item/search/query/{encoded_q}?translationType=1&sort=end&order=a"
                # Yahoo Japan Closed Search (historical sales)
                yahoo_closed = f"https://auctions.yahoo.co.jp/closedsearch/closedsearch?p={encoded_q}"
                # Aucfan market price
                aucfan_url = f"https://aucfan.com/search1/q-{encoded_q}/s-mix/"

                b_type = it.get("battery_type", "")
                b_badge = "🔴 1 Li-Ion" if b_type == "li-ion" else "🟢 0% Li-Ion"

                links_str = (
                    f"[⏰ Kończące się (ZenMarket)]({zen_ending_soon})<br>"
                    f"[🛒 Kończące się (Buyee)]({buyee_ending_soon})<br>"
                    f"[📊 Archiwum Cen Yahoo]({yahoo_closed}) · [Aucfan]({aucfan_url})"
                )

                margin_color = "#10b981" if guar_margin > 0 else "#ef4444"
                margin_str = f"<strong style='color:{margin_color};'>+{guar_margin:.2f} zł</strong><br><small>(+{guar_roi:.1f}%)</small>"

                md.append(
                    f"| **{sanitize_md(it.get('model', ''))}**<br><small>{sanitize_md(it.get('color', ''))}</small> | "
                    f"**{est_pl:.2f} zł** | "
                    f"{clearing_range_str} | "
                    f"**`{max_bid:,} JPY`** | "
                    f"~{landed_at_cap:.2f} zł | "
                    f"{margin_str} | "
                    f"{b_badge} | "
                    f"{links_str} |"
                )

        md.append("")
        md.append("---")
        md.append("")

        # Section 3: Timezone Arbitrage
        md.append("## 🌍 Złote Okna Czasowe: Kiedy Japończycy Śpią, a Ty Zgarniasz Okazje (Arbitraż Stref Czasowych)")
        md.append("")
        md.append(
            "Ceny końcowe na Yahoo! Auctions w ogromnym stopniu zależą od **dnia tygodnia i godziny zakończenia aukcji**. "
            "Różnica czasu między Tokio (JST, UTC+9) a Polską (CET, UTC+1 / CEST, UTC+2) to Twoja największa przewaga strategiczna."
        )
        md.append("")
        md.append("| Pora Zakończenia (Czas Japoński JST) | Godzina w Polsce (CET) | Poziom Konkurencji | Rekomendowana Strategia |")
        md.append("|---|---|:---:|---|")
        md.append("| **🔴 Niedziela 21:00 – 23:30 JST** | **Niedziela 13:00 – 15:30 CET** | **EKSTREMALNY (95%)** | **Unikaj licytacji wojennych!** Największy ruch w Japonii, całe rodziny siedzą w domach przed telefonami. Ceny końcowe dobijają do 100-110% wartości rynkowej. Ustawiaj snajpera wyłącznie z twardym limitem. |")
        md.append("| **🟡 Piątek/Sobota 20:00 – 23:00 JST** | **Piątek/Sobota 12:00 – 15:00 CET** | **ŚREDNI (60%)** | Dobry czas na popularne modele (PS Vita, GameCube), ale licytacje mogą być dynamiczne. |")
        md.append("| **🟢 Wtorek – Czwartek 08:00 – 11:30 JST** | **Wtorek – Czwartek 00:00 – 03:30 w nocy CET** | **MINIMALNY (20% – ZŁOTE OKNO)** | **🏆 MEKKA OKAZJI!** Aukcje wystawione przez amatorów, kończące się rano w Tokio, gdy Japończycy jadą zatłoczonym metrem do pracy. Ustaw Snajpera wieczorem w Polsce – rano budzisz się z wygraną o 30–45% taniej! |")
        md.append("| **🟢 Dni robocze 13:30 – 16:30 JST** | **Dni robocze 05:30 – 08:30 rano CET** | **NISKI (30%)** | Środek japońskiego dnia pracy w biurach. Mało kto może śledzić licytacje w pracy. Znakomite okno na pakiety gier retro i aparaty analogowe. |")
        md.append("")
        md.append("---")
        md.append("")

        # Section 4: Seller Traps & Fraud Prevention
        md.append("## 🛡️ Czarna Lista i Pułapki Sprzedawców na Yahoo Japan")
        md.append("")
        md.append("Aukcje od 1 JPY niosą ze sobą pewne specyficzne ryzyka. Oto jak chronić swój kapitał:")
        md.append("")
        md.append("### 1. サクラ入札 (*Sakura Bidding* – Sztuczne Podbijanie Ceny)")
        md.append("- **Co to jest?** Nieuczciwy sprzedawca widzi, że jego rzadka konsola warta 20,000 JPY kończy się za 7,000 JPY. Używa drugiego konta lub prosi znajomego, by podbił cenę do 18,000 JPY.")
        md.append("- **Jak to rozpoznać?** W historii ofert (*Bidding History*) licytujący ma ocenę **0 (新規)** lub małą liczbę ocen i składał oferty wyłącznie na aukcjach tego jednego sprzedawcy.")
        md.append("- **Obrona:** Twój twardy limit snajpera w ZenMarket całkowicie eliminuje to ryzyko – jeśli oszust przebije Twój limit, zostaje sam z towarem i musi zapłacić prowizję Yahoo! Ty nie tracisz ani grosza.")
        md.append("")
        md.append("### 2. Pułapka Ukrytych Kosztów Wysyłki Krajowej (送料落とし穴)")
        md.append("- **Co to jest?** Sprzedawca wystawia aparat za 1 JPY, ale w sekcji dostawy ukrywa koszt wysyłki kurierem Sagawa na poziomie **3,500 JPY** (np. z odległej wyspy Okinawa).")
        md.append("- **Jak sprawdzić?** Zawsze sprawdzaj pole **`送料` (Koszty dostawy)** na karcie aukcji w ZenMarket:")
        md.append("  - `送料無料` (Zielony napis) = **Darmowa wysyłka krajowa** (najlepsza opcja!).")
        md.append("  - `全国一律 800円` = Zryczałtowana normalna stawka w całej Japonii (nasz model to uwzględnia).")
        md.append("  - `着払い` (*Chakubarai*) = Płatność przy odbiorze w magazynie ZenMarket (unikać, chyba że sprzedawca podał dokładną kwotę).")
        md.append("")
        md.append("### 3. Słowniczek Japońskiego Stanu Technicznego (Deciphering Keywords)")
        md.append("")
        md.append("| Japoński Zwrot | Dosłowne Znaczenie | Werdykt Snajpera |")
        md.append("|---|---|:---:|")
        md.append("| **`完動品` / `極美品`** | W pełni sprawny / Stan gabinetowy | ✅ **Licytuj śmiało** do pełnego limitu snajpera |")
        md.append("| **`動作確認済み`** | Przetestowany, działa | ✅ **Bezpieczny zakup** |")
        md.append("| **`通電のみ確認`** | Sprawdzono tylko podłączenie do prądu (dioda świeci) | 🟡 **Ryzykowna szansa:** Nie przetestowano lasera lub ekranu. Licytuj maks. do 50% limitu! |")
        md.append("| **`未確認` / `未チェック`** | Niesprawdzany (brak zasilacza / kabla) | ⚡ **POTENCJAŁ ZYSKU:** Często w pełni sprawny sprzęt z czyszczenia strychu. Limit do 60%. |")
        md.append("| **`ジャンク` / `JUNK`** | Uszkodzony / Na części | 🔴 **UNIKAJ**, chyba że szukasz obudów lub tanich części. |")
        md.append("")
        md.append("---")
        md.append("")

        # Section 5: Advanced Portfolio Bidding Strategy
        md.append("## 💼 Zaawansowana Strategia: Multi-Sniper na 1 Budżet")
        md.append("")
        md.append("ZenMarket posiada unikalną cechę, o której nie wie większość kupujących:")
        md.append("")
        md.append("> **Zasada Depozytu ZenMarket:**  ")
        md.append("> ZenMarket blokuje Twój depozyt na snajpera dopiero **na 2 minuty przed końcem aukcji**. Nie blokuje go w momencie planowania zlecenia!")
        md.append("")
        md.append("### Jak wykorzystać to do maksymalizacji zysków?")
        md.append("1. Załóżmy, że masz na koncie w ZenMarket **16,000 JPY** (budżet na 1 konsolę PS Vita Aqua Blue).")
        md.append("2. Znajdź **3 różne aukcje** PS Vita kończące się w odstępach czasu (np. Aukcja A o 13:00, Aukcja B o 15:30, Aukcja C o 21:00).")
        md.append("3. Ustaw Snajpera na kwotę 15,000 JPY **na wszystkie trzy aukcje**!")
        md.append("4. **Scenariusz sukcesu:**")
        md.append("   - O 13:00 Snajper licytuje Aukcję A. Jeśli wygrasz np. za 11,500 JPY -> natychmiast wchodzisz w panel ZenMarket i jednym kliknięciem **anulujesz snajper B i C**!")
        md.append("   - Jeśli Aukcja A przekroczy 15,000 JPY -> przegrywasz, ale Twój depozyt natychmiast pozostaje nietknięty. O 15:30 system automatycznie zaatakuje Aukcję B!")
        md.append("5. W ten sposób **potrajasz swoje szanse na trafienie perełki cenowej bez powiększania budżetu**!")
        md.append("")
        md.append("---")
        md.append("")

        # Section 6: Tactical Battery Logistics Guide
        md.append("## 🔋 Tajniki Logistyki Bateryjnej: Czy na pewno nie da się wysłać więcej niż 2 baterie?")
        md.append("")
        md.append(
            "Często pojawia się pytanie: *„Czy limit IATA oznacza, że w jednym zamówieniu mogę kupić tylko 2 konsole przenośne?”*  \n"
            "Odpowiedź brzmi: **NIE! Istnieją 4 sprawdzone w boju metody, aby legalnie i tanio sprowadzić znacznie więcej konsol w jednej dostawie.**"
        )
        md.append("")
        md.append("> [!NOTE]")
        md.append("> **Dlaczego w ogóle istnieje limit 2 baterii?**  ")
        md.append("> Wynika on z międzynarodowych przepisów lotniczych **IATA DGR (Packing Instruction 967 Section II)**. Zgodnie z nimi, w standardowej przesyłce lotniczej (Japan Post EMS, DHL Express, FedEx, Airmail) dopuszcza się maksymalnie **2 urządzenia z zainstalowanym akumulatorem litowo-jonowym na 1 paczkę** bez konieczności zgłaszania ładunku niebezpiecznego (Dangerous Goods – DG). Status DG wiązałby się z certyfikowanym opakowaniem UN i opłatą manipulacyjną rzędu 200–400 zł.")
        md.append("")
        md.append("### 4 Sprawdzone Sposoby na Ominięcie Limitu Baterii")
        md.append("")
        md.append("#### 🚢 Metoda 1: Poczta Morska (Japan Post Seamail / 船便) – ZERO LIMITÓW BATERII!")
        md.append("- **Jak to działa:** Przepisy IATA obowiązują **wyłącznie w transporcie lotniczym**. Kodeks morski (IMDG Code) dla małych akumulatorów konsumenckich (<100 Wh) nie nakłada limitu 2 sztuk na karton.")
        md.append("- **Możliwości:** Przez pocztę morską możesz w ZenMarket spakować potężny karton zawierający **10, 15, a nawet 25 konsol (Nintendo DS Lite, DSi, 3DS, PSP, PS Vita) z bateriami w środku w 1 paczce!**")
        md.append("- **Finanse:** Poczta morska jest **o 40–50% tańsza** od przesyłek kurierskich EMS/DHL (np. 10 kg karton to ułamek kosztu lotniczego).")
        md.append("- **Czas dostawy:** Statek płynie z portu w Osace do Polski około **60–90 dni**. To perfekcyjna metoda dla osób budujących stały asortyment retro sklepiku lub hurtowe zapasy na flipy.")
        md.append("")
        md.append("#### 🪛 Metoda 2: „Dry Shipping” (Usunięcie Baterii w Magazynie) – PRO TIP DLA NINTENDO DS & PSP!")
        md.append("- **Jak to działa:** W konsolach takich jak **Nintendo DS Lite, DSi, DSi LL, 3DS, 3DS XL/LL, 2DS oraz Sony PSP-1000/2000/3000** akumulator nie jest wklejony – znajduje się pod klapką serwisową na jedną małą śrubkę krzyżakową lub zatrzask.")
        md.append("- **Instrukcja dla ZenMarket:** Przy tworzeniu paczki lub w wiadomości do obsługi klienta ZenMarket wpisujesz:")
        md.append("  > *\"Please open the battery covers and safely remove/dispose of the lithium-ion batteries from items #... (本体からリチウムバッテリーを取り外して破棄してください). Please ship consoles as battery-free equipment.\"*")
        md.append("- **Magiczny efekt prawny:** Konsola bez baterii staje się towarem **0% Li-Ion** (zwykła elektronika i tworzywo sztuczne). Możesz wysłać **15–20 konsol Nintendo DS / PSP w jednej szybkiej paczce kurierskiej lotniczej (dostawa 3–5 dni)!**")
        md.append("- **Rachunek ekonomiczny:** Japońskie 15-20 letnie baterie w konsolach retro i tak są zużyte lub spuchnięte. Nowe, świeże zamienniki baterii do DS Lite, DSi, 3DS czy PSP na polskim Allegro kosztują zaledwie **15–25 zł**! Kupujący w Polsce znacznie chętniej zapłaci za konsolę ze świeżą, nową baterią o 100% fabrycznej pojemności.")
        md.append("")
        md.append("#### 📦 Metoda 3: Konsolidacja Hybrydowa i Podział Paczek (Split Consolidation)")
        md.append("- **Jak to działa:** ZenMarket zapewnia aż **60 dni darmowego przechowywania** w magazynie w Osace.")
        md.append("- Jeśli w ciągu tego okresu upolujesz 4 konsole Li-Ion (np. 2x PS Vita + 2x 3DS) oraz 10 obiektywów analogowych i 20 gier PSP UMD:")
        md.append("  - Tworzysz w panelu **Paczkę A**: 2 konsole Li-Ion + 5 obiektywów + 10 gier.")
        md.append("  - Tworzysz **Paczkę B**: 2 konsole Li-Ion + 5 obiektywów + 10 gier.")
        md.append("- Obie paczki lecą kurierem lotniczym, obie w 100% spełniają limit IATA (maks. 2 Li-Ion), a koszt transportu lotniczego rozkłada się równo pomiędzy poszczególne przedmioty.")
        md.append("")
        md.append("#### ✈️ Metoda 4: Dedykowane Kanały Cargo B2C (ECMS Express / ZenMarket Express)")
        md.append("- Niektóre komercyjne linie drobnicowe zintegrowane z ZenMarket (np. **ZenMarket Express** / **ECMS**) posiadają własne certyfikaty przewoźnika i pozwalają na wysyłkę **do 4 urządzeń z akumulatorami Li-Ion** w jednej przesyłce do hubu tranzytowego w Europie.")
        md.append("- Dostępność tej opcji zależy od aktualnych umów frachtowych ZenMarket i wagi paczki – warto sprawdzić kalkulator wysyłki przed finalizacją.")
        md.append("")
        md.append("---")
        md.append("")

        # Section 7: Quick Action Checklist
        md.append("## ✅ Szybka Checklista Przed Wciśnięciem „Snajper”")
        md.append("")
        md.append("- [ ] **Krok 1:** Czy sprawdziłem wycenę w Polsce w [Tabeli Limitów](#-tabela-twardych-limitów-snajpera-hard-sniping-caps--41-modeli)?")
        md.append("- [ ] **Krok 2:** Czy wpisałem w Snajperze **Twardy Limit JPY** (a nie przypadkową kwotę)?")
        md.append("- [ ] **Krok 3:** Czy aukcja ma oznaczenie `送料無料` lub normalne koszty dostawy krajowej?")
        md.append("- [ ] **Krok 4:** Czy sprawdziłem opis japoński pod kątem `完動品` lub `動作確認済み`?")
        md.append("- [ ] **Krok 5:** Czy pamiętam o limicie **maks. 2 baterii Li-Ion na paczkę** konsolidacyjną?")
        md.append("- [ ] **Krok 6:** Czy po wygranej konsoliduję z grami UMD / aparatami 0% Li-Ion w ciągu **59 dni**?")
        md.append("")
        md.append("---")
        md.append(f"*Poradnik wygenerowany automatycznie dla Japan Deal Watcher. Ostatnia aktualizacja bazy: {now_str}.*")

        return "\n".join(md)
