"""
Unit Tests for Phase 4: Side-by-Side Parity Audit Engine
========================================================

Tests:
    1. Perfect match between TV alert and Black Box shadow signal
    2. Timing delta and level deviation tolerances
    3. Outcome and return differential calculations
    4. Unmatched TV signals and unmatched Black Box signals
    5. Overall composite parity score calculation
"""

import sys
import os
import unittest

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from algo_engine.parity_audit import ParityAuditor, ParityMatch, ParityReport


class TestParityAuditor(unittest.TestCase):

    def setUp(self):
        self.auditor = ParityAuditor(time_window_seconds=300.0, level_tolerance_pct=0.001)

    def test_perfect_match(self):
        """Identical TV and Black Box signals result in 100% parity score."""
        tv_signals = [{
            "symbol": "NSE:RELIANCE",
            "type": "LONG LIGHTNING",
            "entry": 2850.0,
            "stop": 2835.0,
            "target": 2880.0,
            "status": "Hit Target",
            "outcome": "WIN",
            "created_at": "2026-09-19T10:00:00Z",
            "signal_ts": "2026-09-19T10:00:00Z",
            "metadata": {
                "day_type": "TREND DAY",
                "opening_bias": "IN RANGE IN VALUE",
                "exact_pct": 1.05,
            }
        }]

        bb_signals = [{
            "symbol": "RELIANCE",
            "type": "LONG LIGHTNING",
            "entry": 2850.0,
            "stop": 2835.0,
            "target": 2880.0,
            "status": "Hit TP1",
            "outcome": "WIN",
            "created_at": "2026-09-19T10:00:01Z",  # 1s delta
            "signal_ts": "2026-09-19T10:00:01Z",
            "metadata": {
                "day_type": "TREND DAY",
                "opening_bias": "IN RANGE IN VALUE",
                "exact_pct": 1.05,
            }
        }]

        report = self.auditor.audit(tv_signals, bb_signals)

        self.assertEqual(report.matched_count, 1)
        self.assertEqual(report.unmatched_tv_count, 0)
        self.assertEqual(report.unmatched_bb_count, 0)

        match = report.matches[0]
        self.assertEqual(match.fidelity_status, "PERFECT_MATCH")
        self.assertAlmostEqual(match.timing_delta_seconds, 1.0, places=1)
        self.assertEqual(match.entry_delta_pct, 0.0)
        self.assertTrue(match.outcome_match)
        self.assertTrue(match.day_type_match)
        self.assertAlmostEqual(match.return_delta_pct, 0.0, places=4)
        self.assertEqual(report.overall_parity_score, 100.0)

    def test_divergent_levels_and_outcome(self):
        """Divergence in prices or outcome degrades the parity score."""
        tv_signals = [{
            "symbol": "BTCUSDT",
            "type": "LONG MISSILE",
            "entry": 65000.0,
            "stop": 64000.0,
            "target": 67000.0,
            "outcome": "WIN",
            "created_at": "2026-09-19T12:00:00Z",
            "metadata": {"exact_pct": 3.08}
        }]

        bb_signals = [{
            "symbol": "BTCUSDT",
            "type": "LONG MISSILE",
            "entry": 65150.0,  # 0.23% higher entry
            "stop": 63900.0,
            "target": 67000.0,
            "outcome": "LOSS", # Divergent outcome
            "created_at": "2026-09-19T12:00:02Z",
            "metadata": {"exact_pct": -1.5}
        }]

        report = self.auditor.audit(tv_signals, bb_signals)
        self.assertEqual(report.matched_count, 1)
        match = report.matches[0]

        self.assertEqual(match.fidelity_status, "DIVERGENT")
        self.assertFalse(match.outcome_match)
        self.assertLess(report.overall_parity_score, 60.0)

    def test_unmatched_signals_detection(self):
        """Detects signals present in one engine but missed by the other."""
        tv_signals = [
            {"symbol": "CL", "type": "SHORT SCALP", "created_at": "2026-09-19T14:00:00Z"},
            {"symbol": "GC", "type": "LONG LIGHTNING", "created_at": "2026-09-19T14:15:00Z"},
        ]

        bb_signals = [
            {"symbol": "CL", "type": "SHORT SCALP", "created_at": "2026-09-19T14:00:03Z"},
            {"symbol": "EURUSD", "type": "LONG MISSILE", "created_at": "2026-09-19T14:30:00Z"},
        ]

        report = self.auditor.audit(tv_signals, bb_signals)

        self.assertEqual(report.matched_count, 1)  # CL matched
        self.assertEqual(report.unmatched_tv_count, 1)  # GC only in TV
        self.assertEqual(report.unmatched_bb_count, 1)  # EURUSD only in BB

        self.assertEqual(report.unmatched_tv[0]["symbol"], "GC")
        self.assertEqual(report.unmatched_bb[0]["symbol"], "EURUSD")


if __name__ == '__main__':
    unittest.main(verbosity=2)
