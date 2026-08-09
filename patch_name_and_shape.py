with open('/Users/vishant/Documents/Project/TV Indicator/TLCS_Live_Pivot_Alerts.pine', 'r') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "indicator('TLCS Live Pivot Alerts'" in line:
        new_lines.append(line.replace("indicator('TLCS Live Pivot Alerts'", "indicator('TLCS All Signal Alerts'"))
    elif "plotshape(isBullishDiv, title=\"Bullish Divergence\"" in line:
        new_lines.append(line.replace("shape.triangleup", "shape.xcross"))
    elif "plotshape(isBearishDiv, title=\"Bearish Divergence\"" in line:
        new_lines.append(line.replace("shape.triangledown", "shape.xcross"))
    else:
        new_lines.append(line)

with open('/Users/vishant/Documents/Project/TV Indicator/TLCS_Live_Pivot_Alerts.pine', 'w') as f:
    f.writelines(new_lines)
print("Applied name and shape patches")
