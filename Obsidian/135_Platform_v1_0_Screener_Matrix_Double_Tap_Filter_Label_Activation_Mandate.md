# 135 — Platform v1.0 Screener Matrix Filter Label Double-Tap / Double-Click Activation Mandate

**Date**: November 27, 2026  
**Status**: Canonical Production Release (`v1.0.0`)  
**Target Files**: `Tv-Alert-Mobile/src/app/globals.css`, `page.tsx`, `RemoteURL/page.tsx`, `Tv-Alert-Mobile/src/app/page.tsx`, `AGENTS.md`, `.agents/AGENTS.md`, `RemoteURL/AGENTS.md`, `RemoteURL/.agents/AGENTS.md`

---

## 1. Executive Summary

In response to the user's explicit directive ("Filter names becomes visible on hover or touch. Make them visible only when clicked twice/ double tap"), all hover and single-touch activation triggers for sticky row labels (`.table-row-label`) across 7-Day Performance & Blueprint Matrix tables were eliminated. Floating tooltip bubbles representing indicator filter names (`Outside Day Blueprint`, `Scalp`, etc.) are now strictly gated behind an intentional **double-click (desktop)** or **double-tap (mobile)** interaction.

---

## 2. Problem Statement & User Experience Friction

In the horizontally scrollable 7-day screener matrix tables, when scrolled right, the left sticky column collapses to a 48px strip displaying icons (💥, 🧭, 📈, 🛑, 🏃, ⚡, 🎯, etc.).
- **Desktop Hover Friction**: Moving the mouse cursor across the screen inadvertently hovered over `.table-row-label` elements, spawning black floating tooltip bubbles that obscured adjacent data cells.
- **Mobile Touch Friction**: Scrolling through days horizontally or swiping vertically triggered `:active` states or single tap events on touch devices, causing unwanted label popovers to flash and block cell values.

---

## 3. Implementation Details

### A. Style Sheet Elimination of `:hover` & `:active` (`globals.css`)
- Replaced all `:hover` and `:active` rules for `.table-row-label` in `Tv-Alert-Mobile/src/app/globals.css` with a dedicated `.table-row-label-active` class.
- Updated all theme-specific style overrides (`.theme-light`, `.theme-gray`, `.theme-lion`, `.theme-goldengate`, `.theme-goldengate-light`) so they only apply when `.table-row-label-active` is explicitly attached.
- When resting or hovered, `.table-row-label` retains `display: none !important; opacity: 0; pointer-events: none;`.

### B. Double-Click & Fast Double-Tap Event Architecture (`page.tsx`)
A global event listener was attached to manage interaction state deterministically:
1. **Desktop Double-Click (`dblclick`)**:
   - Inspects whether the clicked target resides inside `.table-row-sticky` or a cell containing `.table-row-label`.
   - Toggles `.table-row-label-active` on the matched label element.
2. **Mobile Fast Double-Tap (`touchend`)**:
   - Measures time delta $\Delta t$ between consecutive tap events on the same cell:
     $$40	ext{ ms} \le \Delta t \le 380	ext{ ms}$$
   - If $\Delta t$ falls within the double-tap window on the same target, toggles `.table-row-label-active`.
   - Single taps, dragging, or horizontal scrolling never trigger the active state.
3. **Auto-Dismiss & Clean Teardown**:
   - Active labels automatically dismiss after a 4-second timeout.
   - Any tap outside the active cell immediately dismisses all open labels.
   - Double-tapping the same cell again dismisses the label immediately.

---

## 4. Verification & Validation

- **Next.js Production Build**: Tested via `npm --prefix Tv-Alert-Mobile run build` on Node v20.20.2. Build succeeded with 0 errors (`✓ Compiled successfully`, `✓ Generating static pages (8/8)`).
- **Multi-Repository Parity**: Synchronized identically across `Tv-Alert-Mobile`, `RemoteURL`, root `page.tsx`, and `Project Backup/Tv-Alert-Mobile/`.
- **Zero Side Modifications**: No business logic, calculation engines, or Pine Script code altered.
