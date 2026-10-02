# TLCS Platform Architecture Note: Terminal Menu Engine Isolation & Compact Visual Skins (v7.0)

**Document ID**: `TLCS-DOC-20261002-V7-TERMINAL-MENU-ENGINE-ISOLATION`  
**Date**: October 2, 2026  
**Platform Version**: `v7.0` (`7.0.0`)  
**Target Applications**: `Tv-Alert-Mobile` (Next.js PWA), `.agents/AGENTS.md`  

---

## 1. Executive Summary

This architecture release achieves three core design objectives requested by institutional operations:
1. **Engine Selector Relocation & Header Cleanliness**: Relocated the autonomous engine switcher (`TV PROD`, `BLACK BOX LIVE`, `PARITY AUDIT`) from the main terminal header into the internal **Terminal Menu** (`TERMINAL MENU`). The primary terminal screen is now clean and uncluttered for all users.
2. **Compact Theme Buttons**: Re-engineered the `Visual Skins` theme buttons (`DARK`, `SLATE`, `LIGHT`, `THE LION`, `AUTO`) from large, space-consuming cards (`py-7 rounded-3xl`) into a sleek, ultra-compact 5-column responsive row (`py-2.5 px-1 rounded-xl`), reducing vertical height consumption by over 80%.
3. **Strict Admin-Only Menu Access**: Guaranteed that access to the `Terminal Menu` is strictly restricted to verified administrators (`APPROVED_ADMIN_EMAILS` with `admin`, `developer`, or `owner` roles). Non-admin subscribers cannot see or trigger the Menu under any circumstance.

---

## 2. Technical Implementation Specifications

### A. Terminal Menu Admin-Only Access Gating
```typescript
// 1. Header Access Check
{isAdmin && (
  <button onClick={() => setShowSettings(true)} className="...">
    <Target size={14} className="text-accent" />
    <span>Menu</span>
  </button>
)}

// 2. Modal Mount Protection
<AnimatePresence>
  {isAdmin && showSettings && (
    <motion.div ...>
      ...
    </motion.div>
  )}
</AnimatePresence>

// 3. State Invalidation Guard
useEffect(() => {
  if (!isAdmin && engineSource !== 'TV') {
    setEngineSource('TV');
  }
  if (!isAdmin && showSettings) {
    setShowSettings(false);
  }
}, [isAdmin, engineSource, showSettings]);
```

### B. Execution Engine Source Relocation
- **Source**: Removed lines from under `<header>` on the main screen.
- **Destination**: Embedded as the primary section inside `Terminal Menu`:
  - `⚡ TV PROD`
  - `🖲 BLACK BOX [LIVE]`
  - `⚖ PARITY AUDIT [100%]` (with live parity score badge)
- **Exit Action**: Selecting `PARITY AUDIT` automatically dismisses the menu modal (`setShowSettings(false)`), transitioning directly to the Parity Audit Screen.
- **Parity Audit Screen Navigation**: Provided an explicit `Exit Audit` back-button (`<ArrowLeft size={12} /> Exit Audit`) beside `Re-Audit Telemetry` to allow direct return to the primary terminal.

### C. Compact Visual Skins (Theme Selector)
- **Previous Layout**: 2-column grid + 1 full-width button with `py-7` and large icons, consuming ~260px vertical height.
- **New Layout**: 5-column responsive grid with `py-2.5 px-1 rounded-xl` and 15px icons:
  - `dark` $\rightarrow$ `DARK`
  - `gray` $\rightarrow$ `SLATE`
  - `light` $\rightarrow$ `LIGHT`
  - `lion` $\rightarrow$ `THE LION`
  - `auto` $\rightarrow$ `AUTO`
- Displays active theme badge in section header.

---

## 3. Verification & Compliance Matrix

| Target Requirement | Implementation Detail | Verification Status |
| :--- | :--- | :--- |
| **Move engine selector into Menu** | Removed from header; placed as top section in Terminal Menu | **VERIFIED** |
| **Compact theme buttons** | 5-column sleek row (`py-2.5 px-1 rounded-xl`) | **VERIFIED** |
| **Parity Audit navigation** | Added `Exit Audit` back-button on Parity Audit Screen | **VERIFIED** |
| **Admin-only Menu access** | Guarded by `isAdmin`, `showSettings` mount check, & `useEffect` hook | **VERIFIED** |
| **Subscriber restriction** | Subscribers cannot view, open, or trigger Terminal Menu | **VERIFIED** |
| **Version 7.0 Platform standard** | Maintained across all files and documentation | **VERIFIED** |
| **TypeScript compile** | `tsc --noEmit` | **PASS (0 errors)** |
