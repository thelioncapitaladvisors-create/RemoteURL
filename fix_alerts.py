with open('/Users/vishant/Documents/Project/TV Indicator/TLCS_Live_Pivot_Alerts.pine', 'r') as f:
    text = f.read()

# 1. Fix sendTrailingSLAlert trigger
old_tPay = """    string _tPay = '{' + str.format(
         '"secret":"{0}","symbol":"{1}","type":"{2}","status":"{3}","entryPrice":"{4}","slLevel":"{5}","tpLevel":"{6}","zone":"{7}","dayType":"{8}","marketType":"{9}","tradeMessage":"{10}","entryTime":"{11}","entryDate":"{12}","trade_id":"{13}"',"""

new_tPay = """    string _tPay = '{' + str.format(
         '"trigger":"TrailingSLUpdate","secret":"{0}","symbol":"{1}","type":"{2}","status":"{3}","entryPrice":"{4}","slLevel":"{5}","tpLevel":"{6}","zone":"{7}","dayType":"{8}","marketType":"{9}","tradeMessage":"{10}","entryTime":"{11}","entryDate":"{12}","trade_id":"{13}"',"""

if old_tPay in text:
    print("Fixed sendTrailingSLAlert")
    text = text.replace(old_tPay, new_tPay)

# 2. Remove sendFillAlert calls and definition
# First remove the call
old_fill_call = """            // ✅ Send fill alert the instant a limit order fills
            if trade.hasHitEntry and wasUnfilled and not trade.isClosed
                sendFillAlert(settings, trade, z1, dX, mX, d1_message)"""

if old_fill_call in text:
    print("Removed sendFillAlert call")
    text = text.replace(old_fill_call, "")

# Then remove the definition
import re
pattern_fill_def = r"sendFillAlert\(Settings settings, TradeLogic trade, string z1_zone, string dX, string mX, string d1_message\) =>.*?alert\(_fPay, alert\.freq_once_per_bar\)\n\n\n"
if re.search(pattern_fill_def, text, re.DOTALL):
    print("Removed sendFillAlert definition")
    text = re.sub(pattern_fill_def, "\n", text, flags=re.DOTALL)

with open('/Users/vishant/Documents/Project/TV Indicator/TLCS_Live_Pivot_Alerts.pine', 'w') as f:
    f.write(text)

