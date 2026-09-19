"""
algo_engine.parity_audit — Side-by-Side Signal Engine Parity Auditor
====================================================================

Compares TradingView production alerts (`signals`) against Black Box
shadow signals (`shadow_signals`), calculating timing deltas, level
fidelity, Day Type alignment, outcome parity, and return deviations.
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import logging

from .feeds import normalize_symbol

logger = logging.getLogger(__name__)


def parse_timestamp(ts_val: Any) -> Optional[float]:
    """Parse string or numeric timestamp to epoch seconds."""
    if not ts_val:
        return None
    if isinstance(ts_val, (int, float)):
        # If milliseconds (> 1e11), convert to seconds
        return ts_val / 1000.0 if ts_val > 1e11 else float(ts_val)

    if isinstance(ts_val, str):
        # Clean ISO format
        s = ts_val.replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(s)
            return dt.timestamp()
        except Exception:
            pass
        # Try dateutil or common format
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f%z"):
            try:
                dt = datetime.strptime(s, fmt)
                return dt.timestamp()
            except Exception:
                continue
    return None


@dataclass
class ParityMatch:
    """Detailed comparison between a single TV alert and Black Box signal."""
    symbol: str
    strategy: str

    # Timing
    tv_ts: Optional[float]
    bb_ts: Optional[float]
    timing_delta_seconds: float

    # Price Levels
    tv_entry: float
    bb_entry: float
    entry_delta_pct: float

    tv_stop: float
    bb_stop: float
    stop_delta_pct: float

    tv_target: float
    bb_target: float
    target_delta_pct: float

    # Day Types & Context
    tv_day_type: str
    bb_day_type: str
    day_type_match: bool

    tv_opening_bias: str
    bb_opening_bias: str
    bias_match: bool

    # Outcomes & Returns
    tv_outcome: str
    bb_outcome: str
    outcome_match: bool

    tv_exact_pct: Optional[float]
    bb_exact_pct: Optional[float]
    return_delta_pct: Optional[float]

    # Quality Rating
    fidelity_status: str  # 'PERFECT_MATCH', 'HIGH_FIDELITY', 'DIVERGENT'

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "strategy": self.strategy,
            "timing_delta_seconds": round(self.timing_delta_seconds, 2),
            "tv_entry": self.tv_entry,
            "bb_entry": self.bb_entry,
            "entry_delta_pct": round(self.entry_delta_pct, 4),
            "tv_stop": self.tv_stop,
            "bb_stop": self.bb_stop,
            "tv_target": self.tv_target,
            "bb_target": self.bb_target,
            "day_type_match": self.day_type_match,
            "tv_day_type": self.tv_day_type,
            "bb_day_type": self.bb_day_type,
            "outcome_match": self.outcome_match,
            "tv_outcome": self.tv_outcome,
            "bb_outcome": self.bb_outcome,
            "tv_exact_pct": self.tv_exact_pct,
            "bb_exact_pct": self.bb_exact_pct,
            "return_delta_pct": round(self.return_delta_pct, 4) if self.return_delta_pct is not None else None,
            "fidelity_status": self.fidelity_status,
        }


@dataclass
class ParityReport:
    """Comprehensive parity audit evaluation report."""
    total_tv: int = 0
    total_bb: int = 0
    matched_count: int = 0
    unmatched_tv_count: int = 0
    unmatched_bb_count: int = 0

    timing_correlation_pct: float = 0.0  # Timing within 5s
    level_fidelity_pct: float = 0.0      # Entry & SL within 0.1%
    day_type_accuracy_pct: float = 0.0   # Day type blueprint match
    outcome_parity_pct: float = 0.0      # WIN/LOSS/BE alignment
    overall_parity_score: float = 0.0    # Composite fidelity index

    matches: List[ParityMatch] = field(default_factory=list)
    unmatched_tv: List[Dict[str, Any]] = field(default_factory=list)
    unmatched_bb: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": {
                "total_tv_signals": self.total_tv,
                "total_bb_signals": self.total_bb,
                "matched_count": self.matched_count,
                "unmatched_tv_count": self.unmatched_tv_count,
                "unmatched_bb_count": self.unmatched_bb_count,
                "timing_correlation_pct": round(self.timing_correlation_pct, 2),
                "level_fidelity_pct": round(self.level_fidelity_pct, 2),
                "day_type_accuracy_pct": round(self.day_type_accuracy_pct, 2),
                "outcome_parity_pct": round(self.outcome_parity_pct, 2),
                "overall_parity_score": round(self.overall_parity_score, 2),
            },
            "matches": [m.to_dict() for m in self.matches],
            "unmatched_tv": self.unmatched_tv,
            "unmatched_bb": self.unmatched_bb,
        }


class ParityAuditor:
    """
    Audits side-by-side signals generated by TradingView vs the Black Box engine.
    """

    def __init__(self,
                 time_window_seconds: float = 300.0,
                 level_tolerance_pct: float = 0.001):  # 0.1% tolerance
        self.time_window_seconds = time_window_seconds
        self.level_tolerance_pct = level_tolerance_pct

    def audit(self,
              tv_signals: List[Dict[str, Any]],
              bb_signals: List[Dict[str, Any]]) -> ParityReport:
        """
        Compare TV signals against Black Box signals.
        
        Args:
            tv_signals: List of row dictionaries from `signals` table
            bb_signals: List of row dictionaries from `shadow_signals` table
            
        Returns:
            ParityReport with detailed metrics and discrepancy logs
        """
        report = ParityReport(
            total_tv=len(tv_signals),
            total_bb=len(bb_signals),
        )

        used_bb_indices = set()
        matches: List[ParityMatch] = []

        for tv_sig in tv_signals:
            tv_sym = normalize_symbol(tv_sig.get("symbol", ""))
            tv_type = (tv_sig.get("type") or "").strip().upper()
            tv_ts = parse_timestamp(tv_sig.get("signal_ts") or tv_sig.get("created_at"))

            # Find matching BB signal with same symbol & strategy within time window
            best_idx = None
            min_time_diff = float("inf")

            for idx, bb_sig in enumerate(bb_signals):
                if idx in used_bb_indices:
                    continue

                bb_sym = normalize_symbol(bb_sig.get("symbol", ""))
                bb_type = (bb_sig.get("type") or "").strip().upper()

                if tv_sym != bb_sym or tv_type != bb_type:
                    continue

                bb_ts = parse_timestamp(bb_sig.get("signal_ts") or bb_sig.get("created_at"))
                if tv_ts and bb_ts:
                    diff = abs(tv_ts - bb_ts)
                    if diff <= self.time_window_seconds and diff < min_time_diff:
                        min_time_diff = diff
                        best_idx = idx
                elif not tv_ts and not bb_ts:
                    # Fallback match on symbol and type
                    best_idx = idx
                    min_time_diff = 0.0
                    break

            if best_idx is not None:
                used_bb_indices.add(best_idx)
                bb_sig = bb_signals[best_idx]
                match = self._build_match(tv_sig, bb_sig, min_time_diff)
                matches.append(match)
            else:
                report.unmatched_tv.append(tv_sig)

        # Collect unmatched BB signals
        for idx, bb_sig in enumerate(bb_signals):
            if idx not in used_bb_indices:
                report.unmatched_bb.append(bb_sig)

        report.matches = matches
        report.matched_count = len(matches)
        report.unmatched_tv_count = len(report.unmatched_tv)
        report.unmatched_bb_count = len(report.unmatched_bb)

        # Compute aggregate performance scores
        if matches:
            timing_hits = sum(1 for m in matches if m.timing_delta_seconds <= 5.0)
            level_hits = sum(1 for m in matches if m.entry_delta_pct <= 0.001 and m.stop_delta_pct <= 0.001)
            dt_hits = sum(1 for m in matches if m.day_type_match)
            outcome_hits = sum(1 for m in matches if m.outcome_match)

            report.timing_correlation_pct = (timing_hits / len(matches)) * 100.0
            report.level_fidelity_pct = (level_hits / len(matches)) * 100.0
            report.day_type_accuracy_pct = (dt_hits / len(matches)) * 100.0
            report.outcome_parity_pct = (outcome_hits / len(matches)) * 100.0

            # Overall parity score: weighted composite
            report.overall_parity_score = (
                report.level_fidelity_pct * 0.40 +
                report.outcome_parity_pct * 0.30 +
                report.day_type_accuracy_pct * 0.15 +
                report.timing_correlation_pct * 0.15
            )
        else:
            report.overall_parity_score = 0.0

        return report

    def _build_match(self, tv: Dict[str, Any], bb: Dict[str, Any], time_diff: float) -> ParityMatch:
        """Construct detailed ParityMatch object comparing fields."""
        sym = normalize_symbol(tv.get("symbol", ""))
        strat = tv.get("type", "")

        tv_entry = float(tv.get("entry") or 0.0)
        bb_entry = float(bb.get("entry") or 0.0)
        entry_delta = abs(tv_entry - bb_entry) / max(tv_entry, 1e-6)

        tv_stop = float(tv.get("stop") or 0.0)
        bb_stop = float(bb.get("stop") or 0.0)
        stop_delta = abs(tv_stop - bb_stop) / max(tv_stop, 1e-6)

        tv_target = float(tv.get("target") or 0.0)
        bb_target = float(bb.get("target") or 0.0)
        target_delta = abs(tv_target - bb_target) / max(tv_target, 1e-6)

        # Day Type
        tv_meta = tv.get("metadata") or {}
        if isinstance(tv_meta, str):
            import json
            try: tv_meta = json.loads(tv_meta)
            except: tv_meta = {}

        bb_meta = bb.get("metadata") or {}
        if isinstance(bb_meta, str):
            import json
            try: bb_meta = json.loads(bb_meta)
            except: bb_meta = {}

        tv_dt = (tv_meta.get("day_type") or tv.get("message") or "").strip().upper()
        bb_dt = (bb_meta.get("day_type") or "").strip().upper()
        dt_match = (tv_dt == bb_dt) or (not tv_dt and not bb_dt)

        tv_bias = (tv_meta.get("opening_bias") or "").strip().upper()
        bb_bias = (bb_meta.get("opening_bias") or "").strip().upper()
        bias_match = (tv_bias == bb_bias) or (not tv_bias and not bb_bias)

        # Outcomes
        tv_out = (tv.get("outcome") or "").strip().upper()
        bb_out = (bb.get("outcome") or "").strip().upper()
        out_match = (tv_out == bb_out)

        # Exact Returns
        tv_pct = tv_meta.get("exact_pct")
        if tv_pct is not None:
            try: tv_pct = float(tv_pct)
            except: tv_pct = None

        bb_pct = bb_meta.get("exact_pct")
        if bb_pct is not None:
            try: bb_pct = float(bb_pct)
            except: bb_pct = None

        ret_delta = abs(tv_pct - bb_pct) if (tv_pct is not None and bb_pct is not None) else None

        # Fidelity status
        if entry_delta <= 0.0005 and stop_delta <= 0.0005 and out_match:
            status = "PERFECT_MATCH"
        elif entry_delta <= 0.002 and out_match:
            status = "HIGH_FIDELITY"
        else:
            status = "DIVERGENT"

        return ParityMatch(
            symbol=sym,
            strategy=strat,
            tv_ts=parse_timestamp(tv.get("signal_ts") or tv.get("created_at")),
            bb_ts=parse_timestamp(bb.get("signal_ts") or bb.get("created_at")),
            timing_delta_seconds=time_diff,
            tv_entry=tv_entry,
            bb_entry=bb_entry,
            entry_delta_pct=entry_delta,
            tv_stop=tv_stop,
            bb_stop=bb_stop,
            stop_delta_pct=stop_delta,
            tv_target=tv_target,
            bb_target=bb_target,
            target_delta_pct=target_delta,
            tv_day_type=tv_dt,
            bb_day_type=bb_dt,
            day_type_match=dt_match,
            tv_opening_bias=tv_bias,
            bb_opening_bias=bb_bias,
            bias_match=bias_match,
            tv_outcome=tv_out,
            bb_outcome=bb_out,
            outcome_match=out_match,
            tv_exact_pct=tv_pct,
            bb_exact_pct=bb_pct,
            return_delta_pct=ret_delta,
            fidelity_status=status,
        )
