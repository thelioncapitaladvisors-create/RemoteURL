import requests
import json

payload = {
  "secret": "675d6a2593b4e7a89f9b48c6d48e02d8f764a789123b3a744a56c07d354b9f2d",
  "symbol": "AUDUSD",
  "type": "SHORT SCALP",
  "action": "sell",
  "entry": 0.68985,
  "stop": 0.68860,
  "target": 0.68902,
  "status": "Active",
  "pricing_type": "LIVE",
  "signal_ts": "1719662100000",
  "opening_bias": "BULLISH"
}

res = requests.post(
    'https://thelioncapitalsolutions.com/.netlify/functions/process-webhook-background',
    data=json.dumps(payload),
    headers={'Content-Type': 'text/plain'}
)
print(res.status_code)
