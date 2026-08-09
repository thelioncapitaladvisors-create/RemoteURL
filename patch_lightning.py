with open('/Users/vishant/Documents/Project/TV Indicator/TLCS_Live_Pivot_Alerts.pine', 'r') as f:
    lines = f.readlines()

new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    if "CanSignalFunc() => LightningBuy" in line:
        new_lines.append("bool LightningBuyPure  = (CanBuy and ScalpBuy)\n")
        new_lines.append("bool LightningSellPure = (CanSell and ScalpSell)\n\n")
        new_lines.append("CanSignalFunc() => LightningBuyPure\n")
        new_lines.append("ERSignalFunc() => LightningSellPure\n")
        i += 2 # Skip CanSignalFunc and ERSignalFunc
    elif "[CanBuy, CanSell, ScalpBuy, ScalpSell, LightningBuy, LightningSell]" in line:
        new_lines.append("    [CanBuy, CanSell, ScalpBuy, ScalpSell, LightningBuyPure, LightningSellPure]\n")
        i += 1
    elif "plotshape(isBullishDiv, title=\"Bullish Divergence\"" in line:
        new_lines.append(line.replace("shape.triangleup", "shape.xcross"))
        i += 1
    elif "plotshape(isBearishDiv, title=\"Bearish Divergence\"" in line:
        new_lines.append(line.replace("shape.triangledown", "shape.xcross"))
        i += 1
    else:
        new_lines.append(line)
        i += 1

with open('/Users/vishant/Documents/Project/TV Indicator/TLCS_Live_Pivot_Alerts.pine', 'w') as f:
    f.writelines(new_lines)
print("Applied LightningPure and xcross patches")
