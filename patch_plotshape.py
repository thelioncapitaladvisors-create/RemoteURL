with open('/Users/vishant/Documents/Project/TV Indicator/TLCS_Live_Pivot_Alerts.pine', 'r') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "plotshape(isBullishDiv, title=\"Bullish Divergence\"" in line:
        new_lines.append(line.replace("isBullishDiv,", "isBullishDiv and not isBullishDiv[1],"))
    elif "plotshape(isBearishDiv, title=\"Bearish Divergence\"" in line:
        new_lines.append(line.replace("isBearishDiv,", "isBearishDiv and not isBearishDiv[1],"))
    else:
        new_lines.append(line)

with open('/Users/vishant/Documents/Project/TV Indicator/TLCS_Live_Pivot_Alerts.pine', 'w') as f:
    f.writelines(new_lines)
print("Applied plotshape deduplication")
