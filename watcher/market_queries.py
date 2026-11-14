"""Polish market search queries and OLX slug formatting."""

import re
import unicodedata
from typing import Dict, Any, Tuple

def clean_polish_market_queries(deal: Dict[str, Any]) -> Tuple[str, str]:
    """
    Produces:
    1) clean_pl_query: optimized Polish search phrase for Allegro listings.
    2) clean_olx_slug: URL-safe, lowercase, hyphenated ASCII slug for OLX (e.g. 'ps-vita-slim').
    
    Guarantees:
    - Zero Japanese characters or kanji brackets (【...】).
    - Zero URL-breaking symbols (%26, &, +, #).
    - True Polish market keywords.
    """
    model = deal.get("model", "")
    title = deal.get("title", "")
    text = f"{model} {title}".lower()

    if any(w in text for w in ["danshari", "mystery", "karton", "pakiet", "zestaw", "mix", "hurtowy", "まとめ売り", "断捨離", "実家整理", "引退品"]):
        if "pokemon" in text or "pokémon" in text or "stwork" in text:
            pl_q = "gry pokemon nintendo"
        elif "psp" in text and any(w in text for w in ["konsol", "sztuk", "pakiety", "pakiet", "本体", "台", "3台", "5台", "10台"]):
            pl_q = "konsola psp zestaw"
        elif "3ds" in text or "ds" in text:
            pl_q = "gry nintendo ds zestaw"
        elif "gba" in text or "game boy" in text or "gb" in text:
            pl_q = "gry game boy advance zestaw"
        elif "psp" in text or "umd" in text:
            pl_q = "gry psp zestaw"
        elif "ps2" in text or "ps1" in text or "playstation 2" in text or "playstation 1" in text:
            pl_q = "gry ps2 zestaw"
        elif "sfc" in text or "super famicom" in text:
            pl_q = "gry super famicom"
        else:
            pl_q = "gry retro zestaw mix"

    elif "realforce" in text or "東プレ" in text:
        pl_q = "Topre Realforce"
    elif "hhkb" in text or "happy hacking" in text:
        pl_q = "HHKB Professional"
    elif "filco" in text or "majestouch" in text:
        pl_q = "Filco Majestouch"
    elif "keychron" in text:
        pl_q = "Keychron Hot Swap"
    elif "evangelion" in text and ("keyboard" in text or "klawiatura" in text or "キーボード" in text):
        pl_q = "Klawiatura Evangelion"
    elif "klawiatura" in text or "keyboard" in text or "キーボード" in text or "hot-swap" in text or "hotswap" in text:
        pl_q = "klawiatura mechaniczna hot swap"

    elif "mju" in text:
        pl_q = "Olympus Mju II"
    elif "pc35af" in text:
        pl_q = "Pentax PC35AF"
    elif "tw2d" in text:
        pl_q = "Nikon TW2D"
    elif "autoboy" in text or "prima" in text:
        pl_q = "Canon Autoboy"
    elif "big mini" in text:
        pl_q = "Konica Big Mini"
    elif "espio" in text:
        pl_q = "Pentax Espio"
    elif "riva" in text:
        pl_q = "Minolta Riva"
    elif "trip 35" in text:
        pl_q = "Olympus Trip 35"
    elif "myport" in text:
        pl_q = "Ricoh Myport Zoom"
    elif "cardia" in text:
        pl_q = "Fuji Cardia Mini"
    elif "af-10 twin" in text or "af 10 twin" in text:
        pl_q = "Olympus AF-10 Twin"
    elif "yashica" in text:
        pl_q = "Kyocera Yashica Zoomate"
    elif "pop efj" in text:
        pl_q = "Konica Pop EFJ"

    elif "pch-2000" in text or ("vita" in text and "slim" in text):
        pl_q = "PS Vita Slim"
    elif "pch-1000" in text or ("vita" in text and "oled" in text):
        pl_q = "PS Vita OLED"
    elif "psp-2000" in text or "psp 2000" in text:
        pl_q = "Sony PSP 2000"
    elif "psp-3000" in text or "psp 3000" in text:
        pl_q = "Sony PSP 3000"
    elif "psp-1000" in text or "psp 1000" in text:
        pl_q = "Sony PSP 1000"
    elif "new" in text and "3ds" in text and ("ll" in text or "xl" in text):
        pl_q = "New Nintendo 3DS XL"
    elif "new" in text and "3ds" in text:
        pl_q = "New Nintendo 3DS"
    elif "3ds" in text and ("ll" in text or "xl" in text):
        pl_q = "Nintendo 3DS XL"
    elif "3ds" in text:
        pl_q = "Nintendo 3DS"
    elif "2ds" in text and ("ll" in text or "xl" in text):
        pl_q = "New Nintendo 2DS XL"
    elif "2ds" in text:
        pl_q = "Nintendo 2DS"
    elif "dsi ll" in text or "dsi xl" in text:
        pl_q = "Nintendo DSi XL"
    elif "dsi" in text:
        pl_q = "Nintendo DSi"
    elif "ds lite" in text:
        pl_q = "Nintendo DS Lite"
    elif "ags-101" in text:
        pl_q = "Game Boy Advance SP AGS-101"
    elif "famicom 20th" in text or ("famicom" in text and "sp" in text):
        pl_q = "Game Boy Advance SP Famicom"
    elif "torchic" in text:
        pl_q = "Game Boy Advance SP Torchic"
    elif "advance sp" in text or "gba sp" in text:
        pl_q = "Game Boy Advance SP"
    elif "game boy color" in text or "cgb-001" in text or "gbc" in text:
        pl_q = "Game Boy Color Pokemon" if ("pokemon" in text or "pokémon" in text) else "Game Boy Color"
    elif "game boy micro" in text or "oxy-001" in text or "micro" in text:
        pl_q = "Game Boy Micro"
    elif "agb-001" in text or "advance" in text:
        pl_q = "Game Boy Advance"
    elif "psone combo" in text or "scph-130" in text:
        pl_q = "PSone LCD Combo SCPH-130"
    elif "gamecube" in text and "spice" in text:
        pl_q = "GameCube Spice Orange"
    elif "gamecube" in text:
        pl_q = "Nintendo GameCube"
    elif "ps4 pro" in text and "monster hunter" in text:
        pl_q = "PS4 Pro Monster Hunter"
    elif "ps4" in text and "metal gear" in text:
        pl_q = "PS4 Metal Gear Solid V"

    elif "astro bot" in text:
        pl_q = "DualSense Astro Bot"
    elif "monster hunter" in text and "dualsense" in text:
        pl_q = "DualSense Monster Hunter"
    elif "god of war" in text and "dualsense" in text:
        pl_q = "DualSense God of War"
    elif "final fantasy" in text and "dualsense" in text:
        pl_q = "DualSense Final Fantasy XVI"
    elif "spider-man" in text and "dualsense" in text:
        pl_q = "DualSense Spider-Man 2"
    elif "30th" in text and "dualsense" in text:
        pl_q = "DualSense 30th Anniversary"
    elif "slime" in text:
        pl_q = "Dragon Quest Slime PS2"
    elif "rathalos" in text or ("monster hunter" in text and "dualshock" in text):
        pl_q = "DualShock 4 Monster Hunter"
    elif "berry blue" in text:
        pl_q = "DualShock 4 Berry Blue"
    elif "500 million" in text:
        pl_q = "DualShock 4 500 Million"
    elif "death stranding" in text:
        pl_q = "DualShock 4 Death Stranding"
    elif "metallic blue" in text:
        pl_q = "DualShock 3 Metallic Blue"
    elif "island blue" in text:
        pl_q = "DualShock Island Blue PS1"
    elif "emerald green" in text:
        pl_q = "DualShock 2 Emerald Green"
    elif "dualsense" in text:
        pl_q = "DualSense PS5"
    elif "dualshock 4" in text:
        pl_q = "DualShock 4"

    elif "super-takumar 55mm" in text or "takumar 55mm" in text:
        pl_q = "Super-Takumar 55mm 1.8"
    elif "pentax-m 50mm" in text and "1.4" in text:
        pl_q = "Pentax-M 50mm 1.4"
    elif "pentax-m 50mm" in text:
        pl_q = "Pentax-M 50mm f2"
    elif "canon fd 50mm" in text:
        pl_q = "Canon FD 50mm 1.8"
    elif "minolta md 50mm" in text:
        pl_q = "Minolta MD 50mm 1.7"
    elif "zuiko 50mm" in text:
        pl_q = "Zuiko 50mm 1.8"
    elif "pentax 28mm" in text:
        pl_q = "Pentax 28mm 2.8"

    else:
        t = re.sub(r"[\u3000-\u303f\u3040-\u309f\u30a0-\u30ff\uff00-\uffef\u4e00-\u9faf]", "", model or title)
        t = re.sub(r"【.*?】", "", t)
        t = re.sub(r"\(.*?\)", "", t)
        t = t.replace("&", " i ").replace("/", " ")
        t = re.sub(r"[^a-zA-Z0-9\sąćęłńóśźżĄĆĘŁŃÓŚŹŻ-]", " ", t)
        words = t.split()[:4]
        pl_q = " ".join(words) if words else "retro gry"

    slug_base = unicodedata.normalize("NFKD", pl_q).encode("ascii", "ignore").decode("utf-8").lower()
    clean_olx_slug = re.sub(r"[^a-z0-9]+", "-", slug_base).strip("-")
    if not clean_olx_slug:
        clean_olx_slug = "retro-gry"
    return pl_q, clean_olx_slug
