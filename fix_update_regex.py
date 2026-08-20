import re

with open('/Users/vishant/Documents/Project/TV Indicator/TLCS_Live_Pivot_Alerts.pine', 'r') as f:
    text = f.read()

pattern = r"updateTradeVisuals\(Settings settings, TradeLogic trade, TradeVisuals visuals\) =>.*?label\.set_xy\(visuals\.entryMarkerLabel"

replacement = """updateTradeVisuals(Settings settings, TradeLogic trade, TradeVisuals visuals) =>
    bool isInvalidated = trade.isClosed and not trade.hasHitEntry

    // 1. PERMANENT DELETION — only EMA exits and never-filled limits
    if trade.emaExitTriggered or isInvalidated
        deleteTradeVisuals(visuals)

    // 2. DRAW FILLED TRADES ONLY
    if not (trade.emaExitTriggered or isInvalidated) and trade.hasHitEntry
        // ✅ Build the levels the split-second the limit fills
        if na(visuals.entryMarkerLine) and settings.showTPSL
            generateTradeVisuals(settings, trade, visuals)

        label.set_xy(visuals.entryMarkerLabel"""

if re.search(pattern, text, re.DOTALL):
    print("Found and replaced via regex")
    text = re.sub(pattern, replacement, text, flags=re.DOTALL)
    
with open('/Users/vishant/Documents/Project/TV Indicator/TLCS_Live_Pivot_Alerts.pine', 'w') as f:
    f.write(text)
