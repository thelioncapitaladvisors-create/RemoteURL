const http = require('http');

const payload = {
  "symbol": "CL1!",
  "exchange": "NYMEX",
  "type": "LONG MISSILE",
  "entry": 80.50,
  "stop": 80.00,
  "target": 81.50
};

const req = http.request({
  hostname: 'market-store.online',
  path: '/api/webhook',
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  }
}, (res) => {
  let data = '';
  res.on('data', chunk => data += chunk);
  res.on('end', () => console.log('Response:', res.statusCode, data));
});

req.on('error', e => console.error(e));
req.write(JSON.stringify(payload));
req.end();
