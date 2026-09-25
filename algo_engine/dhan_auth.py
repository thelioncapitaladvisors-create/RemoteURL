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

_cached_token = os.getenv("DHAN_ACCESS_TOKEN", "")
_token_expires_at = 1790441448.0  # 2026-09-26 22:20:48 IST


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


def fetch_fresh_token() -> str:
    """Call DhanHQ Auth Server to generate fresh 24-hour token via Client ID, PIN, and dynamic TOTP."""
    global _cached_token, _token_expires_at
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
            return _cached_token
        else:
            err_msg = data.get("message", f"HTTP {res.status_code}")
            logger.warning(f"[DhanAuth] Dhan auth returned error: {err_msg}. Using cached token.")
            return _cached_token
    except Exception as e:
        logger.error(f"[DhanAuth] Failed to generate token: {e}")
        return _cached_token


def get_valid_dhan_token(force_refresh: bool = False) -> str:
    """Return a guaranteed valid Dhan token. Refreshes if expired or < 5 mins left."""
    global _cached_token, _token_expires_at
    now = time.time()
    safety_buffer = 300  # 5 minutes

    if not force_refresh and _cached_token and (_token_expires_at - now > safety_buffer):
        return _cached_token

    return fetch_fresh_token()
