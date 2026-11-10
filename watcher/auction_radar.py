"""Generator module for AUCTION_RADAR.md (Live Auction Radar, Real Closing Prices & Arbitrage Radar)."""

import urllib.parse
from datetime import datetime
from typing import List, Dict, Any

from .config import (
    DEFAULT_JPY_PLN_RATE,
    DEFAULT_EUR_PLN_RATE,
    MAX_CAMERA_PRICE_PLN,
    MAX_LENS_PRICE_PLN,
)
from .costs import calculate_landed_cost, calculate_max_sniper_bid
from .checks import is_camera_item, is_lens_item
from .closure_predictor import AuctionClosurePredictor, ConditionGrade


def sanitize_md(text: Any) -> str:
    """Sanitizes text for safe inclusion in Markdown tables."""
    if text is None:
        return ""
    cleaned = str(text).replace("|", "&#124;").replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
    return " ".join(cleaned.split()).strip()


class AuctionRadarGenerator:
    """Generates AUCTION_RADAR.md – The dedicated live auction radar and closure price intelligence dashboard."""

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
        days_rem = self.timeline.get("days_remaining", 58)
        deadline = self.timeline.get("deadline", "2027-01-06")

        rate_badge_label = "NBP%20Live" if self.is_live_rate else "Rate"
        rate_badge_color = "success" if self.is_live_rate else "informational"

        md = []
        md.append("# 📡 Yahoo! Auctions Live Radar & Real Closing Price Intelligence")
        md.append("")
        md.append("> **Radar Aktywnych Licytacji, Baza Rzeczywistych Cen Końcowych (落札相場) i Arbitraż Yahoo vs Mercari**  ")
        md.append("> *Dedykowane narzędzie analityczne: gdzie aukcje miażdżą oferty Kup Teraz, jakie są realne ceny zamknięcia i które licytacje natychmiast wrzucić na celownik.*")
        md.append("")
        md.append(
            f"![Auction Radar](https://img.shields.io/badge/Auction%20Radar-Active-brightgreen) "
            f"![Watched Targets](https://img.shields.io/badge/Watched%20Targets-{len(self.raw_deals)}%20Models-blue) "
            f"![Last Scan](https://img.shields.io/badge/Last%20Scan-{now_str.replace(' ', '%20')}-purple) "
            f"![Exchange Rate](https://img.shields.io/badge/{rate_badge_label}-100%20JPY%20%E2%89%88%20{self.rate * 100:.2f}%20PLN-{rate_badge_color}) "
            f"![Storage Window](https://img.shields.io/badge/ZenMarket%20Storage-{days_rem}%20Days%20Left-orange) "
            f"![Max Li-Ion](https://img.shields.io/badge/IATA%20Limit-Max%202%20Li--Ion-red)"
        )
        md.append("")
        md.append(
            "⬅ **Nawigacja:** [📱 **Aplikacja Android / PWA (Live)**](https://110kc3.github.io/japan-deal-watcher/) · "
            "[Główny Dashboard Mercari (README.md)](README.md) · "
            "[📦 **Pakiety Różności & Danshari (MYSTERY_LOTS_ANALYSIS.md)**](MYSTERY_LOTS_ANALYSIS.md) · "
            "[🎯 Poradnik Snajpera i Limity (AUCTION_SNIPING_GUIDE.md)](AUCTION_SNIPING_GUIDE.md) · "
            "[🔨 Katalog Alternatywnych Ofert (YAHOO_AUCTIONS_DEALS.md)](YAHOO_AUCTIONS_DEALS.md) · "
            "[📈 Historia Sprzedaży (MARKET_SALES_HISTORY.md)](MARKET_SALES_HISTORY.md) · "
            "[💰 Audyt Opłacalności (REAL_PROFITABILITY_AUDIT.md)](REAL_PROFITABILITY_AUDIT.md)"
        )
        md.append("")
        md.append("---")
        md.append("")

        # Section 1: Core Arbitrage Thesis
        md.append("## 💡 Dlaczego na Aukcjach Yahoo Kupisz Taniej Niż na Mercari? (Fakty i Liczby)")
        md.append("")
        md.append("> [!NOTE]")
        md.append("> **Mercari Japan vs Yahoo! Auctions Japan – Dwa Różne Światy Handlu:**")
        md.append("> - **Mercari (Kup Teraz / BIN):** Sprzedawcy wyceniają towar na podstawie innych aktywnych ofert. Ceny są sztywne. Jeśli ktoś wystawi tanio, boty i resellerzy wykupują to w 2–15 minut. Zostają tylko oferty w cenach rynkowych.")
        md.append("> - **Yahoo! Auctions (Licytacje od 1 JPY):** Japończycy wystawiający spadki, likwidacje strychów czy szaf wystawiają towar od 1 JPY na 5–7 dni bez ceny minimalnej. **Aukcje hurtowe i nieprzetestowane zamykają się średnio 25%–55% taniej niż oferty Kup Teraz na Mercari!**")
        md.append("> - **Magia Ostatnich 120 Sekund:** Ponad 75% licytacji w dni robocze kończy się w godzinach, gdy w Japonii trwa praca lub sen. Wykorzystując automatycznego Snajpera ZenMarket z twardym limitem kapitałowym, wygrywasz aukcje poniżej ceny detalicznej!")
        md.append("")
        md.append("```mermaid")
        md.append("graph LR")
        md.append("    A[\"Mercari Japan (Kup Teraz)<br>Cena stała: 100% wartości rynkowej<br>Szybki zakup, mniejszy narzut\"] --- vs[\"VS\"]")
        md.append("    vs --- B[\"Yahoo! Auctions (Licytacje 1 JPY)<br>Cena końcowa: 55-75% wartości rynkowej<br>⚡ Wyższa marża o +150-400 zł na sztuce!\"]")
        md.append("```")
        md.append("")
        md.append("---")
        md.append("")

        # Section 2: Condition-Aware Closure Price Matrix & Prediction Engine (落札相場)
        md.append("## 📊 Matryca Arbitrażu: Rzeczywiste Ceny Końcowe Yahoo (落札相場) i Predykcja Stanów Wizualnych")
        md.append("")
        md.append(
            "Ceny na Yahoo! Auctions zależą bezpośrednio od **stanu technicznego i wizualnego**. "
            "Poniższy silnik analityczny klasyfikuje oferty do 5 standardowych klas stanu (od *Box CIB* po *Danshari Junk*), "
            "porównuje je z historyczną bazą sprzedaży (`落札相場`) i **prognozuje ostateczną cenę zamknięcia danej licytacji**. "
            "Dzięki temu wiesz z góry, czy licytacja okaże się prawdziwą okazją, czy w ostatnich minutach zostanie przepłacona przez konkurencję."
        )
        md.append("")
        md.append("> [!IMPORTANT]")
        md.append("> **Zasada 4 Poziomów Rekomendacji Rynkowej (Market Deal Verdict):**  ")
        md.append("> - 🔥 **S-TIER (Pewny Arbitraż):** Prognozowana cena końcowa zostawia **> 120 zł zysku** i **> 30% ROI** przy twardym limicie snajpera. Absolutny priorytet zakupowy!  ")
        md.append("> - ⚡ **A-TIER (Solidna Okazja):** Oczekiwane zamknięcie poniżej limitu opłacalności, marża **60–120 zł** (ROI > 18%).  ")
        md.append("> - ⚖️ **B-TIER (Na Styku Opłacalności):** Cena rynkowa. Kupuj wyłącznie ze sztywnym limitem snajpera (nie licytuj ręcznie).  ")
        md.append("> - ⚠️ **C-TIER (Ryzyko Przepłacenia):** Licytacja w walce snajperów przekroczy próg opłacalności w Polsce – nie bierz w niej udziału!")
        md.append("")

        # Sort ALL items by remaining time ascending (ending soonest first – true prices)
        sorted_deals = sorted(
            self.raw_deals,
            key=lambda x: (
                x.get("time_remaining_minutes") if x.get("time_remaining_minutes") is not None else 999999,
                -x.get("est_pl_value", 0)
            )
        )

        # Precompute predictions for all deals
        predictions = [AuctionClosurePredictor.predict_closure(it, self.rate, self.rate_eur) for it in sorted_deals]

        # Top Spotlight: S-Tier and A-Tier Confirmed Deals
        spotlight = [
            (it, pred) for it, pred in zip(sorted_deals, predictions)
            if pred["verdict_code"] in ["S_TIER_SURE_ARBITRAGE", "A_TIER_SOLID_DEAL"]
        ]

        if spotlight:
            md.append("### 🏆 Potwierdzone Okazje Rynkowe (S-Tier & A-Tier – Kupuj Ze Snajperem)")
            md.append("")
            md.append("| Model / Przedmiot | ⏳ Czas | Stan | Aktualna Oferta | 🔮 Prognoza Zamknięcia | Cena w PL | Czysty Zysk przy Prognozie | 🎯 Rekomendacja Snajpera |")
            md.append("|---|:---:|:---:|---:|---:|---:|---:|---|")
            for it, pred in spotlight[:10]:
                time_m = it.get("time_remaining_minutes", 9999)
                time_fmt = it.get("time_remaining_formatted", f"{time_m} min")
                time_tag = f"<strong style='color:#ef4444;'>🔥 {time_fmt}</strong>" if time_m <= 60 else f"<strong>{time_fmt}</strong>"
                cond_tag = f"<span style='color:{pred['condition_badge_color']}; font-weight:600;'>{pred['condition_short_label']}</span>"
                profit_tag = f"<strong style='color:#10b981;'>+{pred['expected_margin_pln']:.0f} zł</strong><br><small>(+{pred['expected_roi_pct']:.0f}%)</small>"
                pred_tag = f"**{pred['predicted_closure_jpy']:,} JPY**<br><small>(~{pred['predicted_closure_pln']:.0f} zł)</small>"
                
                md.append(
                    f"| **{sanitize_md(it.get('model', ''))}** | "
                    f"{time_tag} | "
                    f"{cond_tag} | "
                    f"{it.get('price_jpy', 0):,} JPY | "
                    f"{pred_tag} | "
                    f"**{it.get('est_pl_value', 0):.0f} zł** | "
                    f"{profit_tag} | "
                    f"`{pred['verdict_label']}`<br><small>{pred['recommendation_text']}</small> |"
                )
            md.append("")
            md.append("---")
            md.append("")

        # Master Table
        md.append("### 📊 Kompletna Matryca Licytacji: Stan, Prognoza Końcowa i Werdykt Rynkowy")
        md.append("")
        md.append("| Model / Przedmiot | ⏳ Czas | Stan Wizualny | Aktualna Oferta | 🔮 Prognoza Zamknięcia | Cena w PL | Zysk przy Prognozie | 🎯 Werdykt i Limit Snajpera | Bateria |")
        md.append("|---|:---:|:---:|---:|---:|---:|---:|:---:|:---:|")

        for it, pred in zip(sorted_deals, predictions):
            est_pl = float(it.get("est_pl_value", 0))
            price_curr = float(it.get("price_jpy", 0))

            b_type = it.get("battery_type", "")
            b_badge = "🔴 1 Li-Ion" if b_type == "li-ion" else "🟢 0% Li-Ion"

            img_url = it.get("image_url", "./assets/images/placeholder.svg")
            img_tag = f"<img src='{img_url}' width='50' height='32' style='border-radius:4px; object-fit:contain; background:#0f172a; vertical-align:middle;' /><br>"
            allegro_p = it.get("allegro_archive_pln", round(est_pl * 1.08, 0))
            olx_p = it.get("olx_haggled_pln", round(est_pl * 0.90, 0))

            # Remaining time badge
            time_m = it.get("time_remaining_minutes", 9999)
            time_fmt = it.get("time_remaining_formatted", f"{time_m} min")
            if time_m <= 60:
                time_badge = f"<strong style='color:#ef4444;'>🔥 {time_fmt}</strong><br><small style='color:#fca5a5;'>Faza końcowa</small>"
            elif time_m <= 360:
                time_badge = f"<strong style='color:#f59e0b;'>⚡ {time_fmt}</strong><br><small style='color:#fcd34d;'>Ostatnie godziny</small>"
            elif time_m <= 1440:
                time_badge = f"<span style='color:#3b82f6;'>⏳ {time_fmt}</span><br><small>Średnia faza</small>"
            else:
                time_badge = f"<span style='color:#94a3b8;'>🕒 {time_fmt}</span><br><small>Wczesna oferta</small>"

            cond_badge = f"<span style='color:{pred['condition_badge_color']}; font-weight:600;'>{pred['condition_short_label']}</span><br><small style='color:#94a3b8;'>{pred['condition_features'][0] if pred['condition_features'] else ''}</small>"
            pred_badge = f"**{pred['predicted_closure_jpy']:,} JPY**<br><small>(~{pred['predicted_closure_pln']:.0f} zł)</small>"
            profit_color = "#10b981" if pred["expected_margin_pln"] >= 60 else ("#f59e0b" if pred["expected_margin_pln"] >= 25 else "#ef4444")
            profit_badge = f"<strong style='color:{profit_color};'>+{pred['expected_margin_pln']:.0f} zł</strong><br><small>(+{pred['expected_roi_pct']:.0f}%)</small>"

            verdict_badge = f"**{pred['verdict_label']}**<br><small>Limit: `{pred['max_sniper_bid_jpy']:,} JPY`</small>"

            md.append(
                f"| {img_tag}**{sanitize_md(it.get('model', ''))}**<br><small>{sanitize_md(it.get('color', ''))}</small> | "
                f"{time_badge} | "
                f"{cond_badge} | "
                f"**{price_curr:,.0f} JPY**<br><small>(~{price_curr * self.rate:.0f} zł)</small> | "
                f"{pred_badge} | "
                f"**{est_pl:.0f} zł**<br><small>Allegro: ~{allegro_p:.0f} zł<br>OLX: ~{olx_p:.0f} zł</small> | "
                f"{profit_badge} | "
                f"{verdict_badge} | "
                f"{b_badge} |"
            )

        md.append("")
        md.append("---")
        md.append("")

        # Section 3: Curated Top 12 Auction Targets To Watch
        md.append("## 🎯 Top 12 Wyselekcjonowanych Celów do Obserwacji (Bezpośrednie Linki i Snajper)")
        md.append("")
        md.append(
            "Poniższe pozycje to absolutna czołówka opłacalności na Yahoo! Auctions. "
            "Kliknij `[⏰ Kończące się Aukcje]`, aby zobaczyć trwające licytacje w kolejności wygasania (gotowe do snajpingu w T-2m), "
            "lub `[💰 Świeże od 1 JPY]`, aby dodać do obserwowanych nowe wystawienia!"
        )
        md.append("")

        # Top 12 Curated Items
        top_targets = [
            ("new_n3ds_xl_red", "Nintendo 3DS XL / New 3DS", "Królowie Płynności", "Szukaj egzemplarzy z ekranami IPS (górny ekran ma głębszą czerń pod kątem)."),
            ("gba_sp_famicom", "Game Boy Advance SP Famicom", "Rarytas Kolekcjonerski", "Możliwość Dry Shippingu (usunięcie baterii = 0% Li-Ion)."),
            ("h1179048211", "Hurtowy Pakiet 50 Gier Retro", "0% Li-Ion Maszyna Marży", "W paczkach hurtowych gry wychodzą po ~3-5 zł za sztukę w zakupie!"),
            ("a1189402911", "PSone COMBO SCPH-130 + LCD", "Wyselekcjonowana Stacjonarna", "Sprawdź czy w zestawie jest zasilacz SCPH-10130 i brak pęknięć zawiasu LCD."),
            ("ndsi_ll_wine_red", "Nintendo DSi LL (XL) IPS", "Fabryczne Ekrany IPS", "Każdy DSi LL ma fabrycznie montowane matryce IPS o szerokim kącie widzenia."),
            ("v1173928104", "PS Vita Slim PCH-2000 Aqua Blue", "Najpopularniejszy Kolor PL", "Sprawdź brak driftu gałek analogowych w opisie."),
            ("f1172938411", "GameCube DOL-001 Spice Orange", "Wyselekcjonowana Stacjonarna", "Upewnij się, że z tyłu jest cyfrowy port Digital AV Out."),
            ("psp3000_vibrant_blue", "PSP-3000 Vibrant Blue", "Płynny Handheld", "Metaliczny lakier – sprawdź brak wytarć na tylnym okręgu."),
            ("b1168492019", "Zestaw 30 Gier Nintendo DS Box", "0% Li-Ion Kartridże", "Gry DS w plastikowych pudełkach – wysoka marża jednostkowa."),
            ("j1128492014", "PS4 Pro Rathalos Monster Hunter 1TB", "Kolekcjonerski Box", "Sprawdź czy w zestawie jest limitowany czerwony pad Rathalos."),
            ("z1184920188", "SMC Pentax-M 50mm f/1.4", "Jasny Obiektyw Manualny", "Sprawdź czystość szkieł (brak zamglenia / grzyba), limit <= 100 zł."),
            ("o1168492017", "Canon Autoboy 3 Prime 38mm f/2.8", "Analogowy Hit Instagrama", "Jasny obiektyw stałoogniskowy f/2.8, automatyczny AF, limit <= 100 zł.")
        ]

        md.append("| # | Model / Przedmiot | Kategoria | Kluczowa Wskazówka Snajpera | 🎯 Limit JPY | Zysk w PL | Linki Aktywne (1-Click) |")
        md.append("|:---:|---|---|---|---:|---:|---|")

        idx = 1
        deals_by_id = {}
        for d in self.raw_deals:
            if d.get("id"):
                deals_by_id[d.get("id")] = d
            if d.get("slug_id"):
                deals_by_id[d.get("slug_id")] = d
        for did, title, cat_badge, tip in top_targets:
            it = deals_by_id.get(did)
            if not it:
                continue

            est_pl = float(it.get("est_pl_value", 0))
            cat_id = it.get("category_id", "")
            query = it.get("search_query_jp", it.get("model", ""))
            encoded_q = urllib.parse.quote(query)

            # Cap
            cap_info = calculate_max_sniper_bid(est_pl, cat_id, 32.0, self.rate, self.rate_eur)
            max_bid = cap_info["max_bid_jpy"]
            guar_margin = cap_info["guaranteed_margin_pln"]

            # Camera / Lens caps
            if is_camera_item(it) or cat_id == "film_cameras_point_shoot":
                max_cam = int((MAX_CAMERA_PRICE_PLN / self.rate) // 100 * 100)
                if max_bid > max_cam:
                    max_bid = max_cam
                    rc = calculate_landed_cost(max_bid, cat_id, self.rate, self.rate_eur)
                    guar_margin = round(est_pl - rc["landed_cost_pln"], 2)

            if is_lens_item(it) or cat_id == "analog_lenses":
                max_lens = int((MAX_LENS_PRICE_PLN / self.rate) // 100 * 100)
                if max_bid > max_lens:
                    max_bid = max_lens
                    rc = calculate_landed_cost(max_bid, cat_id, self.rate, self.rate_eur)
                    guar_margin = round(est_pl - rc["landed_cost_pln"], 2)

            zen_ending_soon = f"https://zenmarket.jp/pl/yahoo.aspx?q={encoded_q}&sort=end&order=asc"
            zen_lowest = f"https://zenmarket.jp/pl/yahoo.aspx?q={encoded_q}&sort=price&order=asc"
            yahoo_closed = f"https://auctions.yahoo.co.jp/closedsearch/closedsearch?p={encoded_q}"

            zen_sniper = it.get("zenmarket_url", zen_ending_soon)
            buyee_url = it.get("buyee_url", f"https://buyee.jp/item/search/query/{encoded_q}?translationType=1")
            img_url = it.get("image_url", "./assets/images/placeholder.svg")
            img_tag = f"<img src='{img_url}' width='50' height='32' style='border-radius:4px; object-fit:contain; background:#0f172a; vertical-align:middle;' /><br>"

            links = (
                f"[🎯 Snajper ZenMarket]({zen_sniper})<br>"
                f"[⏰ Kończące się]({zen_ending_soon}) · [🪙 Od 1 JPY]({zen_lowest})<br>"
                f"[📊 Archiwum Yahoo]({yahoo_closed}) · [🛒 Buyee]({buyee_url})"
            )

            md.append(
                f"| **{idx}** | {img_tag}**{sanitize_md(it.get('model'))}**<br><small>{sanitize_md(it.get('color'))}</small> | "
                f"`{cat_badge}` | "
                f"<small>{tip}</small> | "
                f"**`{max_bid:,} JPY`**<br><small>(~{max_bid * self.rate:.0f} zł)</small> | "
                f"<strong style='color:#10b981;'>+{guar_margin:.2f} zł</strong> | "
                f"{links} |"
            )
            idx += 1

        md.append("")
        md.append("---")
        md.append("")

        # Section 4: Live Sniping Radar Terminal (Search Matrix by Category)
        md.append("## 🛰️ Terminal Wyszukiwania Licytacji (Wszystkie 11 Kategorii)")
        md.append("")
        md.append(
            "Wybierz kategorię i kliknij odpowiedni filtr, aby natychmiast załadować w panelu ZenMarket "
            "trwające japońskie aukcje przefiltrowane przez oficjalny silnik proxy:"
        )
        md.append("")
        md.append("| Kategoria | Egzemplarze / Cele | ⏰ Kończące Się (Sniping) | 💰 Od 1 JPY (Tanie) | 🔥 Najwięcej Ofert | 📊 Rzeczywiste Ceny Zamknięcia |")
        md.append("|---|---|:---:|:---:|:---:|:---:|")

        cat_radar_queries = [
            ("Nintendo 3DS & New 3DS", "New 3DS XL, New 3DS Kisekae, 3DS XL", "Newニンテンドー3DS LL 本体"),
            ("Nintendo DS & DSi LL", "DSi LL IPS, DS Lite Crimson, FF3 Limited", "Nintendo DSi LL 本体"),
            ("Game Boy Advance & Retro", "GBA SP Famicom, AGS-101, GBC Atomic Purple", "ゲームボーイアドバンスSP 本体"),
            ("PlayStation Vita Handhelds", "PCH-2000 Slim Aqua Blue, Neon Orange, OLED", "PS Vita PCH-2000 本体"),
            ("Sony PSP Handhelds", "PSP-3000 Vibrant Blue, Monster Hunter 3rd", "PSP-3000 本体"),
            ("Retro Gry Hurtowe Pakiety", "Pakiety 30-50 gier DS, GBA, PS1, PS2 (0% Baterii)", "ゲーム まとめ セット"),
            ("Wyselekcjonowane Stacjonarne", "PSone Combo LCD, GameCube Orange, PS4 Pro CIB", "PS one COMBO SCPH-130"),
            ("Kontrolery Limitowane PS5", "DualSense 30th Anniversary, Astro Bot", "DualSense 30th"),
            ("Kontrolery Limitowane PS Retro", "DualShock 4 500M, Hori Slime Dragon Quest", "スライム コントローラー PS2"),
            ("Aparaty Kompaktowe 35mm", "Autoboy 3, Espio 80, Big Mini, AF-10 (<= 100 zł)", "コンパクトフィルムカメラ"),
            ("Obiektywy Manualne", "Pentax 50/1.4, Super-Takumar 55/1.8 (<= 100 zł)", "オールドレンズ 50mm")
        ]

        for c_title, c_targets, c_query in cat_radar_queries:
            q_enc = urllib.parse.quote(c_query)
            link_end = f"[⏰ Kończące się](https://zenmarket.jp/pl/yahoo.aspx?q={q_enc}&sort=end&order=asc)"
            link_low = f"[💰 Od 1 JPY](https://zenmarket.jp/pl/yahoo.aspx?q={q_enc}&sort=price&order=asc)"
            link_bids = f"[🔥 Najwięcej Ofert](https://zenmarket.jp/pl/yahoo.aspx?q={q_enc}&sort=bids&order=desc)"
            link_closed = f"[📊 Sprawdź Ceny](https://auctions.yahoo.co.jp/closedsearch/closedsearch?p={q_enc})"

            md.append(f"| **{c_title}** | <small>{c_targets}</small> | {link_end} | {link_low} | {link_bids} | {link_closed} |")

        md.append("")
        md.append("---")
        md.append("")

        # Section 5: Practical ZenMarket Sniper Rules
        md.append("## 🛡️ Praktyczna Instrukcja: Jak Ustawić Snajpera w ZenMarket?")
        md.append("")
        md.append("1. **Zaloguj się do ZenMarket i doładuj saldo:**")
        md.append("   - Snajper wymaga, abyś posiadał na saldzie kwotę równą Twojemu maksymalnemu limitowi.")
        md.append("   - Pamiętaj: Jeśli wygrasz taniej (np. Twój limit to 15,000 JPY, a aukcja zakończy się na 9,200 JPY), **nadwyżka (5,800 JPY) natychmiast wraca na Twoje wolne saldo!**")
        md.append("2. **Otwórz wybraną aukcję z tabeli powyżej:**")
        md.append("   - Kliknij zielony przycisk **`Dodaj do Snajpera`** (zamiast standardowego 'Licytuj teraz').")
        md.append("3. **Wpisz Twardy Limit Snajpera z tabeli:**")
        md.append("   - System ZenMarket złoży Twoją ofertę dokładnie **2 minuty przed końcem aukcji**.")
        md.append("   - Jeśli nikt Cię nie przebije, wygrywasz za minimalną możliwą stawkę.")
        md.append("   - Jeśli cena przebije Twój limit – **system automatycznie odpuści**, chroniąc Twój budżet przed stratą.")
        md.append("4. **Zarządzanie Bateriami IATA (Zasada 2x Li-Ion):**")
        md.append("   - W jednej paczce lotniczej możesz skonsolidować **maksymalnie 2 urządzenia z baterią Li-Ion** (np. 1x New 3DS XL + 1x PS Vita).")
        md.append("   - Dopełniaj każdą paczkę przedmiotami o zerowej zawartości baterii (**Pakiety Gier Retro, GameCube, Aparaty Analogowe, Obiektywy**), aby rozbić koszt wysyłki na 5–8 przedmiotów!")
        md.append("")
        md.append("---")
        md.append(f"*Dashboard generated automatically by AuctionRadar & HistoryTracker. Last synchronization: {now_str}.*")

        return "\n".join(md)
