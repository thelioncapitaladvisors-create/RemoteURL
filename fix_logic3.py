with open('/Users/vishant/Documents/Project/TV Indicator/TLCS_Live_Pivot_Alerts.pine', 'r') as f:
    text = f.read()

old1 = """updateTradeVisuals(Settings settings, TradeLogic trade, TradeVisuals visuals) =>
    // 1. PERMANENT DELETION 
    if trade.isClosed
        deleteTradeVisuals(visuals) 
        
    // 2. DRAW ACTIVE TRADES 
    if not trade.isClosed


        label.set_xy(visuals.entryMarkerLabel,    int(math.min(bar_index, trade.startBarIndex) - 15), trade.entryLevel)
        string entryIcon = str.contains(trade.tradeDirection, 'LIGHTNING') ? '⚡ ' : '🔰 '
        label.set_text(visuals.entryMarkerLabel, entryIcon + str.tostring(trade.entryLevel, format.mintick))
        updateLine(visuals.entryMarkerLine,      trade.startBarIndex, trade.entryLevel)
        
        label.set_xy(visuals.stopLossMarkerLabel, int(math.min(bar_index, trade.startBarIndex) - 15), trade.slLevel)
        label.set_text(visuals.stopLossMarkerLabel, '⛔ ' + str.tostring(trade.slLevel, format.mintick))
        updateLine(visuals.stopLossMarkerLine,   trade.startBarIndex, trade.slLevel)
        
        if trade.tp1Triggered
            label.set_xy(visuals.tp1Label, int(math.min(bar_index, trade.startBarIndex) - 15), trade.tp1Level)
            label.set_text(visuals.tp1Label, '✅ ' + str.tostring(trade.tp1Level, format.mintick))
            updateLine(visuals.tp1Line, trade.startBarIndex, na)
        else
            label.set_xy(visuals.tp1Label, int(math.min(bar_index, trade.startBarIndex) - 15), trade.tp1Level)
            label.set_text(visuals.tp1Label, '🎯 ' + str.tostring(trade.tp1Level, format.mintick))
            updateLine(visuals.tp1Line, trade.startBarIndex, trade.tp1Level)
            
        if trade.tp2Triggered
            label.set_xy(visuals.tp2Label, int(math.min(bar_index, trade.startBarIndex) - 15), trade.tp2Level)
            label.set_text(visuals.tp2Label, '✅ ' + str.tostring(trade.tp2Level, format.mintick))
            updateLine(visuals.tp2Line, trade.startBarIndex, na)
        else if trade.tp1Triggered
            label.set_xy(visuals.tp2Label, int(math.min(bar_index, trade.startBarIndex) - 15), trade.tp2Level)
            label.set_text(visuals.tp2Label, '🎯 ' + str.tostring(trade.tp2Level, format.mintick))
            updateLine(visuals.tp2Line, trade.startBarIndex, trade.tp2Level)
        else
            label.set_xy(visuals.tp2Label, na, na)
            updateLine(visuals.tp2Line, trade.startBarIndex, na)
            
        if trade.tp3Triggered
            label.set_xy(visuals.tp3Label, int(math.min(bar_index, trade.startBarIndex) - 15), trade.tp3Level)
            label.set_text(visuals.tp3Label, '✅ ' + str.tostring(trade.tp3Level, format.mintick))
            updateLine(visuals.tp3Line, trade.startBarIndex, na)
        else if trade.tp2Triggered
            label.set_xy(visuals.tp3Label, int(math.min(bar_index, trade.startBarIndex) - 15), trade.tp3Level)
            label.set_text(visuals.tp3Label, '🎯 ' + str.tostring(trade.tp3Level, format.mintick))
            updateLine(visuals.tp3Line, trade.startBarIndex, trade.tp3Level)
        else
            label.set_xy(visuals.tp3Label, na, na)
            updateLine(visuals.tp3Line, trade.startBarIndex, na)
            
        if trade.tp4Triggered
            label.set_xy(visuals.tp4Label, int(math.min(bar_index, trade.startBarIndex) - 15), trade.tp4Level)
            label.set_text(visuals.tp4Label, '✅ ' + str.tostring(trade.tp4Level, format.mintick))
            updateLine(visuals.tp4Line, trade.startBarIndex, na)
        else if trade.tp3Triggered
            label.set_xy(visuals.tp4Label, int(math.min(bar_index, trade.startBarIndex) - 15), trade.tp4Level)
            label.set_text(visuals.tp4Label, '🎯 ' + str.tostring(trade.tp4Level, format.mintick))
            updateLine(visuals.tp4Line, trade.startBarIndex, trade.tp4Level)
        else
            label.set_xy(visuals.tp4Label, na, na)
            updateLine(visuals.tp4Line, trade.startBarIndex, na)"""

