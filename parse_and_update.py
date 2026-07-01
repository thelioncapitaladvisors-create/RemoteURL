import json
import re

with open('parse_watchlists.py', 'r') as f:
    pass # we already ran it and have the json output in terminal, but let's just use the python script to generate a replace script

# Let's just output the exact JSON we got
market_symbols_json = """{
  "nifty": [
    "ADANIENT",
    "ADANIPORTS",
    "APOLLOHOSP",
    "ASIANPAINT",
    "AXISBANK",
    "BAJAJ-AUTO",
    "BAJAJFINSV",
    "BAJFINANCE",
    "BHARTIARTL",
    "BPCL",
    "BRITANNIA",
    "CIPLA",
    "COALINDIA",
    "DIVISLAB",
    "DRREDDY",
    "EICHERMOT",
    "GRASIM",
    "HCLTECH",
    "HDFCBANK",
    "HDFCLIFE",
    "HEROMOTOCO",
    "HINDALCO",
    "HINDUNILVR",
    "ICICIBANK",
    "INDUSINDBK",
    "INFY",
    "ITC",
    "JSWSTEEL",
    "KOTAKBANK",
    "LT",
    "LTIMindtree",
    "M&M",
    "MARUTI",
    "NESTLEIND",
    "NTPC",
    "ONGC",
    "POWERGRID",
    "RELIANCE",
    "SBILIFE",
    "SBIN",
    "SHRIRAMFIN",
    "SUNPHARMA",
    "TATACONSUM",
    "TATAMOTORS",
    "TATASTEEL",
    "TCS",
    "TECHM",
    "TITAN",
    "ULTRACEMCO",
    "WIPRO"
  ],
  "mcx": [
    "ALUMINIUM",
    "ALUMINIUMM",
    "COPPER",
    "COTTON",
    "CRUDEOIL",
    "CRUDEOILM",
    "GOLD",
    "GOLDM",
    "GOLDPETAL",
    "LEAD",
    "LEADMINI",
    "MENTHAOIL",
    "NATURALGAS",
    "NATURALGASM",
    "NICKEL",
    "NICKELMINI",
    "SILVER",
    "SILVERM",
    "SILVERMIC",
    "ZINC",
    "ZINCMINI"
  ],
  "nymex": [
    "CL",
    "GC",
    "HG",
    "HO",
    "NG",
    "PA",
    "PL",
    "RB",
    "SI"
  ],
  "crypto": [
    "ADAUSDT",
    "APTUSDT",
    "ARBUSDT",
    "ATOMUSDT",
    "AVAXUSDT",
    "BCHUSDT",
    "BNBUSDT",
    "BTCUSDT",
    "DOGEUSDT",
    "DOTUSDT",
    "ETHUSDT",
    "FILUSDT",
    "ICPUSDT",
    "LINKUSDT",
    "LTCUSDT",
    "NEARUSDT",
    "POLUSDT",
    "SHIBUSDT",
    "SOLUSDT",
    "STXUSDT",
    "TONUSDT",
    "TRXUSDT",
    "UNIUSDT",
    "XLMUSDT",
    "XRPUSDT"
  ],
  "forex": [
    "AUDCAD",
    "AUDINR",
    "AUDJPY",
    "AUDNZD",
    "AUDUSD",
    "CADJPY",
    "EURAUD",
    "EURCAD",
    "EURCHF",
    "EURGBP",
    "EURINR",
    "EURJPY",
    "EURUSD",
    "GBPAUD",
    "GBPCAD",
    "GBPCHF",
    "GBPINR",
    "GBPJPY",
    "GBPUSD",
    "JPYINR",
    "NZDUSD",
    "USDCAD",
    "USDCHF",
    "USDINR",
    "USDJPY"
  ],
  "world": [
    "AU200",
    "DE40",
    "EU50",
    "FR40",
    "HK50",
    "JP225",
    "NAS100",
    "SPX500",
    "UK100",
    "US2000",
    "US30"
  ]
}"""

replacement = "const MARKET_SYMBOLS = " + market_symbols_json + ";"

# update page.tsx
with open('Tv-Alert-Mobile/src/app/page.tsx', 'r') as f:
    content = f.read()
    
# We need to replace the `const MARKET_SYMBOLS: Record<string, string[]> = { ... };` block
content = re.sub(r'const MARKET_SYMBOLS: Record<string, string\[\]> = \{[\s\S]*?\n\};\n', f'const MARKET_SYMBOLS: Record<string, string[]> = {market_symbols_json};\n', content)
with open('Tv-Alert-Mobile/src/app/page.tsx', 'w') as f:
    f.write(content)

# update index.html
with open('TLCS_Website_Deploy/index.html', 'r') as f:
    content = f.read()

content = re.sub(r'const MARKET_SYMBOLS = \{[\s\S]*?\n                \};\n', f'const MARKET_SYMBOLS = {market_symbols_json};\n', content)
with open('TLCS_Website_Deploy/index.html', 'w') as f:
    f.write(content)

print("Updated page.tsx and index.html")
