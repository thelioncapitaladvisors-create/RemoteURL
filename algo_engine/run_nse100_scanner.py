#!/usr/bin/env python3
"""
algo_engine.run_nse100_scanner — Top 100 Liquid NSE Stocks 15-Minute Scanner Runner
==================================================================================

Provides an autonomous CLI runner for scanning the Top 100 NSE liquid universe
every 15 minutes using DhanHQ market data and evaluating all 13 strategy categories
and Day Type blueprints. Detected signals are synced to Supabase `shadow_signals`.

Usage:
    # Run a single scan across all 100 stocks:
    python3 algo_engine/run_nse100_scanner.py --once

    # Test with first 10 stocks in mock mode:
    python3 algo_engine/run_nse100_scanner.py --limit 10 --mock --once

    # Run continuously every 15 minutes during market hours:
    python3 algo_engine/run_nse100_scanner.py --interval 900
"""

from __future__ import annotations
import os
import sys
import time
import signal
import argparse
import logging
from pathlib import Path

# Add project root and algo_engine to sys.path
_current_dir = Path(__file__).resolve().parent
_parent_dir = _current_dir.parent

if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))
if str(_current_dir) not in sys.path:
    sys.path.insert(0, str(_current_dir))

# Ensure working directory allows finding .env
if not os.path.exists(".env") and os.path.exists(str(_current_dir / ".env")):
    os.chdir(str(_current_dir))

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("NSE100Runner")

from algo_engine.nse100_scanner import NSE100Scanner


def main():
    parser = argparse.ArgumentParser(description="TLCS 15-Minute Black Box Scanner (NSE Equities + MCX Commodities)")
    parser.add_argument("--once", action="store_true", help="Run one scan cycle and exit")
    parser.add_argument("--mock", action="store_true", help="Force mock data mode without live API calls")
    parser.add_argument("--market", type=str, default="all", choices=["all", "nse", "mcx"], help="Market universe to scan: 'all' (NSE + MCX), 'nse', or 'mcx'")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of symbols to scan (for testing)")
    parser.add_argument("--interval", type=int, default=900, help="Scan loop interval in seconds (default: 900s / 15m)")
    parser.add_argument("--sweep-close", type=str, nargs="?", const="ALL", default=None, help="Run market close exit sweep on shadow_signals (NSE, MCX, or ALL) and exit immediately")
    args = parser.parse_args()

    # Determine mock mode: explicit flag or absence of credentials
    from algo_engine.dhan_auth import get_valid_dhan_token
    token = get_valid_dhan_token()
    has_creds = bool((os.getenv("DHAN_CLIENT_ID") or "1100428069") and token)
    mock_mode = args.mock or (not has_creds)

    if mock_mode and not args.mock:
        logger.info("[NSE100Runner] No valid Dhan credentials available. Running in simulation/mock mode.")
    elif not mock_mode:
        logger.info(f"[NSE100Runner] Live Dhan credentials verified. Ingesting live 15m candles from DhanHQ ({args.market.upper()}).")

    scanner = NSE100Scanner(mock_mode=mock_mode, market=args.market)

    if args.sweep_close:
        target_mkt = args.sweep_close.upper()
        logger.info(f"[NSE100Runner] Manual --sweep-close flag detected ({target_mkt}). Sweeping open trades to exit...")
        closed = scanner.exit_all_live_trades_at_market_close(target_mkt)
        logger.info(f"[NSE100Runner] Market close sweep completed ({target_mkt}). Settled {closed} trades.")
        return

    running = True

    def _sig_handler(signum, frame):
        nonlocal running
        logger.info(f"[NSE100Runner] Received shutdown signal ({signum}). Exiting cleanly...")
        running = False

    signal.signal(signal.SIGINT, _sig_handler)
    signal.signal(signal.SIGTERM, _sig_handler)

    logger.info(f"[NSE100Runner] Initialized. Market: {args.market.upper()}. Universe: {len(scanner.symbols)} assets. Interval: {args.interval}s.")

    while running:
        cycle_start = time.time()
        try:
            signals = scanner.run_scan_cycle(limit=args.limit)
            logger.info(f"[NSE100Runner] Cycle completed. {len(signals)} signals generated.")
        except Exception as e:
            logger.error(f"[NSE100Runner] Error in scan cycle: {e}", exc_info=True)

        if args.once:
            break

        elapsed = time.time() - cycle_start
        sleep_time = max(1, args.interval - int(elapsed))
        logger.info(f"[NSE100Runner] Sleeping {sleep_time}s until next 15m candle close...")

        # Sleep in small slices to respond promptly to SIGINT
        while running and sleep_time > 0:
            slice_sleep = min(1, sleep_time)
            time.sleep(slice_sleep)
            sleep_time -= slice_sleep

    logger.info("[NSE100Runner] Scanner shut down successfully.")


if __name__ == "__main__":
    main()
