import urllib.request
import json
import urllib.parse

symbol = 'NZDUSD'
yahoo_symbol = symbol + '=X'  # Forex on Yahoo Finance requires =X usually, let's test both
url1 = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol)}?interval=1d&range=1d&includePrePost=false"
url2 = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(yahoo_symbol)}?interval=1d&range=1d&includePrePost=false"

req1 = urllib.request.Request(url1, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req1) as response:
        print("Response for NZDUSD:", json.loads(response.read().decode())['chart']['error'])
except Exception as e:
    print("Error for NZDUSD:", e)

req2 = urllib.request.Request(url2, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req2) as response:
        data = json.loads(response.read().decode())
        print("Response for NZDUSD=X price:", data['chart']['result'][0]['meta']['regularMarketPrice'])
except Exception as e:
    print("Error for NZDUSD=X:", e)
