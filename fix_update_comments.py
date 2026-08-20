with open('/Users/vishant/Documents/Project/TV Indicator/TLCS_Live_Pivot_Alerts.pine', 'r') as f:
    text = f.read()

old_update = """updateTradeVisuals(Settings settings, TradeLogic trade, TradeVisuals visuals) =>
    bool isInvalidated = trade.isClosed and not trade.hasHitEntry
    
    // 1. PERMANENT DELETION 
    if trade.emaExitTriggered or isInvalidated
        deleteTradeVisuals(visuals) 
        
    // 2. DRAW ACTIVE TRADES 
    if not (trade.emaExitTriggered or isInvalidated) and trade.hasHitEntry
        // ✅ Only generate the visuals the exact split-second the entry is touched!
        if na(visuals.entryMarkerLine) and settings.showTPSL
            generateTradeVisuals(settings, trade, visuals)"""

new_update = """updateTradeVisuals(Settings settings, TradeLogic trade, TradeVisuals visuals) =>
    bool isInvalidated = trade.isClosed and not trade.hasHitEntry

    // 1. PERMANENT DELETION — only EMA exits and never-filled limits
    if trade.emaExitTriggered or isInvalidated
        deleteTradeVisuals(visuals)

    // 2. DRAW FILLED TRADES ONLY
    if not (trade.emaExitTriggered or isInvalidated) and trade.hasHitEntry
        // ✅ Build the levels the split-second the limit fills
        if na(visuals.entryMarkerLine) and settings.showTPSL
            generateTradeVisuals(settings, trade, visuals)"""

if old_update in text:
    print("Fixed updateTradeVisuals comments")
    text = text.replace(old_update, new_update)

with open('/Users/vishant/Documents/Project/TV Indicator/TLCS_Live_Pivot_Alerts.pine', 'w') as f:
    f.write(text)

