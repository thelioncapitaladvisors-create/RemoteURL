import urllib.request
import json

payload = {
    "symbol": "HSI",
    "exchange": "HKEX",
    "type": "SHORT SCALP",
    "entry": 18000,
    "stop": 18050,
    "target": 17950,
    "action": "ENTRY",
    "trigger": "Entry",
    "secret": "675d6a2593..."
}

url = "https://tlcs-mobile.vercel.app/api/webhook" # Guessing URL? No, I shouldn't guess live URLs.

