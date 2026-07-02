import requests
import json
import time

payload = {
  "secret": "675d6a2593b4e7a89f9b48c6d48e02d8f764a789123b3a744a56c07d354b9f2d",
  "symbol": "BTCUSDT",
  "exchange": "BINANCE",
  "action": "LONG",
  "entry": 60000,
  "signal_ts": str(int(time.time() * 1000))
}

try:
    res = requests.post('https://thelioncapitalsolutions.com/.netlify/functions/process-webhook-background', json=payload)
    print("Status Code:", res.status_code)
except Exception as e:
    print(e)
