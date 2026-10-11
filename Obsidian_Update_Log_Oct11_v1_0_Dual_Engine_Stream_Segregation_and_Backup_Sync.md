# Obsidian Update Log — October 11, 2026 (v1.0)
## Dual-Engine Stream Segregation, Zero-Crossover Hardening & Complete Production Backup

### 1. Overview & Context
Prior to commercial subscription release, an audit revealed that the mobile client was exhibiting signal crossover between the `WEBHOOK SIGNALS` stream and the `BLACK BOX` (DhanHQ) stream, causing identical DhanHQ trade counts (21 trades, `IRFC`, `SIEMENS`, `PAGEIND`) to display under Webhook mode.

### 2. Root Cause Analysis (RCA)
- **Supabase Integrity**: Live raw queries on `public.signals` (8 genuine Crypto trades) and `public.shadow_signals` (21 genuine DhanHQ trades) confirmed the database was 100% clean and properly segregated.
- **Client React State Overwrite**: In `Tv-Alert-Mobile/src/app/page.tsx` (`fetchIntradaySignals`), Stage 4 was executing `if (engineSource === 'SHADOW') setSignals(fetchedSignals)`, overwriting the Webhook state `signals` with Black Box `shadow_signals`.
- **Fetch Non-200 Trap**: When toggling back to `engineSource === 'TV'`, `/api/webhook` returned non-200 (due to rate limiting), but standard `fetch()` does not throw on HTTP status codes. The `catch (err)` Supabase fallback was bypassed, leaving `signals` state frozen with `shadow_signals`.

### 3. Engineering Fixes Implemented
1. **Strict Independent Pipeline in `fetchIntradaySignals`**:
   - Stage 1: Queries `supabase.from('signals')` directly into `setSignals(liveSignals)`. `signals` will NEVER receive shadow data.
   - Stage 2: Queries `supabase.from('shadow_signals')` directly into `setShadowSignals(blackboxSignals)`.
   - Alert audio/haptics dispatch on `currentActiveStream = engineSource === 'SHADOW' ? blackboxSignals : liveSignals`.
2. **Dual-Engine Toggle & Subtitle Harmonization**:
   - `HUB`, `LOGS`, `MARKETS`, `INSIGHTS`, `ANALYTICS` top toggle bars and subtitles evaluate `engineSource === 'SHADOW' || hubDataSource === 'DHAN'` deterministically, ensuring mutually exclusive active styles and zero UI state conflicts.
3. **Verified Production Build**:
   - Executed `npm run build` in `Tv-Alert-Mobile` (Next.js 14.2.35): compiled with 0 errors, full type validation passed across all routes.
4. **Git Release & Comprehensive Multi-Mirror Backup**:
   - Git commit in `Tv-Alert-Mobile`: `fix(engine): strict segregation of Webhook and DhanHQ BlackBox streams, prevent crossover v1.0`.
   - Release tags: `v1.0` and `v1.0.0` updated to HEAD.
   - Mirrored into `Project Backup/Tv-Alert-Mobile/`.
   - Archived complete snapshot: `Backups/TLCS_v1.0_Complete_Backup_20261011_174500` & `.zip`.
   - Updated `Backups/TLCS_Applications_v1.0_20261011.zip`.
   - Synced to external mirror `/Users/vishant/Documents/Backups/`.
