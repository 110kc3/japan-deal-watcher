"""Product Matching & Verification Engine.

Validates that observed Japanese listings match their intended target models,
preventing misattribution (e.g. games valued as consoles, silicone covers as consoles,
shoes as consoles, or zoom cameras as rare prime cameras).
"""

import re
from typing import Dict, Any, Tuple, Optional, List


# Keywords indicating packaging, manuals, accessories, or protective gear rather than the actual console/device
ACCESSORY_AND_TRAP_PATTERNS = [
    # Boxes & packaging only
    (r"(?:外箱|空箱|箱のみ|化粧箱のみ|元箱のみ|パッケージのみ|外箱のみ)", "Tylko pudełko / opakowanie (brak konsoli)"),
    # Manuals & documentation only
    (r"(?:取扱説明書|説明書のみ|マニュアルのみ|取説のみ|チラシのみ)", "Tylko instrukcja obsługi (brak sprzętu)"),
    # Silicone covers, cases, shells, pouches
    (r"(?:シリコンカバー|シリコンケース|ハードカバー|保護カバー|カバーのみ|ケースのみ|ポーチのみ|収納ケース|キャリングケース)", "Tylko pokrowiec / etui / silikon (brak konsoli)"),
    # Shell replacement / parts only
    (r"(?:交換用シェル|交換用外装|ハウジングシェル|シェルのみ|外装のみ|フロントパネル|バックパネル)", "Tylko obudowa / części wymienne"),
    # Screen protector / films
    (r"(?:保護フィルム|液晶フィルム|ガラスフィルム|保護シート)", "Tylko folia / szkło ochronne"),
    # Cables & chargers only
    (r"(?:充電器のみ|ACアダプタ[ー]?のみ|電源コードのみ|ケーブルのみ|USBケーブルのみ)", "Tylko ładowarka / kabel (brak konsoli)"),
    # Non-electronic / apparel / shoes
    (r"(?:ASICS|SUKU2|スクスク|スニーカー|シューズ|靴|キッズシューズ|スリッポン|サンダル|ブーツ|ウェア|パンツ|Tシャツ)", "Odzież / obuwie (błędna kategoria)"),
]

# Software / game indicators when expecting console hardware
SOFTWARE_PATTERNS = [
    (r"(?:[0-9一二三四五六七八九十]+\s*本セット|[0-9]+\s*本まとめ|ソフト\s*[0-9]+\s*本|ゲームソフト\s*[0-9]+\s*点)", "Pakiet gier / oprogramowania (nie konsola)"),
    (r"(?:カセットのみ|ソフトのみ|ソフト単品|ROMカセット|ディスクのみ|UMDのみ|ゲームディスク)", "Tylko nośnik gry (nie konsola)"),
]

# Zoom exclusions for prime cameras (e.g. Olympus Mju-II 35mm f/2.8 prime)
ZOOM_EXCLUSIONS = [
    r"zoom",
    r"ズーム",
    r"zoom\s*140",
    r"zoom\s*115",
    r"zoom\s*80",
    r"zoom\s*70",
    r"panorama",  # Often associated with Mju Zoom Panorama
]

# PC35AF-M motorized exclusions for Pentax PC35AF (manual thumbwheel required)
PC35AF_M_EXCLUSIONS = [
    r"pc35af[- ]?m",
    r"pc35afm",
    r"pc[- ]?35af[- ]?m",
]


class ProductMatchResult:
    """Represents the verification result of a listing against its target."""

    def __init__(
        self,
        is_match: bool,
        reason: str = "",
        matched_category: str = "",
        confidence: str = "high",
        details: Optional[Dict[str, Any]] = None
    ):
        self.is_match = is_match
        self.reason = reason
        self.matched_category = matched_category
        self.confidence = confidence
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_match": self.is_match,
            "reason": self.reason,
            "matched_category": self.matched_category,
            "confidence": self.confidence,
            "details": self.details,
        }


