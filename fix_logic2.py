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


old2 = """            if session.islastbar_regular and timeframe.isintraday and not trade.isClosed
                terminateTrade(settings, trade)
            
            if trade.slLevel != prevSL and trade.trailingSLActivated
                sendTrailingSLAlert(settings, trade, z1, dX, mX, d1_message)
                
            if not trade.isClosed
                updateTradeVisuals(settings, trade, vis)
                signalLabelUpdate(settings, trade, vis)
            else
                // Run a final update to snap lines/labels to the closing bar and handle invalidation
                updateTradeVisuals(settings, trade, vis)
                signalLabelUpdate(settings, trade, vis)
                
                // The split-second it mathematically closes, finalize and clean up!
                string closePayload = finalizeTrade(settings, trade, z1, dX, mX, d1_message)
                alert(closePayload, alert.freq_once_per_bar)"""

new2 = """            if session.islastbar_regular and timeframe.isintraday and not trade.isClosed
                terminateTrade(settings, trade)
            
            if trade.slLevel != prevSL and trade.trailingSLActivated
                sendTrailingSLAlert(settings, trade, z1, dX, mX, d1_message)
                
            if not trade.isClosed
                updateTradeVisuals(settings, trade, vis)
                signalLabelUpdate(settings, trade, vis)
            else
                // The split-second it mathematically closes, finalize and clean up!
                string closePayload = finalizeTrade(settings, trade, z1, dX, mX, d1_message)
                alert(closePayload, alert.freq_once_per_bar)
                
                // ✅ DELETES VISUALS INSTANTLY
                deleteTradeVisuals(vis) 
                
                array.remove(sessionsArr, i)
                array.remove(visualsArr, i)
                0"""

old3 = """signalLabelUpdate(Settings settings, TradeLogic trade, TradeVisuals visuals) =>
    0 """

new3 = """signalLabelUpdate(Settings settings, TradeLogic trade, TradeVisuals visuals) =>
    0"""

if old1 in text:
    print("Found old1")
    text = text.replace(old1, new1)

if old2 in text:
    print("Found old2")
    text = text.replace(old2, new2)

if old3 in text:
    print("Found old3")
    text = text.replace(old3, new3)
    
# Wait, let's fix the indicator name to v7
old_title = "indicator('TLCS All Signal Alerts (Limits Fixed)'"
new_title = "indicator('TLCS All Signal Alerts (Live Fixed)'"
if old_title in text:
    print("Found title")
    text = text.replace(old_title, new_title)


with open('/Users/vishant/Documents/Project/TV Indicator/TLCS_Live_Pivot_Alerts.pine', 'w') as f:
    f.write(text)

