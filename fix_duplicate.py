with open('/Users/vishant/Documents/Project/TV Indicator/TLCS_Live_Pivot_Alerts.pine', 'r') as f:
    text = f.read()

old = """                // ✅ DELETES VISUALS INSTANTLY
                deleteTradeVisuals(vis) 
                
                array.remove(sessionsArr, i)
                array.remove(visualsArr, i)
                0 
                
                array.remove(sessionsArr, i)
                array.remove(visualsArr, i)
                0"""

new = """                // ✅ DELETES VISUALS INSTANTLY
                deleteTradeVisuals(vis) 
                
                array.remove(sessionsArr, i)
                array.remove(visualsArr, i)
                0"""

if old in text:
    print("Found and replaced duplicated array.remove")
    text = text.replace(old, new)
else:
    print("Did not find duplicated array.remove")

with open('/Users/vishant/Documents/Project/TV Indicator/TLCS_Live_Pivot_Alerts.pine', 'w') as f:
    f.write(text)
