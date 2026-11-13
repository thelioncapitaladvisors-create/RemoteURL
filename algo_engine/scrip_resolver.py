"""
algo_engine.scrip_resolver — Automated Dynamic DhanHQ MCX Front-Month Scrip Resolver
===================================================================================

Streams DhanHQ's daily security master CSV (https://images.dhan.co/api-data/api-scrip-master.csv),
identifies the active front-month futures contract for all MCX commodities, and updates
in-memory mappings, disk caches, and Supabase system_config.
"""

import os
import io
import csv
import json
import time
import datetime
import logging
import requests
from typing import Dict, Any, Tuple, Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

SUPABASE_URL = os.getenv("SUPABASE_URL") or "https://dwepduvhzuhzeehbeaaz.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR3ZXBkdXZoenVoemVlaGJlYWF6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NzMwMDY3NSwiZXhwIjoyMDkyODc2Njc1fQ.4gnT-NbFvQp_8PwkCHqzMvt1KGXwyZXH6kpSqwC70qg"

DHAN_SCRIP_MASTER_URL = "https://images.dhan.co/api-data/api-scrip-master.csv"
CACHE_FILE = "/tmp/dhan_mcx_contracts.json"

TARGET_MCX_COMMODITIES = [
    "CRUDEOIL",
    "CRUDEOILM",
    "NATURALGAS",
    "GOLD",
    "GOLDM",
    "SILVER",
    "SILVERM",
    "COPPER",
    "ZINC",
    "ALUMINIUM",
    "ALUMINI"
]

# Baseline fallback if network is completely unreachable
FALLBACK_MCX_MAP = {
    "CRUDEOIL": {"security_id": "573422", "lot_size": 100, "expiry": "2026-11-19 23:30:00"},
    "CRUDEOILM": {"security_id": "573423", "lot_size": 10, "expiry": "2026-11-19 23:30:00"},
    "NATURALGAS": {"security_id": "574319", "lot_size": 1250, "expiry": "2026-11-24 23:30:00"},
    "GOLD": {"security_id": "495213", "lot_size": 1, "expiry": "2026-12-04 23:30:00"},
    "GOLDM": {"security_id": "575011", "lot_size": 1, "expiry": "2026-12-04 23:30:00"},
    "SILVER": {"security_id": "495214", "lot_size": 30, "expiry": "2026-12-04 23:30:00"},
    "SILVERM": {"security_id": "483080", "lot_size": 5, "expiry": "2026-11-30 23:30:00"},
    "COPPER": {"security_id": "578634", "lot_size": 2500, "expiry": "2026-11-30 23:30:00"},
    "ZINC": {"security_id": "578638", "lot_size": 5000, "expiry": "2026-11-30 23:30:00"},
    "ALUMINIUM": {"security_id": "578633", "lot_size": 5000, "expiry": "2026-11-30 23:30:00"},
    "ALUMINI": {"security_id": "578632", "lot_size": 1000, "expiry": "2026-11-30 23:30:00"}
}

_memory_cache: Dict[str, Dict[str, Any]] = {}
_memory_cache_date: str = ""


def get_ist_now() -> datetime.datetime:
    """Return current datetime in Indian Standard Time (UTC + 5:30)."""
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30)))


def get_supabase_mcx_symbols() -> Optional[Dict[str, Dict[str, Any]]]:
    """Fetch active MCX front-month symbols from Supabase system_config."""
    try:
        url = f"{SUPABASE_URL}/rest/v1/system_config?key=eq.mcx_front_month_symbols&select=value,updated_at"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}"
        }
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if data and len(data) > 0:
                val = data[0].get("value", {})
                updated_at = data[0].get("updated_at", "")
                today_str = get_ist_now().strftime("%Y-%m-%d")
                if val and updated_at.startswith(today_str):
                    return val
                # Even if older, return if all keys exist as warm cache
                if val and all(k in val for k in ["CRUDEOIL", "GOLD", "SILVER"]):
                    return val
    except Exception as e:
        logger.debug(f"[ScripResolver] Supabase read error: {e}")
    return None


