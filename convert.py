import re

with open('/Users/vishant/Documents/Project/TV Indicator/TLCS_Intraday_Dashboards.pine', 'r') as f:
    content = f.read()

# Replace the end of f_calc
old_return = """    // Return 20 booleans
    [bullAcc, bearDist, bullRej, bearRej, bullSrdSignal, bearSrdSignal, odBull, odBear, bullFade_final, bearFade_final, unifiedBullAbs, unifiedBearAbs, fnlSignal, fnhSignal, bullFailedBreakout, bearFailedBreakout, bullRetestAfterSrd, bearRetestAfterSrd, bullCont, bearCont]"""

new_return = """    // Return single integer encoded with all booleans to bypass memory limits
    int encoded = 0
    encoded += bullAcc ? 1 : 0
    encoded += bearDist ? 2 : 0
    encoded += bullRej ? 4 : 0
    encoded += bearRej ? 8 : 0
    encoded += bullSrdSignal ? 16 : 0
    encoded += bearSrdSignal ? 32 : 0
    encoded += odBull ? 64 : 0
    encoded += odBear ? 128 : 0
    encoded += bullFade_final ? 256 : 0
    encoded += bearFade_final ? 512 : 0
    encoded += unifiedBullAbs ? 1024 : 0
    encoded += unifiedBearAbs ? 2048 : 0
    encoded += fnlSignal ? 4096 : 0
    encoded += fnhSignal ? 8192 : 0
    encoded += bullFailedBreakout ? 16384 : 0
    encoded += bearFailedBreakout ? 32768 : 0
    encoded += bullRetestAfterSrd ? 65536 : 0
    encoded += bearRetestAfterSrd ? 131072 : 0
    encoded += bullCont ? 262144 : 0
    encoded += bearCont ? 524288 : 0
    encoded

f_decode(int val) =>
    int temp = val
    acB = (temp % 2) != 0; temp := math.floor(temp / 2)
    acS = (temp % 2) != 0; temp := math.floor(temp / 2)
    rB  = (temp % 2) != 0; temp := math.floor(temp / 2)
    rS  = (temp % 2) != 0; temp := math.floor(temp / 2)
    sB  = (temp % 2) != 0; temp := math.floor(temp / 2)
    sS  = (temp % 2) != 0; temp := math.floor(temp / 2)
    odB = (temp % 2) != 0; temp := math.floor(temp / 2)
    odS = (temp % 2) != 0; temp := math.floor(temp / 2)
    fdB = (temp % 2) != 0; temp := math.floor(temp / 2)
    fdS = (temp % 2) != 0; temp := math.floor(temp / 2)
    aB  = (temp % 2) != 0; temp := math.floor(temp / 2)
    aS  = (temp % 2) != 0; temp := math.floor(temp / 2)
    fB  = (temp % 2) != 0; temp := math.floor(temp / 2)
    fS  = (temp % 2) != 0; temp := math.floor(temp / 2)
    fbB = (temp % 2) != 0; temp := math.floor(temp / 2)
    fbS = (temp % 2) != 0; temp := math.floor(temp / 2)
    rtB = (temp % 2) != 0; temp := math.floor(temp / 2)
    rtS = (temp % 2) != 0; temp := math.floor(temp / 2)
    cB  = (temp % 2) != 0; temp := math.floor(temp / 2)
    cS  = (temp % 2) != 0; temp := math.floor(temp / 2)
    [acB, acS, rB, rS, sB, sS, odB, odS, fdB, fdS, aB, aS, fB, fS, fbB, fbS, rtB, rtS, cB, cS]"""

content = content.replace(old_return, new_return)

# Replace security calls
content = re.sub(r'(request\.security\([^,]+, timeframe\.period, f_calc\(\)\))', r'f_decode(\1)', content)

with open('/Users/vishant/Documents/Project/TV Indicator/TLCS_Intraday_Dashboards.pine', 'w') as f:
    f.write(content)
