"""Live NBP exchange rate fetcher with fallback support for JPY and EUR."""

import urllib.request
import json
import logging
from .config import (
    DEFAULT_JPY_PLN_RATE,
    DEFAULT_EUR_PLN_RATE,
    USER_AGENT,
    REQUEST_TIMEOUT
)

NBP_JPY_API_URL = "https://api.nbp.pl/api/exchangerates/rates/a/jpy/?format=json"
NBP_EUR_API_URL = "https://api.nbp.pl/api/exchangerates/rates/a/eur/?format=json"

def get_live_nbp_rate(timeout=5):
    """
    Fetches official mid-market JPY/PLN exchange rate from Narodowy Bank Polski (NBP).
    Returns (rate, is_live) tuple.
    """
    req = urllib.request.Request(
        NBP_JPY_API_URL,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            rate = float(data["rates"][0]["mid"])
            if rate > 0:
                logging.info(f"Fetched live NBP JPY rate: 1 JPY = {rate:.6f} PLN (100 JPY ≈ {rate * 100:.2f} PLN)")
                return rate, True
    except Exception as e:
        logging.warning(f"Could not fetch live NBP JPY rate ({e}). Using fallback rate {DEFAULT_JPY_PLN_RATE:.6f}")
    
    return DEFAULT_JPY_PLN_RATE, False

def get_live_nbp_eur_rate(timeout=5):
    """
    Fetches official mid-market EUR/PLN exchange rate from Narodowy Bank Polski (NBP).
    Returns (rate, is_live) tuple.
    """
    req = urllib.request.Request(
        NBP_EUR_API_URL,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            rate = float(data["rates"][0]["mid"])
            if rate > 0:
                logging.info(f"Fetched live NBP EUR rate: 1 EUR = {rate:.4f} PLN")
                return rate, True
    except Exception as e:
        logging.warning(f"Could not fetch live NBP EUR rate ({e}). Using fallback rate {DEFAULT_EUR_PLN_RATE:.4f}")
    
    return DEFAULT_EUR_PLN_RATE, False

def get_live_rates(timeout=5):
    """Fetches both JPY and EUR live rates from NBP."""
    rate_jpy, live_jpy = get_live_nbp_rate(timeout=timeout)
    rate_eur, live_eur = get_live_nbp_eur_rate(timeout=timeout)
    return rate_jpy, rate_eur, live_jpy, live_eur

def jpy_to_pln(amount_jpy, rate=DEFAULT_JPY_PLN_RATE):
    """Safely converts JPY amount to PLN rounded to 2 decimal places."""
    if amount_jpy is None or amount_jpy < 0:
        return 0.0
    return round(float(amount_jpy) * float(rate), 2)