new1 = """updateTradeVisuals(Settings settings, TradeLogic trade, TradeVisuals visuals) =>
    bool isInvalidated = trade.isClosed and not trade.hasHitEntry
    
    // 1. PERMANENT DELETION 
    if trade.emaExitTriggered or isInvalidated
        deleteTradeVisuals(visuals) 
        
    // 2. DRAW ACTIVE TRADES 
    if not (trade.emaExitTriggered or isInvalidated) and trade.hasHitEntry
        // ✅ Only generate the visuals the exact split-second the entry is touched!
        if na(visuals.entryMarkerLine) and settings.showTPSL
            generateTradeVisuals(settings, trade, visuals)

        label.set_xy(visuals.entryMarkerLabel,    int(math.min(bar_index, trade.startBarIndex) - 15), trade.entryLevel)
        string entryIcon = str.contains(trade.tradeDirection, 'LIGHTNING') ? '⚡ ' : '🔰 '
        label.set_text(visuals.entryMarkerLabel, entryIcon + str.tostring(trade.entryLevel, format.mintick))
        updateLine(visuals.entryMarkerLine,      trade.startBarIndex, trade.entryLevel)
        
        label.set_xy(visuals.stopLossMarkerLabel, int(math.min(bar_index, trade.startBarIndex) - 15), trade.slLevel)
        label.set_text(visuals.stopLossMarkerLabel, '⛔ ' + str.tostring(trade.slLevel, format.mintick))
        updateLine(visuals.stopLossMarkerLine,   trade.startBarIndex, trade.slLevel)
        
        if trade.tp1Triggered
            label.set_xy(visuals.tp1Label, int(math.min(bar_index, trade.startBarIndex) - 15), trade.tp1Level)
            label.set_text(visuals.tp1Label, '✅ ' + str.tostring(trade.tp1Level, format.mintick))
            updateLine(visuals.tp1Line, trade.startBarIndex, na)
        else
            label.set_xy(visuals.tp1Label, int(math.min(bar_index, trade.startBarIndex) - 15), trade.tp1Level)
            label.set_text(visuals.tp1Label, '🎯 ' + str.tostring(trade.tp1Level, format.mintick))
            updateLine(visuals.tp1Line, trade.startBarIndex, trade.tp1Level)
            
        if trade.tp2Triggered
            label.set_xy(visuals.tp2Label, int(math.min(bar_index, trade.startBarIndex) - 15), trade.tp2Level)
            label.set_text(visuals.tp2Label, '✅ ' + str.tostring(trade.tp2Level, format.mintick))
            updateLine(visuals.tp2Line, trade.startBarIndex, na)
        else if trade.tp1Triggered
            label.set_xy(visuals.tp2Label, int(math.min(bar_index, trade.startBarIndex) - 15), trade.tp2Level)
            label.set_text(visuals.tp2Label, '🎯 ' + str.tostring(trade.tp2Level, format.mintick))
            updateLine(visuals.tp2Line, trade.startBarIndex, trade.tp2Level)
        else
            label.set_xy(visuals.tp2Label, na, na)
            updateLine(visuals.tp2Line, trade.startBarIndex, na)
            
        if trade.tp3Triggered
            label.set_xy(visuals.tp3Label, int(math.min(bar_index, trade.startBarIndex) - 15), trade.tp3Level)
            label.set_text(visuals.tp3Label, '✅ ' + str.tostring(trade.tp3Level, format.mintick))
            updateLine(visuals.tp3Line, trade.startBarIndex, na)
        else if trade.tp2Triggered
            label.set_xy(visuals.tp3Label, int(math.min(bar_index, trade.startBarIndex) - 15), trade.tp3Level)
            label.set_text(visuals.tp3Label, '🎯 ' + str.tostring(trade.tp3Level, format.mintick))
            updateLine(visuals.tp3Line, trade.startBarIndex, trade.tp3Level)
        else
            label.set_xy(visuals.tp3Label, na, na)
            updateLine(visuals.tp3Line, trade.startBarIndex, na)
            
        if trade.tp4Triggered
            label.set_xy(visuals.tp4Label, int(math.min(bar_index, trade.startBarIndex) - 15), trade.tp4Level)
            label.set_text(visuals.tp4Label, '✅ ' + str.tostring(trade.tp4Level, format.mintick))
            updateLine(visuals.tp4Line, trade.startBarIndex, na)
        else if trade.tp3Triggered
            label.set_xy(visuals.tp4Label, int(math.min(bar_index, trade.startBarIndex) - 15), trade.tp4Level)
            label.set_text(visuals.tp4Label, '🎯 ' + str.tostring(trade.tp4Level, format.mintick))
            updateLine(visuals.tp4Line, trade.startBarIndex, trade.tp4Level)
        else
            label.set_xy(visuals.tp4Label, na, na)
            updateLine(visuals.tp4Line, trade.startBarIndex, na)"""

if old1 in text:
    print("Found old1!")
    text = text.replace(old1, new1)
else:
    print("Could not find old1")

with open('/Users/vishant/Documents/Project/TV Indicator/TLCS_Live_Pivot_Alerts.pine', 'w') as f:
    f.write(text)

