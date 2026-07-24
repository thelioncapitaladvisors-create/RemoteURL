import urllib.request
import json
import urllib.parse

def check(symbol):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol)}?interval=1d&range=1d&includePrePost=false"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            print(f"Price for {symbol}:", data['chart']['result'][0]['meta']['regularMarketPrice'])
    except Exception as e:
        print(f"Error for {symbol}:", e)

check("BTCUSDT")
check("BTC-USD")
