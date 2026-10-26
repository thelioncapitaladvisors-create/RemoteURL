# Obsidian Update Log: ALUMINI In Range / Out of Value Parser Fix

**Timestamp:** 2026-10-26 22:15 IST  
**Component:** `Tv-Alert-Mobile/src/app/page.tsx`  
**Release Tag:** `v1.0`  

### Key Fixes:
1. **Mathematical Verification**:
   - Confirmed ALUMINI opened at 327.80 on October 26, 2026.
   - Friday Oct 23 Range: 323.80 - 328.40. Value Area: 323.875 - 327.175.
   - Since 323.80 <= 327.80 <= 328.40, ALUMINI opened **INSIDE RANGE**.
   - Since 327.80 > 327.175 (VAH), ALUMINI opened **OUT OF VALUE**.
   - True classification: `IN RANGE / OUT OF VALUE`.

2. **Parser Collision Eradication**:
   - Eliminated `(s.includes('OUT') && s.includes('RANGE'))` in `resolveCanonicalBias`, which previously conflated `"IN RANGE OUT OF VALUE"` into `'OUT OF RANGE / OUT OF VALUE'`.
   - Hardened `extractDhanScreenerAssets` and `dhanScreenerSetupStats` so that `OOR` (Out of Range) strictly rejects any bias containing `IN RANGE`.
   - Updated `blueprintCategories` in Section 2 (lines 14025 and 14746) so `OOR_OOV` strictly checks `!dt.includes('IN RANGE')`.

3. **Status**:
   - Next.js build compiled successfully (`next build`).
   - All 114 python unit tests passed (`unittest`).
