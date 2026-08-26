const https = require('https');

const payload = JSON.stringify({
  secret: "test_secret",
  trigger: "TradeFill",
  symbol: "DOGEUSDT",
  exchange: "BINANCE",
  entryPrice: 0.08424,
  entryTime: Date.now(),
  action: "LONG",
  slLevel: 0.08000,
  tpLevel: 0.09000,
  trade_id: "test_doge_123"
});

const options = {
  hostname: 'thelioncapitalsolutions.com',
  path: '/.netlify/functions/process-webhook-background',
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Content-Length': payload.length
  }
};

const req = https.request(options, (res) => {
  console.log(`STATUS: ${res.statusCode}`);
  res.on('data', (d) => {
    process.stdout.write(d);
  });
});

req.on('error', (e) => {
  console.error(e);
});

req.write(payload);
req.end();
