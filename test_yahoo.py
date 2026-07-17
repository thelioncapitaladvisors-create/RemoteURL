import urllib.request
import json

def test(symbol):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1d"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            price = data.get('chart', {}).get('result', [{}])[0].get('meta', {}).get('regularMarketPrice')
            print(f"{symbol} -> {price}")
    except Exception as e:
        print(f"{symbol} -> ERROR {e}")

test('RELIANCE.NS')
test('GOLD.MC')
test('MGC=F')
test('CL=F')
test('^DJI')
test('^GSPC')
test('^NDX')
