with open('/Users/vishant/Documents/Project/TV Indicator/TLCS_Live_Pivot_Alerts.pine', 'r') as f:
    lines = f.readlines()

new_lines = []
skip_next = False
for i, line in enumerate(lines):
    if skip_next:
        skip_next = False
        continue
        
    if "type DivergenceObject" in line:
        new_lines.append(line)
        continue
    if "Label priceLabel" in line and "type DivergenceObject" in lines[i-2]:
        new_lines.append(line)
        new_lines.append("    Label xcrossLabel\n")
        continue
    if "this.priceLabel.delete()" in line:
        new_lines.append(line)
        new_lines.append("    this.xcrossLabel.delete()\n")
        continue
    if "this.priceLabel.draw()" in line:
        new_lines.append(line)
        new_lines.append("    this.xcrossLabel.draw()\n")
        continue
    if "divergenceObject = DivergenceObject.new(priceDivergenceLine, priceDivergenceLabel, pricePoint, divergenceType)" in line:
        new_lines.append("                        color xColor = divergenceType == DivergenceType.BullishDivergence or divergenceType == DivergenceType.BullishHiddenDivergence ? color.green : color.red\n")
        new_lines.append("                        string xYloc = divergenceType == DivergenceType.BullishDivergence or divergenceType == DivergenceType.BullishHiddenDivergence ? yloc.belowbar : yloc.abovebar\n")
        new_lines.append("                        LabelProperties xcrossProps = LabelProperties.new(xloc.bar_time, xYloc, xColor, label.style_xcross, color.new(color.white, 100), size.small, force_overlay = false)\n")
        new_lines.append("                        Label xcrossLabelObj = Label.new(pricePoint, \"\", \"\", xcrossProps)\n")
        new_lines.append("                        divergenceObject = DivergenceObject.new(priceDivergenceLine, priceDivergenceLabel, xcrossLabelObj, pricePoint, divergenceType)\n")
        continue
    
    if "plotshape(isBullishDiv and not isBullishDiv[1]" in line or "plotshape(isBearishDiv and not isBearishDiv[1]" in line:
        continue
    if "plotshape(isBullishDiv," in line or "plotshape(isBearishDiv," in line:
        continue
    if "// ✅ DIVERGENCE PLOTS" in line:
        continue
        
    new_lines.append(line)

with open('/Users/vishant/Documents/Project/TV Indicator/TLCS_Live_Pivot_Alerts.pine', 'w') as f:
    f.writelines(new_lines)
print("Applied OOP xcross patch")
