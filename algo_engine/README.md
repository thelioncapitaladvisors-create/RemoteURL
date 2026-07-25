# DhanHQ MCX Execution Engine

This Python daemon listens to your Supabase `tv_signals` table for new TradingView webhooks and automatically places the corresponding order on your Dhan account using the DhanHQ SDK.

## Setup

1. **Install Dependencies**
   Run the following command to install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   - Copy `.env.example` to `.env`.
   - Add your Supabase URL and Service Role Key (needed to read realtime database entries).
   - Add your Dhan Client ID and Access Token (generated via [dhan.dev](https://dhan.dev)).
   - Set `PAPER_TRADING=False` only when you are ready to place real live orders. When True, it only prints what it would do.

3. **Update Security IDs**
   In `dhan_executor.py`, you must update the `MCX_SYMBOLS` mapping with the CURRENT security IDs for the active expiry month. You can download the full CSV of active security IDs daily from Dhan's API documentation portal.

## Running the Engine

To start the engine locally or on your server (like AWS EC2 or DigitalOcean):
```bash
python dhan_executor.py
```

The script polls the Supabase database every 2 seconds for new signals. If a signal arrives for a mapped MCX symbol, it will automatically place an `INTRA` Limit/Market order on Dhan.

## Security Warning
Do not commit your `.env` file to GitHub. It contains your live broker access tokens.
