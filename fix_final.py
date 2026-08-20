with open('/Users/vishant/Documents/Project/TV Indicator/TLCS_Live_Pivot_Alerts.pine', 'r') as f:
    text = f.read()

# 1. Remove generateTradeVisuals from initializeAndPushTrade
old_init = """        sendAlert(settings, newTrade, dX, mX, z1, d1_message)
        if settings.showTPSL
            generateTradeVisuals(settings, newTrade, newVis)
        array.push(sessionsArr, newTrade)"""

new_init = """        sendAlert(settings, newTrade, dX, mX, z1, d1_message)
        array.push(sessionsArr, newTrade)"""

if old_init in text:
    print("Fixed initializeAndPushTrade")
    text = text.replace(old_init, new_init)

# 2. Add hasHitEntry gate to updateTradeVisuals
old_update = """updateTradeVisuals(Settings settings, TradeLogic trade, TradeVisuals visuals) =>
    // 1. PERMANENT DELETION 
    if trade.isClosed
        deleteTradeVisuals(visuals) 
        
    // 2. DRAW ACTIVE TRADES 
    if not trade.isClosed


        label.set_xy(visuals.entryMarkerLabel,    int(math.min(bar_index, trade.startBarIndex) - 15), trade.entryLevel)"""

new_update = """updateTradeVisuals(Settings settings, TradeLogic trade, TradeVisuals visuals) =>
    // 1. PERMANENT DELETION 
    if trade.isClosed
        deleteTradeVisuals(visuals) 
        
    // 2. DRAW ACTIVE TRADES 
    if not trade.isClosed and trade.hasHitEntry
        if na(visuals.entryMarkerLine) and settings.showTPSL
            generateTradeVisuals(settings, trade, visuals)

        label.set_xy(visuals.entryMarkerLabel,    int(math.min(bar_index, trade.startBarIndex) - 15), trade.entryLevel)"""

if old_update in text:
    print("Fixed updateTradeVisuals")
    text = text.replace(old_update, new_update)

# 3. Fix title
text = text.replace("indicator('TLCS All Signal Alerts (Limits Fixed)'", "indicator('TLCS All Signal Alerts (Live Plottings)'")

with open('/Users/vishant/Documents/Project/TV Indicator/TLCS_Live_Pivot_Alerts.pine', 'w') as f:
    f.write(text)

