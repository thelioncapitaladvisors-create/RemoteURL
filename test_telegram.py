import sys, urllib.request, json, ssl

def test_telegram(token, chat_id):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": "<b>🚨 TLCS Alerts Test Message</b>\nTelegram Bot Dispatcher is connected and working!",
        "parse_mode": "HTML"
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            res = json.loads(resp.read().decode('utf-8'))
            print("Telegram API Response:", res)
            return res
    except urllib.error.HTTPError as e:
        err = e.read().decode('utf-8')
        print(f"Telegram HTTP Error {e.code}:", err)
        return {"ok": False, "error": err}
    except Exception as e:
        print("Error:", e)
        return {"ok": False, "error": str(e)}

if __name__ == '__main__':
    if len(sys.argv) > 2:
        test_telegram(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python3 test_telegram.py <BOT_TOKEN> <CHAT_ID>")
