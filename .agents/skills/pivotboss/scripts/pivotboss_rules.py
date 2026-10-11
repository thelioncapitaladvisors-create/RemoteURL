#!/usr/bin/env python3
"""
pivotboss_rules.py - Standalone CLI & Verification Tool for PivotBoss Swing Trade Pro 2.0 (STP2)

Usage:
    python3 pivotboss_rules.py --help
    python3 pivotboss_rules.py size --equity 1000000 --risk-pct 1.0 --entry 2500 --stop 2450
    python3 pivotboss_rules.py srd-target --prev-high 2520 --prev-low 2480 --high 2535 --low 2470 --type bull
    python3 pivotboss_rules.py scale --shares 100 --method 111 --entry 100 --target1 105 --target2 110 --target3 115
"""

import argparse
import sys
from typing import Dict, Any


def calculate_position_size(core_equity: float, risk_pct: float, entry: float, stop: float) -> Dict[str, Any]:
    """
    STP2 Step 1: Fixed Risk % Position Sizing.
    Risk Capital = Core Equity * (Risk % / 100)
    Risk Per Share = abs(Entry - Stop)
    Shares = Risk Capital / Risk Per Share
    """
    if risk_pct <= 0 or risk_pct > 10:
        raise ValueError("Risk percentage must be between 0.1% and 10% (STP2 recommends 0.5% - 2.0%).")
    risk_per_share = abs(entry - stop)
    if risk_per_share <= 0:
        raise ValueError("Stop price must differ from Entry price.")
    
    risk_capital = core_equity * (risk_pct / 100.0)
    shares = int(risk_capital / risk_per_share)
    total_capital = shares * entry
    leverage_pct = (total_capital / core_equity) * 100.0 if core_equity > 0 else 0.0

    return {
        "core_equity": core_equity,
        "risk_pct": risk_pct,
        "risk_capital": round(risk_capital, 2),
        "entry": entry,
        "stop": stop,
        "risk_per_share": round(risk_per_share, 2),
        "shares": shares,
        "total_capital_deployed": round(total_capital, 2),
        "capital_utilization_pct": round(leverage_pct, 2)
    }


def calculate_srd_target(prev_high: float, prev_low: float, high: float, low: float, direction: str) -> Dict[str, Any]:
    """
    STP2 Stop Run Day Measured Target (STP2 p. 30):
    Bullish SRD: Target = PrevHigh + (PrevHigh - Low)
    Bearish SRD: Target = PrevLow - (High - PrevLow)
    """
    d = direction.lower()
    if d in ("bull", "long", "bullish"):
        target = prev_high + (prev_high - low)
        expansion = prev_high - low
    elif d in ("bear", "short", "bearish"):
        target = prev_low - (high - prev_low)
        expansion = high - prev_low
    else:
        raise ValueError("Direction must be 'bull' or 'bear'.")

    return {
        "direction": d,
        "prev_high": prev_high,
        "prev_low": prev_low,
        "session_high": high,
        "session_low": low,
        "expansion_distance": round(expansion, 2),
        "srd_target": round(target, 2)
    }


def calculate_scale_outs(shares: int, method: str) -> Dict[str, Any]:
    """
    STP2 Step 4: Scale-Out Tranche Calculator.
    Methods:
      - 11: 50% at Target 1, 50% at Target 2
      - 111: 33.3% at T1, 33.3% at T2, 33.4% at T3
      - 211: 50% at T1, 25% at T2, 25% at T3
    """
    if shares <= 0:
        raise ValueError("Shares must be positive.")
    
    if method == "11":
        t1 = shares // 2
        t2 = shares - t1
        return {"method": "11", "total_shares": shares, "tranches": [("T1 (50%)", t1), ("T2 (50%)", t2)]}
    elif method == "111":
        t1 = shares // 3
        t2 = shares // 3
        t3 = shares - (t1 + t2)
        return {"method": "111", "total_shares": shares, "tranches": [("T1 (33%)", t1), ("T2 (33%)", t2), ("T3 (34%)", t3)]}
    elif method == "211":
        t1 = shares // 2
        t2 = (shares - t1) // 2
        t3 = shares - (t1 + t2)
        return {"method": "211", "total_shares": shares, "tranches": [("T1 (50%)", t1), ("T2 (25%)", t2), ("T3 (25%)", t3)]}
    else:
        raise ValueError("Method must be '11', '111', or '211'.")


def main():
    parser = argparse.ArgumentParser(description="PivotBoss STP2 Rules Calculator & Auditor")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Position sizing
    size_parser = subparsers.add_parser("size", help="Calculate position size based on STP2 Fixed Risk %")
    size_parser.add_argument("--equity", type=float, required=True, help="Core equity in account currency")
    size_parser.add_argument("--risk-pct", type=float, default=1.0, help="Risk percentage (default: 1.0%)")
    size_parser.add_argument("--entry", type=float, required=True, help="Planned entry price")
    size_parser.add_argument("--stop", type=float, required=True, help="Initial stop price")

    # SRD Target
    srd_parser = subparsers.add_parser("srd-target", help="Calculate Stop Run Day measured move target")
    srd_parser.add_argument("--prev-high", type=float, required=True, help="Prior session high")
    srd_parser.add_argument("--prev-low", type=float, required=True, help="Prior session low")
    srd_parser.add_argument("--high", type=float, required=True, help="SRD session high")
    srd_parser.add_argument("--low", type=float, required=True, help="SRD session low")
    srd_parser.add_argument("--type", choices=["bull", "bear"], default="bull", help="SRD direction")

    # Scaling
    scale_parser = subparsers.add_parser("scale", help="Calculate scale-out tranches")
    scale_parser.add_argument("--shares", type=int, required=True, help="Total position shares")
    scale_parser.add_argument("--method", choices=["11", "111", "211"], default="111", help="Scale method")

    args = parser.parse_args()

    if args.command == "size":
        res = calculate_position_size(args.equity, args.risk_pct, args.entry, args.stop)
        print("=== STP2 Step 1: Position Sizing ===")
        for k, v in res.items():
            print(f"  {k:25}: {v}")
    elif args.command == "srd-target":
        res = calculate_srd_target(args.prev_high, args.prev_low, args.high, args.low, args.type)
        print("=== STP2 Stop Run Day Measured Target ===")
        for k, v in res.items():
            print(f"  {k:25}: {v}")
    elif args.command == "scale":
        res = calculate_scale_outs(args.shares, args.method)
        print(f"=== STP2 Step 4: Scale-Out Distribution ({res['method']}) ===")
        print(f"  Total Shares: {res['total_shares']}")
        for label, qty in res["tranches"]:
            print(f"  {label:15}: {qty} shares")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
