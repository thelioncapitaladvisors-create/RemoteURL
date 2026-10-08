"""
algo_engine.dhan_auth — Autonomous DhanHQ Self-Healing Token Engine
===================================================================

Provides zero-touch dynamic TOTP token generation and renewal for DhanHQ.
"""

import os
import time
import base64
import struct
import hmac
import hashlib
import datetime
import requests
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

DHAN_CLIENT_ID = os.getenv("DHAN_CLIENT_ID", "1100428069")
DHAN_PIN = os.getenv("DHAN_PIN", "871346")
DHAN_TOTP_SECRET = os.getenv("DHAN_TOTP_SECRET", "N5ZUIALJCBGJ63YS2DUB3BLW7EEPBJU2")

TOKEN_CACHE_FILE = "/tmp/dhan_token_cache.json"

_cached_token = os.getenv("DHAN_ACCESS_TOKEN", "")
_token_expires_at = 0.0

# Try loading persisted token from disk on module load
try:
    if os.path.exists(TOKEN_CACHE_FILE):
        import json
        with open(TOKEN_CACHE_FILE, "r") as f:
            file_data = json.load(f)
            exp_sec = file_data.get("expires_at", 0) / 1000.0
            if file_data.get("token") and exp_sec > time.time():
                _cached_token = file_data["token"]
                _token_expires_at = exp_sec
                logger.info(f"[DhanAuth] Loaded persisted token from disk. Valid until {exp_sec}")
except Exception:
    pass


def generate_totp(secret: str = DHAN_TOTP_SECRET) -> str:
    """Generate 6-digit TOTP code from Base32 secret using HMAC-SHA1 (RFC 6238)."""
    clean_secret = secret.replace(" ", "").replace("-", "").upper()
    key = base64.b32decode(clean_secret, True)
    now = int(time.time())
    counter = struct.pack(">Q", now // 30)
    mac = hmac.new(key, counter, hashlib.sha1).digest()
    offset = mac[-1] & 0x0F
    code = struct.unpack(">I", mac[offset : offset + 4])[0] & 0x7FFFFFFF
    return f"{code % 1000000:06d}"


_last_totp_attempt = 0.0


def fetch_fresh_token() -> str:
    """Call DhanHQ Auth Server to generate fresh 24-hour token via Client ID, PIN, and dynamic TOTP."""
    global _cached_token, _token_expires_at, _last_totp_attempt
    now = time.time()
    if now - _last_totp_attempt < 125.0 and _cached_token and _token_expires_at > now:
        logger.info("[DhanAuth] Enforcing 2-minute cooldown between TOTP requests. Using cached token.")
        return _cached_token

    _last_totp_attempt = now
    totp = generate_totp()
    url = "https://auth.dhan.co/app/generateAccessToken"
    params = {
        "dhanClientId": DHAN_CLIENT_ID,
        "pin": DHAN_PIN,
        "totp": totp,
    }

    logger.info(f"[DhanAuth] Requesting fresh token for client {DHAN_CLIENT_ID} with dynamic TOTP...")
    try:
        res = requests.post(url, params=params, timeout=10)
        data = res.json()
        if res.status_code == 200 and data.get("accessToken"):
            _cached_token = data["accessToken"]
            # Parse JWT exp
            try:
                import json
                payload_part = _cached_token.split(".")[1]
                # pad base64
                payload_part += "=" * (-len(payload_part) % 4)
                payload = json.loads(base64.urlsafe_b64decode(payload_part).decode("utf-8"))
                _token_expires_at = float(payload.get("exp", time.time() + 86400))
            except Exception:
                _token_expires_at = time.time() + 86400

            logger.info(f"[DhanAuth] Successfully generated fresh Dhan access token (valid until {_token_expires_at}).")
            try:
                import json
                with open(TOKEN_CACHE_FILE, "w") as f:
                    json.dump({
                        "token": _cached_token,
                        "expires_at": int(_token_expires_at * 1000)
                    }, f)
            except Exception:
                pass
            return _cached_token
        else:
            err_msg = data.get("message", f"HTTP {res.status_code}")
            logger.warning(f"[DhanAuth] Dhan auth returned error: {err_msg}. Using cached token.")
            return _cached_token
    except Exception as e:
        logger.error(f"[DhanAuth] Failed to generate token: {e}")
        return _cached_token


SUPABASE_URL = os.getenv("SUPABASE_URL") or "https://dwepduvhzuhzeehbeaaz.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR3ZXBkdXZoenVoemVlaGJlYWF6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NzMwMDY3NSwiZXhwIjoyMDkyODc2Njc1fQ.4gnT-NbFvQp_8PwkCHqzMvt1KGXwyZXH6kpSqwC70qg"


def get_token_from_supabase() -> tuple[str, float] | None:
    """Fetch active token from Supabase shared cache."""
    try:
        url = f"{SUPABASE_URL}/rest/v1/dhan_token?id=eq.1&select=access_token,expires_at"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}"
        }
        res = requests.get(url, headers=headers, timeout=4)
        if res.status_code == 200:
            data = res.json()
            if data and len(data) > 0:
                t = data[0].get("access_token")
                exp = float(data[0].get("expires_at", 0)) / 1000.0
                if t and exp > time.time():
                    return t, exp
    except Exception as e:
        logger.debug(f"[DhanAuth] Supabase token check warning: {e}")
    return None


def save_token_to_supabase(token: str, exp_sec: float):
    """Save token to Supabase shared cache."""
    try:
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates"
        }
        payload = {
            "id": 1,
            "access_token": token,
            "expires_at": int(exp_sec * 1000),
            "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        requests.post(f"{SUPABASE_URL}/rest/v1/dhan_token", headers=headers, json=payload, timeout=4)
    except Exception as e:
        logger.debug(f"[DhanAuth] Failed to save token to Supabase: {e}")


def get_valid_dhan_token(force_refresh: bool = False) -> str:
    """Return a guaranteed valid Dhan token. Refreshes if expired or < 5 mins left."""
    global _cached_token, _token_expires_at
    now = time.time()
    safety_buffer = 300  # 5 minutes

    if not force_refresh and _cached_token and (_token_expires_at - now > safety_buffer):
        return _cached_token

    # 1. Check Supabase shared cache first
    if not force_refresh:
        sb_res = get_token_from_supabase()
        if sb_res:
            sb_token, sb_exp = sb_res
            if (sb_exp - now) > safety_buffer:
                _cached_token = sb_token
                _token_expires_at = sb_exp
                logger.info(f"[DhanAuth] Loaded valid token from Supabase shared cache. Valid until {sb_exp}")
                return _cached_token

    # 2. Check disk cache before making network request
    if not force_refresh and os.path.exists(TOKEN_CACHE_FILE):
        try:
            import json
            with open(TOKEN_CACHE_FILE, "r") as f:
                file_data = json.load(f)
                exp_sec = file_data.get("expires_at", 0) / 1000.0
                if file_data.get("token") and (exp_sec - now > safety_buffer):
                    _cached_token = file_data["token"]
                    _token_expires_at = exp_sec
                    return _cached_token
        except Exception:
            pass

    fresh = fetch_fresh_token()
    if fresh and _token_expires_at > now:
        save_token_to_supabase(fresh, _token_expires_at)
    return fresh
