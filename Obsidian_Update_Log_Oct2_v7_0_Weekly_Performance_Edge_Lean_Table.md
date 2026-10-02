# TLCS Architecture Audit Log: Weekly Performance Edge Calmar Removal (Lean Table)

**Release**: `v7.0.0` (Platform Baseline v7.0)  
**Timestamp**: 2026-10-02T11:29:00+05:30  
**Scope**: Mobile Terminal PWA (`Tv-Alert-Mobile`), Agent Mandates (`.agents/AGENTS.md`)  

---

## 1. Summary of Changes

- Removed `Calmar` column from `Weekly Performance Edge` table in `Tv-Alert-Mobile/src/app/page.tsx` (`ANALYTICS` tab).
- Rebalanced the 6 remaining columns (`Wk` 8%, `Date` 21%, `Win Rate` 18%, `Net Edge` 19%, `PF` 16%, `Kelly` 18%).
- Removed unused `cCalmar`, `calmarVal`, and `calmarColor` variables in table render scope.
- Verified TypeScript compilation: `tsc --noEmit` $\rightarrow$ **PASS (0 errors)**.
