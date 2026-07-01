# TLCS Architecture & Webhook Logic Manual

This manual outlines the core architecture, data flows, and logical steps that power the TLCS Trading Terminal (Website and Mobile App) and its integration with TradingView.

## 1. High-Level Architecture

The TLCS system consists of:
*   **Frontend**: Website and Mobile App (React/Next.js and React Native) serving as the trading dashboard.
*   **Backend Hosting**: Netlify Functions (Serverless).
*   **Database**: Supabase (PostgreSQL) for storing signals, pivots, broker mappings, and user profiles.
*   **Data Source**: TradingView Pine Script webhooks providing real-time alerts.
*   **Broker Integration**: Dhan API for automated trade execution (`dhan-engine.js`).

## 2. Webhook Ingestion Logic

When TradingView triggers an alert, it sends a JSON payload to the Netlify webhook endpoint.

### 2.1 The Relayer (`webhook.js`)
*   **Purpose**: TradingView requires webhooks to respond within 3 seconds, or it drops the connection and marks it failed.
*   **Action**: Receives the payload and immediately dispatches it to a Netlify Background Function (`process-webhook-background.js`).
*   **Response**: Returns `200 OK` instantly to TradingView.

### 2.2 The Processor (`process-webhook-background.js`)
This is the core engine handling signal validation and database insertion.

**Step 1: Parsing & Sanitization**
*   Extracts JSON from the payload.
*   Handles edge cases like `str.tostring(na)` (bare NaN) in Pine Script.

**Step 2: Recency Guard & Timezone Handling**
*   Verifies `body.timenow` or `body.signal_ts`.
*   Resolves the timezone based on the asset (e.g., `Asia/Kolkata` for NSE/MCX, `America/New_York` for Crypto/Forex).
*   **Rule**: Rejects any signal where the TradingView timestamp does not match today's date in the asset's timezone (prevents stale signals from historical replays).

**Step 3: Routing by Signal Type**
The payload is evaluated against three distinct routes:

1.  **Pivot Update (`PivotUpdate`)**
    *   **Trigger**: Any payload that provides Bias, Day Type, or Trade Zone mid-session.
    *   **Action**: Upserts the new values into the `pivots` table to keep the dashboard dynamically in sync with indicator recalculations.
    
2.  **Outcome Update (`TradeClose` / `TrailingSLUpdate`)**
    *   **Trigger**: Exit alerts, TP targets hit, or trailing SL updates.
    *   **Action**: Locates the active signal in the `signals` table using Entry Timestamp, Order ID, or Fallback rules.
    *   **Math**: Calculates Exact Points (`exact_pts`) and Exact Percentage (`exact_pct`) using `((Exit - Entry) / Entry) * 100`. (Note: `r_multiple` is deprecated).
    *   **Execution**: Updates the signal in Supabase and triggers `executeDhanExit`.

3.  **New Signal (Trade Entry)**
    *   **Trigger**: Standard `LONG` or `SHORT` trade entries.
    *   **Market Hours Guard**: If it's an NSE stock (not 24x7 crypto), rejects signals received outside 9:15 AM - 3:45 PM IST.
    *   **Pivot Fallback**: If the entry payload lacks Bias or Day Type, the engine fetches the latest values from the `pivots` table.
    *   **Action**: Inserts the new trade into the `signals` table.
    *   **Execution**: Triggers `executeDhanEntry`.

## 3. Dhan Broker Integration (`dhan-engine.js`)

Automated execution is routed through `dhan-engine.js`:
*   **Entry**: Calculates the nearest Strike Price (CE/PE) based on the asset and entry price. Maps it to the Dhan Security ID via the `dhan_option_chain` table, and submits a Market Order.
*   **Exit**: Retrieves the Security ID mapped to the open trade and submits a Market Sell order.

## 4. Frontend Constraints (Rules & Display)

*   **Single Source of Truth**: All performance metrics (Profit Factor, Expectancy, Win Rate, Drawdown) strictly rely on `exact_pct`.
*   **Dynamic Exits**: Trailing Stops are bucketed into a dedicated `TRAIL` bucket, not incorrectly snapped to static TP levels.
*   **Symbols**: Symbols are normalized (stripping `NSE:`, `1!`) for categorization in market tabs.
*   **Labels**: Pine Script bias labels like "Double Distribution" are mapped dynamically to "DD" on the frontend for dashboard rendering.