def save_supabase_mcx_symbols(resolved: Dict[str, Dict[str, Any]]) -> bool:
    """Persist resolved MCX symbols to Supabase system_config."""
    try:
        url = f"{SUPABASE_URL}/rest/v1/system_config"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates"
        }
        payload = {
            "key": "mcx_front_month_symbols",
            "value": resolved,
            "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        res = requests.post(url, headers=headers, json=payload, timeout=5)
        return res.status_code in (200, 201)
    except Exception as e:
        logger.warning(f"[ScripResolver] Failed to persist symbols to Supabase: {e}")
        return False


def parse_scrip_master_csv(csv_content: str) -> Dict[str, Dict[str, Any]]:
    """Parse CSV content and extract active front-month contracts for MCX commodities."""
    reader = csv.DictReader(io.StringIO(csv_content))
    now_ist_str = get_ist_now().strftime("%Y-%m-%d %H:%M:%S")
    
    candidates = {s: [] for s in TARGET_MCX_COMMODITIES}
    
    for row in reader:
        # Gated to MCX Commodity Futures
        if row.get("SEM_EXM_EXCH_ID") == "MCX" and row.get("SEM_INSTRUMENT_NAME") == "FUTCOM":
            sym = row.get("SM_SYMBOL_NAME", "").strip()
            custom = row.get("SEM_CUSTOM_SYMBOL", "").strip()
            trading_sym = row.get("SEM_TRADING_SYMBOL", "").strip()
            exp = row.get("SEM_EXPIRY_DATE", "").strip()
            
            # Exclude already-expired contracts
            if exp and exp < now_ist_str:
                continue
                
            for target in TARGET_MCX_COMMODITIES:
                if sym == target or custom.startswith(target + " ") or trading_sym.startswith(target + "-"):
                    try:
                        lot = float(row.get("SEM_LOT_UNITS", "1.0") or 1.0)
                    except ValueError:
                        lot = 1.0
                    try:
                        tick = float(row.get("SEM_TICK_SIZE", "0.05") or 0.05)
                    except ValueError:
                        tick = 0.05

                    candidates[target].append({
                        "security_id": str(row.get("SEM_SMST_SECURITY_ID", "")).strip(),
                        "trading_symbol": trading_sym,
                        "custom_symbol": custom,
                        "expiry": exp,
                        "lot_size": lot,
                        "tick_size": tick,
                        "exchange_segment": 5,
                        "instrument": "FUTCOM",
                        "series": "FUT"
                    })
                    break

    front_month = {}
    for target in TARGET_MCX_COMMODITIES:
        if candidates[target]:
            # Sort ascending by expiry date -> index 0 is nearest unexpired front-month contract
            candidates[target].sort(key=lambda x: x["expiry"])
            front_month[target] = candidates[target][0]
        else:
            # Fallback if specific symbol not found in master
            if target in FALLBACK_MCX_MAP:
                front_month[target] = FALLBACK_MCX_MAP[target]

    return front_month


def resolve_mcx_front_month_contracts(force_refresh: bool = False) -> Dict[str, Dict[str, Any]]:
    """
    Resolve active front-month MCX contracts with multi-tier caching:
    1. In-memory cache (same day)
    2. Local disk cache (/tmp/dhan_mcx_contracts.json)
    3. Supabase system_config shared cache
    4. Dhan Scrip Master CSV download & parse
    """
    global _memory_cache, _memory_cache_date
    today_str = get_ist_now().strftime("%Y-%m-%d")

    # 1. In-memory cache
    if not force_refresh and _memory_cache and _memory_cache_date == today_str:
        return _memory_cache

    # 2. Local disk cache
    if not force_refresh and os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                disk_data = json.load(f)
                if disk_data.get("date") == today_str and disk_data.get("symbols"):
                    _memory_cache = disk_data["symbols"]
                    _memory_cache_date = today_str
                    logger.info("[ScripResolver] Loaded MCX front-month contracts from local disk cache.")
                    return _memory_cache
        except Exception:
            pass

    # 3. Supabase shared cache
    if not force_refresh:
        sb_symbols = get_supabase_mcx_symbols()
        if sb_symbols:
            _memory_cache = sb_symbols
            _memory_cache_date = today_str
            # Save to disk cache for fast local reuse
            try:
                with open(CACHE_FILE, "w") as f:
                    json.dump({"date": today_str, "symbols": _memory_cache}, f)
            except Exception:
                pass
            logger.info("[ScripResolver] Loaded MCX front-month contracts from Supabase shared cache.")
            return _memory_cache

    # 4. Fetch from Dhan Scrip Master CSV
    logger.info("[ScripResolver] Downloading fresh Dhan scrip master from images.dhan.co...")
    try:
        res = requests.get(DHAN_SCRIP_MASTER_URL, timeout=25)
        if res.status_code == 200 and res.content:
            resolved = parse_scrip_master_csv(res.content.decode("utf-8", errors="ignore"))
            if resolved:
                _memory_cache = resolved
                _memory_cache_date = today_str
                
                # Persist to disk
                try:
                    with open(CACHE_FILE, "w") as f:
                        json.dump({"date": today_str, "symbols": resolved}, f)
                except Exception:
                    pass
                
                # Persist to Supabase
                save_supabase_mcx_symbols(resolved)
                logger.info(f"[ScripResolver] Successfully resolved {len(resolved)} MCX front-month contracts and synced to Supabase.")
                return resolved
    except Exception as e:
        logger.error(f"[ScripResolver] Failed to download or parse Dhan scrip master: {e}")

    # Safe fallback if all tiers fail
    if _memory_cache:
        return _memory_cache
    return FALLBACK_MCX_MAP


def get_mcx_symbol_map() -> Dict[str, Tuple[int, str]]:
    """Return dict mapping symbol -> (exchange_segment, security_id) for BaseFeed / DhanFeed."""
    contracts = resolve_mcx_front_month_contracts()
    return {
        sym: (5, str(data.get("security_id", "")))
        for sym, data in contracts.items()
        if data.get("security_id")
    }


def get_mcx_executor_map() -> Dict[str, Dict[str, Any]]:
    """Return dict mapping symbol -> {security_id, lot_size} for dhan_executor.py."""
    contracts = resolve_mcx_front_month_contracts()
    return {
        sym: {
            "security_id": str(data.get("security_id", "")),
            "lot_size": int(data.get("lot_size", 1.0))
        }
        for sym, data in contracts.items()
        if data.get("security_id")
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    print("=== DhanHQ Dynamic MCX Scrip Resolver ===")
    resolved = resolve_mcx_front_month_contracts(force_refresh=True)
    for sym, details in resolved.items():
        print(f"{sym:12} -> Sec ID: {details.get('security_id'):6} | {details.get('trading_symbol', ''):25} | Expiry: {details.get('expiry', '')}")
