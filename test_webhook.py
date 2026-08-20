import urllib.request
import json
import time

url = "https://thelioncapitalsolutions.com/.netlify/functions/process-webhook-background"
payload = {"secret": "675d6a25933d3fc1b78b45ba2d6b400c0d1598e6780e9b8ae4ea1b1f824d89eb", "trigger": "Ping"}
data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})

start = time.time()
try:
    with urllib.request.urlopen(req) as f:
        res = f.read().decode('utf-8')
        print(f"Status: {f.status}")
        print(f"Response: {res}")
except Exception as e:
    print(f"Error: {e}")
print(f"Time: {time.time() - start:.3f}s")
