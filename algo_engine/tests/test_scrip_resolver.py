"""
Unit tests for algo_engine.scrip_resolver
=========================================
Validates CSV parsing, nearest front-month sorting, filtering expired contracts,
and dictionary formatting for feeds and executors.
"""

import unittest
from algo_engine.scrip_resolver import (
    parse_scrip_master_csv,
    get_mcx_symbol_map,
    get_mcx_executor_map,
    TARGET_MCX_COMMODITIES
)

SAMPLE_CSV = """SEM_EXM_EXCH_ID,SEM_SEGMENT,SEM_SMST_SECURITY_ID,SEM_INSTRUMENT_NAME,SEM_EXPIRY_CODE,SEM_TRADING_SYMBOL,SEM_LOT_UNITS,SEM_CUSTOM_SYMBOL,SEM_EXPIRY_DATE,SEM_STRIKE_PRICE,SEM_OPTION_TYPE,SEM_TICK_SIZE,SEM_EXPIRY_FLAG,SEM_EXCH_INSTRUMENT_TYPE,SEM_SERIES,SM_SYMBOL_NAME
MCX,M,569900,FUTCOM,0,CRUDEOIL-19Oct2026-FUT,100,CRUDEOIL OCT FUT,2026-10-19 23:30:00,-0.01000,XX,1.0000,M,FUTCOM,FUT,CRUDEOIL
MCX,M,573422,FUTCOM,0,CRUDEOIL-19Nov2026-FUT,100,CRUDEOIL NOV FUT,2099-11-19 23:30:00,-0.01000,XX,1.0000,M,FUTCOM,FUT,CRUDEOIL
MCX,M,576264,FUTCOM,0,CRUDEOIL-18Dec2026-FUT,100,CRUDEOIL DEC FUT,2099-12-18 23:30:00,-0.01000,XX,1.0000,M,FUTCOM,FUT,CRUDEOIL
MCX,M,495213,FUTCOM,0,GOLD-04Dec2026-FUT,1,GOLD DEC FUT,2099-12-04 23:30:00,-0.01000,XX,1.0000,M,FUTCOM,FUT,GOLD
MCX,M,495214,FUTCOM,0,SILVER-04Dec2026-FUT,30,SILVER DEC FUT,2099-12-04 23:30:00,-0.01000,XX,1.0000,M,FUTCOM,FUT,SILVER
MCX,M,574319,FUTCOM,0,NATURALGAS-24Nov2026-FUT,1250,NATURALGAS NOV FUT,2099-11-24 23:30:00,-0.01000,XX,0.1000,M,FUTCOM,FUT,NATURALGAS
NSE,E,2885,EQUITY,0,RELIANCE-EQ,1,RELIANCE,,-0.01000,XX,0.0500,M,EQUITY,EQ,RELIANCE
"""


class TestScripResolver(unittest.TestCase):

    def test_parse_front_month_selection(self):
        """Verify that the earliest unexpired contract is selected as front-month."""
        resolved = parse_scrip_master_csv(SAMPLE_CSV)
        
        # October contract is in 2026 (expired relative to 2099 fixtures), so 573422 (Nov) must be selected
        self.assertIn("CRUDEOIL", resolved)
        self.assertEqual(resolved["CRUDEOIL"]["security_id"], "573422")
        self.assertEqual(resolved["CRUDEOIL"]["trading_symbol"], "CRUDEOIL-19Nov2026-FUT")

    def test_all_target_commodities_present(self):
        """Verify that all target MCX commodities are present with fallbacks."""
        resolved = parse_scrip_master_csv(SAMPLE_CSV)
        for t in TARGET_MCX_COMMODITIES:
            self.assertIn(t, resolved)
            self.assertTrue(bool(resolved[t].get("security_id")))

    def test_symbol_map_formatting(self):
        """Verify that get_mcx_symbol_map returns (5, security_id) tuples."""
        sym_map = get_mcx_symbol_map()
        self.assertIsInstance(sym_map, dict)
        self.assertIn("CRUDEOIL", sym_map)
        segment, sec_id = sym_map["CRUDEOIL"]
        self.assertEqual(segment, 5)
        self.assertTrue(sec_id.isdigit())

    def test_executor_map_formatting(self):
        """Verify that get_mcx_executor_map returns security_id and lot_size."""
        exec_map = get_mcx_executor_map()
        self.assertIsInstance(exec_map, dict)
        self.assertIn("CRUDEOIL", exec_map)
        self.assertIn("security_id", exec_map["CRUDEOIL"])
        self.assertIn("lot_size", exec_map["CRUDEOIL"])
        self.assertGreater(exec_map["CRUDEOIL"]["lot_size"], 0)


if __name__ == '__main__':
    unittest.main()
