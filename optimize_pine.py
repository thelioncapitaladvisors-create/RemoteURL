import re

with open("/Users/vishant/Documents/Project/TV Indicator/TLCS_Intraday_Dashboards.pine", "r") as f:
    content = f.read()

# 1. Replace the return statement in f_calc()
old_return = "    [bullAcc, bearDist, bullRej, bearRej, bullSrdSignal, bearSrdSignal, odBull, odBear, bullFade_final, bearFade_final, unifiedBullAbs, unifiedBearAbs, fnlSignal, fnhSignal, bullFailedBreakout, bearFailedBreakout, bullRetestAfterSrd, bearRetestAfterSrd, bullCont, bearCont]"

new_return = """    int encoded = 0
    if bullAcc
        encoded += 1
    if bearDist
        encoded += 2
    if bullRej
        encoded += 4
    if bearRej
        encoded += 8
    if bullSrdSignal
        encoded += 16
    if bearSrdSignal
        encoded += 32
    if odBull
        encoded += 64
    if odBear
        encoded += 128
    if bullFade_final
        encoded += 256
    if bearFade_final
        encoded += 512
    if unifiedBullAbs
        encoded += 1024
    if unifiedBearAbs
        encoded += 2048
    if fnlSignal
        encoded += 4096
    if fnhSignal
        encoded += 8192
    if bullFailedBreakout
        encoded += 16384
    if bearFailedBreakout
        encoded += 32768
    if bullRetestAfterSrd
        encoded += 65536
    if bearRetestAfterSrd
        encoded += 131072
    if bullCont
        encoded += 262144
    if bearCont
        encoded += 524288
    encoded

f_decode(int val) =>
    int temp = val
    bool acB = (temp % 2) != 0
    temp := math.floor(temp / 2)
    bool acS = (temp % 2) != 0
    temp := math.floor(temp / 2)
    bool rB = (temp % 2) != 0
    temp := math.floor(temp / 2)
    bool rS = (temp % 2) != 0
    temp := math.floor(temp / 2)
    bool sB = (temp % 2) != 0
    temp := math.floor(temp / 2)
    bool sS = (temp % 2) != 0
    temp := math.floor(temp / 2)
    bool odB = (temp % 2) != 0
    temp := math.floor(temp / 2)
    bool odS = (temp % 2) != 0
    temp := math.floor(temp / 2)
    bool fdB = (temp % 2) != 0
    temp := math.floor(temp / 2)
    bool fdS = (temp % 2) != 0
    temp := math.floor(temp / 2)
    bool aB = (temp % 2) != 0
    temp := math.floor(temp / 2)
    bool aS = (temp % 2) != 0
    temp := math.floor(temp / 2)
    bool fB = (temp % 2) != 0
    temp := math.floor(temp / 2)
    bool fS = (temp % 2) != 0
    temp := math.floor(temp / 2)
    bool fbB = (temp % 2) != 0
    temp := math.floor(temp / 2)
    bool fbS = (temp % 2) != 0
    temp := math.floor(temp / 2)
    bool rtB = (temp % 2) != 0
    temp := math.floor(temp / 2)
    bool rtS = (temp % 2) != 0
    temp := math.floor(temp / 2)
    bool cB = (temp % 2) != 0
    temp := math.floor(temp / 2)
    bool cS = (temp % 2) != 0
    [acB, acS, rB, rS, sB, sS, odB, odS, fdB, fdS, aB, aS, fB, fS, fbB, fbS, rtB, rtS, cB, cS]"""

content = content.replace(old_return, new_return)

# 2. Wrap all request.security calls in f_decode()
content = re.sub(r'(=\s*)request\.security\(([^)]+)\)', r'\1f_decode(request.security(\2))', content)

with open("/Users/vishant/Documents/Project/TV Indicator/TLCS_Intraday_Dashboards.pine", "w") as f:
    f.write(content)
