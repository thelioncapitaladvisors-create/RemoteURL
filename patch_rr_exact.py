import re

with open('Tv-Alert-Mobile/src/app/page.tsx', 'r') as f:
    content = f.read()

old_code = """                                       if (entryVal && stopVal) {
                                           const riskAmt = Math.abs(entryVal - stopVal);
                                           if (riskAmt > 0 && s.exit_price != null && !isNaN(Number(s.exit_price))) {
                                               const isShort = s.type?.toUpperCase().includes('SHORT') || s.type?.toUpperCase().includes('SELL');
                                               const realizedRewardAmt = isShort ? (entryVal - Number(s.exit_price)) : (Number(s.exit_price) - entryVal);
                                               rr = `${(realizedRewardAmt / riskAmt).toFixed(2)}`;
                                           }
                                       }"""

new_code = """                                       if (entryVal && stopVal) {
                                           const riskAmt = Math.abs(entryVal - stopVal);
                                           if (riskAmt > 0 && exact !== 0) {
                                               const realizedRewardAmt = (Math.abs(exact) / 100) * entryVal;
                                               const sign = exact > 0 ? 1 : -1;
                                               rr = `${(sign * realizedRewardAmt / riskAmt).toFixed(2)}`;
                                           }
                                       }"""

content = content.replace(old_code, new_code)

with open('Tv-Alert-Mobile/src/app/page.tsx', 'w') as f:
    f.write(content)
