# Obsidian Document 116: Platform v5.0 Other Live Signals Removal & Daily TF Swing Approved Execution Filters Mandate

**Status**: Implemented & Verified in Production  
**Date**: November 22, 2026  
**Platform Version**: v5.0 (`tv-alert-mobile@5.0.0`)  
**Scope**: Next.js Mobile Application (`Tv-Alert-Mobile/src/app/page.tsx`, `page.tsx`, `RemoteURL/page.tsx`), Knowledge Base (`Obsidian/`, `AGENTS.md`, `.agents/AGENTS.md`), and Backup Archives (`Backups/`, `Project Backup/`).

---

## 1. Executive Summary & User Requirements

Per direct user instruction:
> *"Other live signals is not a valid filter or category of signals. Remove this entirely. Keep only approved filters for filtering daily time frame signals here for Swing opportunities excluding VCPR signals."*

### Key Implementation Deliverables:
1. **Permanent Removal of "Other Live Signals"**:
   - The fallback table row (`key="other-signals"`) and its underlying `unmatchedAssets` computation inside `renderDhanLiveSignalsSection()` have been completely excised across all views.
2. **Strict VCPR Exclusion for Daily Swing Opportunities**:
   - When viewing the INSIGHTS tab (`activeTab === 'INSIGHTS'`), all Virgin CPR (`VCPR`) signals—including VCPR touch points, VCPR magnets, and Virgin CPR BlackBox scanner signals—are strictly excluded from `liveSignalsAssets`.
3. **Approved Core Execution Filters Enforced**:
   - Only 8 canonical execution strategies qualify for Daily Timeframe (1D Swing) opportunities:
     1. Confluence (`FIRE`)
     2. Lightning (`LIGHTNING`)
     3. Extreme Reversal (`EXT_REV`)
     4. Missile (`MISSILE`)
     5. Scalp (`SCALP`)
     6. Divergence (`DIV`)
     7. Rejection (`REJ`)
     8. Continuation (`CONT`)
4. **Three-Way Byte-for-Byte Synchronization**:
   - 100% byte-for-byte checksum parity maintained across `page.tsx`, `Tv-Alert-Mobile/src/app/page.tsx`, and `RemoteURL/page.tsx`.

---

## 2. Technical Architecture & Implementation

### 2.1 Timeframe Separation & VCPR Gating in `liveSignalsAssets`
In `extractDhanScreenerAssets()` within `page.tsx`:
```tsx
const filteredByTabTf = activeTab === 'INSIGHTS'
  ? assets.filter(a => {
      const is1D = a.timeframe === '1D' || a.timeframe === 'D' || a.timeframe === 'DAILY' || a.signals?.some((s: any) => {
        const m = typeof s.metadata === 'string' ? JSON.parse(s.metadata || '{}') : (s.metadata || {});
        return m.timeframe === '1D' || m.timeframe === 'D' || m.interval === '1D' || s.timeframe === '1D' || s.timeframe === 'D';
      });
      if (!is1D) return false;

      // Strictly exclude VCPR signals for Swing Trading Opportunities per user instruction
      const isVcpr = a.isVcprTouch || a.relationshipType === 'VCPR' || a.relationshipBadge?.includes('VCPR') || a.signals?.some((s: any) => (s.type || '').toUpperCase().includes('VIRGIN'));
      if (isVcpr) return false;

      // Exclusively retain approved execution strategies
      const matchesApproved = 
        Boolean(a.relationshipBadge?.includes('CONFLUENCE') || a.relationshipType === 'FIRE') ||
        Boolean(a.relationshipBadge?.includes('LIGHTNING') || a.relationshipType === 'LIGHTNING') ||
        Boolean(a.relationshipBadge?.includes('EXT REV') || a.relationshipBadge?.includes('EXTREME') || a.relationshipType === 'EXT_REV') ||
        Boolean(a.relationshipBadge?.includes('MISSILE') || a.relationshipType === 'MISSILE') ||
        Boolean(a.relationshipBadge?.includes('SCALP') || a.relationshipType === 'SCALP') ||
        Boolean(a.relationshipBadge?.includes('DIV') || a.relationshipType === 'DIV') ||
        Boolean(a.relationshipBadge?.includes('REJ') || a.relationshipType === 'REJ') ||
        Boolean(a.relationshipBadge?.includes('CONT') || a.relationshipType === 'CONT');
      return matchesApproved;
    })
  : assets;
```

### 2.2 Category Matching Function (`matchLiveAssetToCategory`)
Inside `renderDhanLiveSignalsSection()`:
```tsx
const matchLiveAssetToCategory = (catId: string, a: any) => {
  if (catId === 'FIRE') return a.relationshipBadge?.includes('CONFLUENCE') || a.relationshipType === 'FIRE';
  if (catId === 'LIGHTNING') return a.relationshipBadge?.includes('LIGHTNING') || a.relationshipType === 'LIGHTNING';
  if (catId === 'EXT_REV') return a.relationshipBadge?.includes('EXT REV') || a.relationshipBadge?.includes('EXTREME') || a.relationshipType === 'EXT_REV';
  if (catId === 'MISSILE') return a.relationshipBadge?.includes('MISSILE') || a.relationshipType === 'MISSILE';
  if (catId === 'SCALP') return a.relationshipBadge?.includes('SCALP') || a.relationshipType === 'SCALP';
  if (catId === 'DIV') return a.relationshipBadge?.includes('DIV') || a.relationshipType === 'DIV';
  if (catId === 'REJ') return a.relationshipBadge?.includes('REJ') || a.relationshipType === 'REJ';
  if (catId === 'CONT') return a.relationshipBadge?.includes('CONT') || a.relationshipType === 'CONT';
  return false;
};
```

### 2.3 Elimination of Unmatched Fallback
The `unmatchedAssets` precomputation and fallback row were excised completely. When all rows are filtered out or empty, a clean informational message is rendered:
```tsx
{renderedRows}
{renderedRows.length === 0 && (
  <tr>
    <td colSpan={2} className="py-6 text-center text-dim font-mono text-xs">
      No signals match current matrix filters
    </td>
  </tr>
)}
```

---

## 3. Verification & Validation

1. **TypeScript Verification**:
   - `tsc --noEmit` passed with 0 errors in `Tv-Alert-Mobile/`.
2. **Three-Way File Parity**:
   - Confirmed 0 diffs between `page.tsx`, `Tv-Alert-Mobile/src/app/page.tsx`, and `RemoteURL/page.tsx`.
3. **Backup Synchronization**:
   - Synced to `Backups/TLCS_v5.0_Complete_Backup_20261122_133000/`.
4. **Git Repository Status**:
   - Committed and pushed to `main` across `Tv-Alert-Mobile`, `RemoteURL`, and root.
