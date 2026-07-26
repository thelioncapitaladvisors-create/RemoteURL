# TLCS System Update - Instagram Automated Marketing Funnel

## 1. Zero-Touch Instagram Architecture
**Feature:** Fully automated social media dispatch engine (`cron-instagram-stats.js`) designed to organically drive traffic from Instagram directly to the web dashboard with zero manual management required.

## 2. Market-Specific Triggers
**Logic:** The system utilizes scheduled serverless Cron jobs that are rigidly bound to the precise daily closing times of the 6 distinct global markets:
- NIFTY (15:35 IST)
- MCX (23:45 IST)
- NYMEX / Forex / World Indices (17:00 EST)
- Cryptocurrency (00:00 UTC)

## 3. Real-Time Metric Aggregation
**Processing:** At market close, the engine securely queries the Supabase `signals` database to calculate exact, unadulterated performance statistics:
- **Daily (Session Close):** Executed trades, Win Rate, Profit Factor, Average Return, Average Winner/Loser, and the Best Performing Symbol.
- **Weekly (WTD) & All-Time (Cumulative):** Long-term edge statistics pulled from `weekly_performance_logs`.

## 4. Meta Graph API Dispatch
**Execution:** The engine dynamically formats an emoji-rich, highly readable caption equipped with relevant SEO hashtags (e.g., `#Nifty50`, `#CryptoTrading`). It then pushes the generated report image and caption directly to the live @thelioncapitaladvisors Instagram feed using official Meta Graph API tokens, completely circumventing the need for third-party automation tools like Zapier.
