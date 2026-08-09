with open('/Users/vishant/Documents/Project/TV Indicator/TLCS_Live_Pivot_Alerts.pine', 'r') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "bool LightningBuy  =" in line and "longAllowed and dayallowed" not in line:
        new_lines.append("// ====================================================================\n")
        new_lines.append("// ── GATING LOGIC (H4/L4 & DAY ALLOWED) ──────────────────────────────\n")
        new_lines.append("// ====================================================================\n")
        new_lines.append("bool longAllowed = close < H4\n")
        new_lines.append("bool shortAllowed = close > L4\n")
        new_lines.append("bool dayallowed = true\n\n")
        new_lines.append("bool LightningBuy  = ((CanBuy and ScalpBuy)   or (hasBullishDiv[1] and GrS)) and longAllowed and dayallowed\n")
    elif "bool LightningSell =" in line and "shortAllowed and dayallowed" not in line:
        new_lines.append("bool LightningSell = ((CanSell and ScalpSell) or (hasBearishDiv[1] and ReS)) and shortAllowed and dayallowed\n")
    elif "bool JustMissileBuy  =" in line and "longAllowed and dayallowed" not in line:
        new_lines.append("bool JustMissileBuy  = CanBuy and not LightningBuy and longAllowed and dayallowed\n")
    elif "bool JustMissileSell =" in line and "shortAllowed and dayallowed" not in line:
        new_lines.append("bool JustMissileSell = CanSell and not LightningSell and shortAllowed and dayallowed\n")
    elif "bool JustScalpBuy  =" in line and "longAllowed and dayallowed" not in line:
        new_lines.append("bool JustScalpBuy  = ScalpBuy and not LightningBuy and longAllowed and dayallowed\n")
    elif "bool JustScalpSell =" in line and "shortAllowed and dayallowed" not in line:
        new_lines.append("bool JustScalpSell = ScalpSell and not LightningSell and shortAllowed and dayallowed\n")
    elif "if (buyCond or sellCond) and not alreadyOpenedThisBar and (not isSideways or NCPR)" in line:
        new_lines.append("    bool _buy = buyCond and close < H4\n")
        new_lines.append("    bool _sell = sellCond and close > L4\n")
        new_lines.append("    if (_buy or _sell) and not alreadyOpenedThisBar and (not isSideways or NCPR)\n")
    elif "TradeLogic newTrade = initializeTradeSession(settings, buyCond ? longName : shortName)" in line:
        new_lines.append("        TradeLogic newTrade = initializeTradeSession(settings, _buy ? longName : shortName)\n")
    else:
        new_lines.append(line)

with open('/Users/vishant/Documents/Project/TV Indicator/TLCS_Live_Pivot_Alerts.pine', 'w') as f:
    f.writelines(new_lines)
print("Applied allowed logic")
