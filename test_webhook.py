import requests

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
  "signal_ts": "1719662100000"
}

try:
    res = requests.post('https://thelioncapital-alerts.vercel.app/api/webhook', json=payload)
    print("Vercel App:", res.text)
except Exception as e:
    print(e)

try:
    res2 = requests.post('https://thelioncapitalsolutions.com/.netlify/functions/webhook', json=payload)
    print("Netlify App:", res2.text)
except Exception as e:
    print(e)

