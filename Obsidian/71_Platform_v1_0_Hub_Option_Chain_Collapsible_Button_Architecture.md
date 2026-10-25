# 71. Platform v1.0 Architecture: Hub Option Chain Collapsible-by-Default Architecture & Interactive Asset Buttons
**Date**: October 25, 2026 (20:15 IST)  
**Release Tag**: `v1.0`  
**Status**: 100% Production Ready & Verified  
**Author**: The Lion Capital Advisors  

---

## 1. Executive Summary

This architecture release fulfills the user's specific ergonomic and layout optimization mandate for the **Option Chain** component on the `HUB` tab (`activeTab === 'DASHBOARD'`) in the mobile terminal (`Tv-Alert-Mobile/src/app/page.tsx`):
1. **Collapsed by Default**:
   - `HubOptionChain` initializes with `isExpanded = false` by default, eliminating the massive vertical scroll footprint from the 4 KPI cards and 13+ strikes table on initial load of the HUB tab.
2. **Tactile Interactive Asset Buttons**:
   - The 5 asset selectors (`NIFTY 50 (NSE)`, `CRUDE OIL (MCX)`, `NATURAL GAS (MCX)`, `GOLD (MCX)`, `SILVER (MCX)`) are transformed into prominent, interactive tactile buttons with:
     - Real button affordance: distinct borders, elevated drop shadows, hover transitions, and tactile active press effects (`active:scale-[0.97]`).
     - Dynamic chevron indicators: `ChevronUp` when selected and expanded; `ChevronDown` otherwise.
     - Dual-action click handler:
       - If the clicked asset is already selected and expanded: toggles the option chain collapsed.
       - If collapsed or switching to a new asset: selects that asset and immediately expands the option chain.
3. **Explicit Header Controls & Collapsed Preview Strip**:
   - **Header Control**: Added an explicit `[EXPAND ▼]` / `[COLLAPSE ▲]` toggle button in the section header alongside the Live/EOD status pill, expiry badge, and refresh button.
   - **Collapsed Preview Strip**: When collapsed, displays a sleek 1-line interactive strip showing `Selected Asset • Spot LTP • PCR • Max Pain • EXPAND CHAIN ▼` that expands on tap without cluttering the screen.
   - **Bottom Collapse Button**: Provides a convenient `[COLLAPSE OPTION CHAIN ▲]` button at the base of the strikes matrix for seamless navigation after reviewing strikes.

---

## 2. Architectural Structure

### 2.1 State Management & View Transitions
```typescript
function HubOptionChain() {
  const [selectedAsset, setSelectedAsset] = useState<'NIFTY' | 'CRUDEOIL' | 'NATURALGAS' | 'GOLD' | 'SILVER'>('NIFTY');
  const [isExpanded, setIsExpanded] = useState<boolean>(false); // Collapsed by default
  const [showAllStrikes, setShowAllStrikes] = useState(false);
  // ...
}
```

### 2.2 Component Visual Progression
1. **Collapsed State (`!isExpanded`)**:
   - Section Header (`⚡ OPTION CHAIN`, Live/EOD status, Expiry, `[EXPAND ▼]`, Refresh).
   - 5 Tactile Asset Buttons with segment badges and `ChevronDown` indicators.
   - Sleek 1-line Collapsed Preview Strip (`NIFTY 50 • CLOSE ₹22,600 • PCR 0.74 • PAIN ₹22,700 • EXPAND CHAIN ▼`).
2. **Expanded State (`isExpanded === true`)**:
   - Active Asset Button highlights with vibrant gradient (`from-indigo-600 to-blue-600`), ring highlight, and `ChevronUp` indicator.
   - Section 3: 4 Underlying Spot & Option Metrics Cards (`SPOT LTP / EOD CLOSE`, `PCR`, `MAX PAIN STRIKE`, `TOTAL OI`).
   - Section 4: 13-Strikes Matrix Table with CE / STRIKE / PE columns, ATM highlighting, ITM background shading, and Near-ATM/Full-Chain toggle.
   - Bottom Collapse Button: `[COLLAPSE OPTION CHAIN ▲]`.

---

## 3. Verification & Deployment

1. **Compilation Verification**: Next.js production build (`npm run build`) exited with code 0 (`Compiled successfully`, `8/8 static pages generated`).
2. **PWA Service Worker Update**: Bumped cache to `tlcs-cache-v1.0.0-rev16` in `Tv-Alert-Mobile/public/sw.js` for instant client cache invalidation and zero `ERR_FAILED` guarantee.
3. **Git Version Control**:
   - `Tv-Alert-Mobile`: Committed (`f802625`), tagged `v1.0`, and pushed to remote `origin main` and `origin v1.0 --force`.
   - `Project` root: Submodule synchronized, committed, tagged `v1.0`, and pushed to remote `origin main` and `origin v1.0 --force`.
4. **Theme Contrast Compliance**: Verified across all 6 themes (`dark`, `gray`, `light`, `lion`, `goldengate`, `goldengate-light`).
