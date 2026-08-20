with open('/Users/vishant/Documents/Project/TV Indicator/TLCS_Live_Pivot_Alerts.pine', 'r') as f:
    text = f.read()

# Edit 1: initializeAndPushTrade
old_init = """        sendAlert(settings, newTrade, dX, mX, z1, d1_message)
        array.push(sessionsArr, newTrade)
        array.push(visualsArr, newVis)"""
new_init = """        sendAlert(settings, newTrade, z1, dX, mX, d1_message)
        array.push(sessionsArr, newTrade)
        array.push(visualsArr, newVis)"""

if old_init in text:
    print("Fixed argument order in initializeAndPushTrade")
    text = text.replace(old_init, new_init)

# Edit 3: processTradeArray else branch
old_else = """            else
                // Run a final update to snap lines/labels to the closing bar and handle invalidation
                updateTradeVisuals(settings, trade, vis)
                signalLabelUpdate(settings, trade, vis)
                
                // The split-second it mathematically closes, finalize and clean up!
                string closePayload = finalizeTrade(settings, trade, z1, dX, mX, d1_message)
                alert(closePayload, alert.freq_once_per_bar)
                
                array.remove(sessionsArr, i)
                array.remove(visualsArr, i)
                0"""

new_else = """            else
                // The split-second it mathematically closes, finalize and clean up!
                string closePayload = finalizeTrade(settings, trade, z1, dX, mX, d1_message)

                // ✅ DELETES VISUALS INSTANTLY
                deleteTradeVisuals(vis)

                array.remove(sessionsArr, i)
                array.remove(visualsArr, i)
                0"""

if old_else in text:
    print("Fixed processTradeArray else branch")
    text = text.replace(old_else, new_else)

with open('/Users/vishant/Documents/Project/TV Indicator/TLCS_Live_Pivot_Alerts.pine', 'w') as f:
    f.write(text)