class ProductMatcher:
    """
    Validates product identity between target specification and raw marketplace listing.
    """

    @classmethod
    def verify_deal(cls, target: Dict[str, Any], listing: Dict[str, Any]) -> ProductMatchResult:
        """
        Compares target specification (model, category, expected type)
        with observed listing (raw Japanese title, description, category).
        """
        target_model = target.get("model") or listing.get("model") or ""
        target_cat = target.get("category_id") or listing.get("category_id") or ""
        raw_seller_title = (listing.get("title") or listing.get("seller_title") or listing.get("raw_title") or "").strip()
        listing_title = raw_seller_title if raw_seller_title else target_model
        item_id = listing.get("id") or listing.get("mercari_id") or target.get("id") or ""

        # Normalize text for inspection
        title_lower = listing_title.lower()

        # If both title and model are completely missing, cannot verify identity
        if not listing_title:
            return ProductMatchResult(
                is_match=False,
                reason="Brak japońskiego tytułu oferty – niemożliwa weryfikacja tożsamości",
                confidence="uncertain"
            )

        # 1. Hard check: Shoes / Apparel / Non-gaming traps
        for pattern, desc in ACCESSORY_AND_TRAP_PATTERNS:
            if re.search(pattern, listing_title, re.IGNORECASE):
                # Check if this is shoes/apparel
                if "ASICS" in pattern or "スニーカー" in pattern:
                    return ProductMatchResult(
                        is_match=False,
                        reason=f"Niedozwolony produkt: wykryto artykuł obuwniczy/odzieżowy ({desc})",
                        confidence="certain",
                        details={"item_id": item_id, "trap": desc, "title": listing_title}
                    )
                # If target is console hardware, accessories/boxes/cases are disqualified
                if cls._is_console_target(target_cat, target_model):
                    return ProductMatchResult(
                        is_match=False,
                        reason=f"Niezgodność typu produktu: oferta dotyczy akcesorium/opakowania, a nie konsoli ({desc})",
                        confidence="certain",
                        details={"item_id": item_id, "trap": desc, "title": listing_title}
                    )

        # 2. Hard check: Games / Software when expecting Console Hardware
        if cls._is_console_target(target_cat, target_model):
            # Check software bundle patterns
            for pattern, desc in SOFTWARE_PATTERNS:
                if re.search(pattern, listing_title, re.IGNORECASE):
                    return ProductMatchResult(
                        is_match=False,
                        reason=f"Niezgodność typu produktu: oferta zawiera gry/oprogramowanie zamiast konsoli ({desc})",
                        confidence="certain",
                        details={"item_id": item_id, "title": listing_title}
                    )
            # Check for multi-pack titles like "PS4 メタルギアソリッドV 2本セット"
            if re.search(r"(?:2本|3本|4本|5本|ソフト)?\s*セット", listing_title) and not cls._is_lot_target(target_cat, target_model):
                if any(kw in title_lower for kw in ["ソフト", "メタルギア", "ゲーム"]):
                    return ProductMatchResult(
                        is_match=False,
                        reason="Niezgodność typu produktu: zestaw gier (software bundle) zamiast konsoli sprzętowej",
                        confidence="certain",
                        details={"item_id": item_id, "title": listing_title}
                    )

        # 3. Camera / Lens Specific Matching:
        # A. Olympus Mju-II Prime f/2.8 vs Mju Zoom
        if "mju" in target_model.lower() or "μ" in target_model.lower() or "mju-ii" in target_model.lower():
            if "prime" in target_model.lower() or "35mm" in target_model.lower() or "f/2.8" in target_model.lower():
                # Target requires prime! Reject Zoom variants
                for z_pat in ZOOM_EXCLUSIONS:
                    if re.search(r"\b" + z_pat, title_lower) or z_pat in title_lower:
                        return ProductMatchResult(
                            is_match=False,
                            reason=f"Niezgodność modelu optyki: wykryto wariant zmiennoogniskowy Zoom ({z_pat}), podczas gdy wymagany jest rzadki aparat stałoogniskowy Prime 35mm f/2.8",
                            confidence="certain",
                            details={"item_id": item_id, "title": listing_title}
                        )

        # B. Pentax PC35AF manual vs motorized PC35AF-M
        if "pc35af" in target_model.lower():
            if "pc35af-m" not in target_model.lower() and "motor" not in target_model.lower():
                for m_pat in PC35AF_M_EXCLUSIONS:
                    if re.search(m_pat, title_lower):
                        return ProductMatchResult(
                            is_match=False,
                            reason="Niezgodność wariantu: wykryto zmotoryzowany model PC35AF-M, wymagany klasyczny manualny PC35AF",
                            confidence="certain",
                            details={"item_id": item_id, "title": listing_title}
                        )

        # 4. Check for Empty Box / Manual keywords explicitly in console titles
        if cls._is_console_target(target_cat, target_model):
            if "外箱" in listing_title and "本体" not in listing_title:
                return ProductMatchResult(
                    is_match=False,
                    reason="Brak konsoli w ofercie: oferta zawiera tylko pudełko zewnętrzne (外箱) bez konsoli (本体)",
                    confidence="certain",
                    details={"item_id": item_id, "title": listing_title}
                )
            if "取扱説明書" in listing_title and "本体" not in listing_title:
                return ProductMatchResult(
                    is_match=False,
                    reason="Brak konsoli w ofercie: oferta zawiera tylko instrukcję obsługi (取扱説明書)",
                    confidence="certain",
                    details={"item_id": item_id, "title": listing_title}
                )

        return ProductMatchResult(
            is_match=True,
            reason="Zweryfikowano zgodność modelu i typu sprzętu",
            confidence="high"
        )

    @staticmethod
    def _is_console_target(category_id: str, model_name: str) -> bool:
        """Determines if the target is console hardware."""
        cat = (category_id or "").lower()
        mod = (model_name or "").lower()

        console_cats = [
            "nintendo_3ds_handhelds",
            "nintendo_ds_handhelds",
            "gameboy_advance_retro",
            "ps_vita",
            "psp_handheld",
            "ps1_consoles",
            "retro_consoles_no_battery",
            "high_margin_curated_consoles",
        ]
        if any(c in cat for c in console_cats):
            # Exclude game bundles or controllers if specified in model
            if "kontroler" in mod or "pad" in mod or "dualshock" in mod:
                return False
            return True

        # Check model name indicators
        console_keywords = ["konsola", "console", "ps4", "playstation", "ds lite", "gba sp", "psp", "3ds", "vita"]
        return any(k in mod for k in console_keywords)

    @staticmethod
    def _is_lot_target(category_id: str, model_name: str) -> bool:
        """Determines if the target is intentionally a game software lot."""
        cat = (category_id or "").lower()
        mod = (model_name or "").lower()
        return "retro_games_mix" in cat or "danshari" in cat or "pakiet" in mod or "lot" in mod or "zestaw" in mod
