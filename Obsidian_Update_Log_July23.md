# Version 1.5.0 Update Log - July 23, 2026

## 🛠️ Critical Architectural Fixes & System Upgrades

### 1. Permanent Single Source of Truth for Outcome Resolution (`exact_pct` Math Priority)
- **Root Cause Identified**: Previous implementations of `resolveOutcome` evaluated status strings (such as `"Hit B/E"` or `"Hit Initial SL"`) **before** checking price math (`metadata.exact_pct`). This caused SHORT trades closing with positive profit (+1.35%, +1.33%) to be incorrectly hijacked into `LOSS` or `BREAKEVEN` outcomes, inflating losses and producing artificial **0% Win Rate / 0.00 Profit Factor** readings despite a +6.29% equity curve.
- **Permanent Solution Deployed**:
  1. **Frontend Priority**: Updated all 5 canonical `resolveOutcome` implementations across [`trade-metrics.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/trade-metrics.js), [`scanner.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/scanner.js), [`commodity-scanner.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/commodity-scanner.js), [`dashboard.html`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/dashboard.html), and [`page.tsx`](file:///Users/vishant/Documents/Project/Tv-Alert-Mobile/src/app/page.tsx) to evaluate `exact_pct` math **at Step 2**, BEFORE keyword string matching at Step 3 (`exact_pct > 0 → WIN`, `< 0 → LOSS`, `= 0 → BREAKEVEN`).
  2. **Database Trigger**: Created and applied [`AUTO_CORRECT_OUTCOME_TRIGGER.sql`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/AUTO_CORRECT_OUTCOME_TRIGGER.sql) directly in Supabase PostgreSQL (`trg_auto_correct_outcome`). This BEFORE INSERT/UPDATE trigger enforces outcome math at the database write layer, ensuring corrupted strings can never commit.
  3. **Self-Healing Cron**: Built and deployed [`cron-heal-outcomes.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/netlify/functions/cron-heal-outcomes.js) running every 30 minutes on Netlify to auto-scan up to 2000 closed trades and repair any anomalous outcome values silently.
  4. **Fixed `dashboard.html` Fallback**: Fixed a regression in `dashboard.html` where `TRAIL` status without `exact_pct` was erroneously defaulting to `WIN`.

---

### 2. Pine Script Indicator & Webhook Payload Hardening
- **JSON Control Character Sanitization**: Resolved Pine Script `SyntaxError` crashes caused by unescaped multiline newlines (`\n`) in indicator text strings (`'TOP \n SWING \n \n'`). Added `cleanBiasOrDayType` and `str.replace_all(..., '\n', ' ')` sanitization across `process-webhook-background.js`, `route.ts`, and Pine Script alert helpers (`sendAlert`, `sendTrailingSLAlert`, `finalizeTrade`).
- **Safe Boolean Indexing**: Fixed Pine Script v5/v6 `nz()` compiler error (`CE10123`) on `series bool` by using explicit non-null boolean checks `(TopSwingZ[1] == true)` and `(BEARS[1] == true)`.
- **Parameter Sequence Alignment**: Re-aligned `initializeAndPushTrade` helper parameter ordering (`z1, dX, mX, d1_message`) to match `sendAlert` function signatures, ensuring Zone, Opening Bias, and Day Type attributes do not swap.
- **Multi-Key SWING Extraction**: Updated backend webhooks and frontend metrics to defensively map all SWING key variants (`d1`, `market_status`, `SWING`, `swing`, `tradeMessage`).

---

### 3. Telegram Channel Signal Broadcast Setup
- **HTML Parse Mode Upgrade**: Upgraded `sendTelegramAlert` in both Netlify background workers ([`process-webhook-background.js`](file:///Users/vishant/Documents/Project/TLCS_Website_Deploy/netlify/functions/process-webhook-background.js)) and Next.js mobile endpoints ([`route.ts`](file:///Users/vishant/Documents/Project/Tv-Alert-Mobile/src/app/api/webhook/route.ts)) to HTML parse mode, preventing API crashes on special characters (`!`, `_`) in symbol tickers like `NG1!`, `SILVER1!`, `GC1!`.
- **Bot Administrator Configured**: Created `@TLCS_bot` via `@BotFather`, added it as Channel Administrator with post message permissions in the Telegram channel **TLCS Alerts**.
- **Netlify Environment Variables**: Bound `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` across builds, functions, and runtime in Netlify. Triggered fresh production deploy `6e3b5fb`.

---

### 4. Canonical System Rules Updated (`AGENTS.md`)
- Updated [.agents/AGENTS.md](file:///Users/vishant/Documents/Project/.agents/AGENTS.md#L67-L125) with the canonical bit-for-bit `resolveOutcome` code block, regression history notes, and single-source-of-truth rules to prevent future AI or developer regressions.

---

### 5. Repository & Submodule Synchronization
- **`TLCS_Website_Deploy`**: Committed and pushed commits `1501735`, `98dbc83`, `1b13d51`, `215b712`, `6e3b5fb` to `main`.
- **`Tv-Alert-Mobile`**: Committed and pushed commits `e65400c`, `589d8dd`, `3e03d54` to `main`.
- **Root Repository**: Committed and pushed commits `8d99380` and latest submodule pointer updates to `main`.
