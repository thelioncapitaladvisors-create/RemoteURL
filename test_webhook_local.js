const payload = {
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
};

fetch('http://localhost:3000/api/webhook', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(payload)
})
.then(res => res.text())
.then(console.log)
.catch(console.error);
