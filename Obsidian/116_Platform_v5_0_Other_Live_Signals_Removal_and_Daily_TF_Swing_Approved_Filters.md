# Obsidian Document 116: Platform v5.0 Ab-Initio Unverified Signal Suppression & 6 Core Swing Strategies Mandate

**Status**: Implemented & Verified in Production  
**Date**: November 22, 2026  
**Platform Version**: v5.0 (`tv-alert-mobile@5.0.0`)  
**Scope**: Next.js Mobile Application (`Tv-Alert-Mobile/src/app/page.tsx`, `page.tsx`, `RemoteURL/page.tsx`), BlackBox Engine (`algo_engine/feeds/feed_manager.py`, `algo_engine/shadow_pipeline.py`, `algo_engine/run_daily_scanner.py`, `algo_engine/nse100_scanner.py`, `algo_engine/engine_daemon.py`, `algo_engine/sync_weekly_performance.py`), Knowledge Base (`Obsidian/`, `AGENTS.md`, `.agents/AGENTS.md`), and Backup Archives.

---

## 1. Executive Summary & User Requirements

Per direct user instruction:
> *"Any asset flagged as other is suppressed from weekly institutional performance tables to prevent unverified or orphan data from polluting the metrics. Stop generation of such signals ab-initio in BlackBox itself."*
> *"Remove these 2 categories [REJ & CONT] from Swing trading opportunities."*

### Key Implementation Deliverables:
1. **Ab-Initio Suppression of Unverified/Other Assets in BlackBox**:
   - Every asset is validated against the 7 canonical institutional markets (`NIFTY`, `STOCKS`, `MCX`, `NYMEX`, `CRYPTO`, `FOREX`, `WORLD`).
   - If an asset resolves to `OTHER` or `UNKNOWN`, BlackBox suppresses evaluation and signal generation **ab-initio** across:
     - `algo_engine/feeds/feed_manager.py` (`get_market_category`, `is_approved_asset`)
     - `algo_engine/shadow_pipeline.py` (`record_signal`, `sync_signal`)
     - `algo_engine/run_daily_scanner.py` (`scan_symbol`)
     - `algo_engine/nse100_scanner.py` (`scan_symbol`)
     - `algo_engine/engine_daemon.py` (`_on_bar_close`)
2. **6 Core Execution Strategies for Swing Trading Opportunities**:
   - Rejections (`REJ`) and Continuations (`CONT`) were removed from Swing Live Signals, keeping strictly the 6 core execution strategies:
     1. Confluence (`FIRE`)
     2. Lightning (`LIGHTNING`)
     3. Extreme Reversal (`EXT_REV`)
     4. Missile (`MISSILE`)
     5. Scalp (`SCALP`)
     6. Divergence (`DIV`)
3. **Ab-Initio Halting of VCPR Generation in Daily Scanner**:
   - In `algo_engine/run_daily_scanner.py`, VCPR touches and magnets are completely suppressed from signal generation, eliminating unwanted VCPR signals at the source.
4. **Permanent Removal of "Other Live Signals"**:
   - The fallback table row (`key="other-signals"`) and its underlying `unmatchedAssets` computation inside `renderDhanLiveSignalsSection()` have been completely excised.

---

## 2. Technical Architecture & Implementation

### 2.1 Canonical Market Resolution & Ab-Initio Validation (`feed_manager.py`)
```python
def get_market_category(symbol: str) -> str:
    sym = normalize_symbol(symbol)
    if sym in NIFTY_INDEX_SYMBOLS:
        return "NIFTY"
    if sym in NIFTY_100_SYMBOLS or sym in NIFTY_SYMBOLS:
        return "STOCKS"
    if sym in MCX_SYMBOLS or sym.startswith("ALUMINI") or sym.startswith("ZINC"):
        return "MCX"
    if sym in NYMEX_SYMBOLS:
        return "NYMEX"
    if sym in CANONICAL_CRYPTO_SYMBOLS or sym.endswith("USDT") or sym.endswith("BTC"):
        return "CRYPTO"
    if sym in FOREX_SYMBOLS:
        return "FOREX"
    if sym in WORLD_INDICES:
        return "WORLD"
    return "OTHER"

def is_approved_asset(symbol: str) -> bool:
    return get_market_category(symbol) in ("NIFTY", "STOCKS", "MCX", "NYMEX", "CRYPTO", "FOREX", "WORLD")
```

### 2.2 Ab-Initio Gating in Shadow Pipeline (`shadow_pipeline.py`)
```python
mkt = get_market_category(clean_sym)
if mkt in ("OTHER", "UNKNOWN", "other") or not is_approved_asset(clean_sym):
    logger.warning(f"[ShadowPipeline] Suppressed unverified/other asset ab-initio: {clean_sym} (market={mkt})")
    return None
```

### 2.3 6 Core Strategies in Swing Live Signals (`page.tsx`)
```tsx
const matchesApproved = 
  Boolean(a.relationshipBadge?.includes('CONFLUENCE') || a.relationshipType === 'FIRE') ||
  Boolean(a.relationshipBadge?.includes('LIGHTNING') || a.relationshipType === 'LIGHTNING') ||
  Boolean(a.relationshipBadge?.includes('EXT REV') || a.relationshipBadge?.includes('EXTREME') || a.relationshipType === 'EXT_REV') ||
  Boolean(a.relationshipBadge?.includes('MISSILE') || a.relationshipType === 'MISSILE') ||
  Boolean(a.relationshipBadge?.includes('SCALP') || a.relationshipType === 'SCALP') ||
  Boolean(a.relationshipBadge?.includes('DIV') || a.relationshipType === 'DIV');
```

---

## 3. Verification & Validation

1. **TypeScript Verification**:
   - `tsc --noEmit` passed with 0 errors in `Tv-Alert-Mobile/`.
2. **Python Syntax & Compilation**:
   - `python3 -m py_compile` passed with 0 errors on all engine modules.
3. **Three-Way File Parity**:
   - Confirmed 0 diffs between `page.tsx`, `Tv-Alert-Mobile/src/app/page.tsx`, and `RemoteURL/page.tsx`.
4. **Git Repository Status**:
   - Committed and pushed to `main` across `Tv-Alert-Mobile`, `RemoteURL`, and root.
