# The Lion Capital Solutions (TLCS) System Architecture & Update Log
## Version 1.0 Release: Analytics Tab Tearsheet Statistics Dynamic Responsive Height & Dead Empty Space Elimination
**Date**: October 4, 2026  
**Status**: Production Hardened Baseline (Release Tags `v1.0` / `v1.0.0`)  
**Architect**: Vishant Vyankat Meshram (*CFTe, CMT L3 Dec 2024*)

---

### Executive Overview
This release resolves the visual layout defect on the **ANALYTICS** tab where a vast expanse of dead empty white space (~480px) appeared beneath the VectorBT institutional statistics metrics table (ending at `Value at Risk`). By implementing dynamic responsive container height sizing coupled with cross-frame `postMessage` height telemetry, the statistics card now tightly hugs its 17 metrics rows across all device screen resolutions and themes with zero empty space and zero table clipping.

---

### Root Cause Analysis & Architecture Fixes

#### 1. Root Cause: Legacy Hardcoded Container Min-Height (`page.tsx`)
- **Vulnerability**: In `Tv-Alert-Mobile/src/app/page.tsx` (line 10744), the statistics iframe was styled with `min-h-[1100px] w-full border-0`. This 1100px minimum height was inherited from a legacy build when the statistics table rendered 35 individual rows.
- **Physical Geometry**: Under the streamlined 17-row institutional tearsheet layout (Header row + 16 core metrics: `Start`, `End`, `Period`, `Start Value`, `End Value`, `Total Return [%]`, `Benchmark Return [%]`, `Max Gross Exposure [%]`, `Total Fees Paid`, `Max Drawdown [%]`, `Max Drawdown Duration`, `Total Trades`, `Win Rate [%]`, `Best Trade [%]`, `Worst Trade [%]`, `Avg Winning Trade [%]`, `Value at Risk`), each row occupies ~35px in height, giving a total table height of ~595px to ~625px. The 1100px container forced ~480px of blank white space inside the card.

#### 2. Bidirectional Responsive Height Telemetry (`strategy_tearsheet.html`)
- In `public/strategy_tearsheet.html`, `body.mode-stats` was optimized to remove fixed heights:
  ```css
  body.mode-stats #stats {
    height: auto !important;
    min-height: auto !important;
    padding: 8px 10px !important;
  }
  body.mode-stats {
    overflow-y: hidden !important;
  }
  ```
- Implemented real-time height broadcasting via `postMessage`:
  ```javascript
  function sendStatsHeight() {
    if (document.body.classList.contains('mode-stats')) {
      const table = document.getElementById('statsTable');
      if (table) {
        const height = table.offsetHeight + 24;
        window.parent.postMessage({ type: 'TLCS_TEARSHEET_HEIGHT', height: height }, '*');
      }
    }
  }
  window.addEventListener('load', sendStatsHeight);
  window.addEventListener('resize', sendStatsHeight);
  ```

#### 3. Dynamic Height State & Auto-Resize in Mobile Terminal (`page.tsx`)
- Added `statsHeight` state initialized to `625px` (the exact rendered height of the 17-row table, eliminating layout shift even before iframe load):
  ```tsx
  const [statsHeight, setStatsHeight] = useState<number>(625);
  ```
- Registered window message listener for `TLCS_TEARSHEET_HEIGHT`:
  ```tsx
  useEffect(() => {
    const handleStatsHeight = (event: MessageEvent) => {
      if (event.data && event.data.type === 'TLCS_TEARSHEET_HEIGHT' && typeof event.data.height === 'number') {
        setStatsHeight(Math.max(500, Math.min(1200, event.data.height)));
      }
    };
    window.addEventListener('message', handleStatsHeight);
    return () => window.removeEventListener('message', handleStatsHeight);
  }, []);
  ```
- Updated iframe element to use dynamic styles:
  ```tsx
  style={{ minHeight: `${statsHeight}px`, height: `${statsHeight}px` }}
  className="w-full border-0 rounded-b-2xl transition-all duration-300"
  ```

#### 4. Multi-Repository & Generator Synchronization
- Synchronized the dynamic height architecture across:
  - `Tv-Alert-Mobile/public/strategy_tearsheet.html`
  - `TLCS_Website_Deploy/strategy_tearsheet.html`
  - `TLCS_Website_Deploy/generate_tearsheet.py`
  - `algo_engine/strategy_tearsheet.html`
  - `algo_engine/backtest_edge.py`
  - `RemoteURL/algo_engine/strategy_tearsheet.html`
  - `RemoteURL/algo_engine/backtest_edge.py`

---

### Verification & Test Suite
1. **Zero Dead White Space**: Verified that the container height adapts strictly to ~625px, completely eliminating the ~480px dead space below `Value at Risk`.
2. **Zero Table Row Clipping**: Verified all 17 rows are visible with crisp typography, correct margins, and zero vertical scrollbar inside the card.
3. **Cross-Theme Parity**: Verified seamless appearance across all 7 visual skins (`DARK`, `SLATE`, `LIGHT`, `THE LION`, `GG DARK`, `GG LIGHT`, `AUTO`).
4. **Triple Mirror Backup**: Full code and assets backed up to `Project Backup/`, `Backups/`, and `Documents/Backups/`.
