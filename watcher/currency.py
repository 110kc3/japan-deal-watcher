"""Live NBP exchange rate fetcher with fallback support."""

import urllib.request
import json
import logging
from .config import DEFAULT_JPY_PLN_RATE, USER_AGENT, REQUEST_TIMEOUT

NBP_API_URL = "https://api.nbp.pl/api/exchangerates/rates/a/jpy/?format=json"

def get_live_nbp_rate(timeout=5):
    """
    Fetches official mid-market JPY/PLN exchange rate from Narodowy Bank Polski (NBP).
    Returns (rate, is_live) tuple.
    """
    req = urllib.request.Request(
        NBP_API_URL,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            rate = float(data["rates"][0]["mid"])
            if rate > 0:
                logging.info(f"Fetched live NBP rate: 1 JPY = {rate:.6f} PLN (100 JPY ≈ {rate * 100:.2f} PLN)")
                return rate, True
    except Exception as e:
        logging.warning(f"Could not fetch live NBP rate ({e}). Using fallback rate {DEFAULT_JPY_PLN_RATE:.6f}")
    
    return DEFAULT_JPY_PLN_RATE, False

def jpy_to_pln(amount_jpy, rate=DEFAULT_JPY_PLN_RATE):
    """Safely converts JPY amount to PLN rounded to 2 decimal places."""
    if amount_jpy is None or amount_jpy < 0:
        return 0.0
    return round(float(amount_jpy) * float(rate), 2)
