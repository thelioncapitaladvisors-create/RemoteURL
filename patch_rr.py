import re

with open('Tv-Alert-Mobile/src/app/page.tsx', 'r') as f:
    content = f.read()

old_code = """                                   const rrNum = meta.risk_reward ? Number(meta.risk_reward) : null;
                                   const rr = rrNum !== null ? `${rrNum.toFixed(2)}` : '--';"""

new_code = """                                   let rr = '--';
                                   if (o !== 'BREAKEVEN' && o !== 'CANCELLED') {
                                       let stopVal = s.stop != null ? Number(s.stop) : (meta.stop != null ? Number(meta.stop) : (meta.sl != null ? Number(meta.sl) : null));
                                       const entryVal = s.entry ? Number(s.entry) : null;
                                       if (entryVal && !stopVal) {
                                           const isLong = s.type?.toUpperCase().includes('LONG') || s.type?.toUpperCase().includes('BUY');
                                           const cleanSym = (s.symbol || '').toUpperCase().replace(/^NSE:|^TVC:|^NYMEX:|^MCX:/i, '').replace(/1!$/, '').trim();
                                           let defPct = 0.005;
                                           if (['CL1!', 'CL', 'CRUDEOIL', 'CRUDEOILM'].includes(cleanSym)) defPct = 0.005;
                                           else if (['GC1!', 'GC', 'GOLD', 'GOLDM', 'GOLDPETAL'].includes(cleanSym)) defPct = 0.003;
                                           else if (['SI1!', 'SI', 'SILVER', 'SILVERM', 'SILVERMIC'].includes(cleanSym)) defPct = 0.005;
                                           else if (['NG1!', 'NG', 'NATURALGAS', 'NATURALGASM'].includes(cleanSym)) defPct = 0.008;
                                           else if (cleanSym.startsWith('NSE:') || ['ADANIENT', 'RELIANCE', 'SBIN', 'NIFTY'].includes(cleanSym)) defPct = 0.0035;
                                           else if (cleanSym.endsWith('USDT') || cleanSym.endsWith('BTC')) defPct = 0.0075;
                                           else if (cleanSym.length === 6) defPct = 0.0025;
                                           stopVal = isLong ? entryVal * (1 - defPct) : entryVal * (1 + defPct);
                                       }
                                       if (entryVal && stopVal) {
                                           const riskAmt = Math.abs(entryVal - stopVal);
                                           if (riskAmt > 0 && s.exit_price != null && !isNaN(Number(s.exit_price))) {
                                               const isShort = s.type?.toUpperCase().includes('SHORT') || s.type?.toUpperCase().includes('SELL');
                                               const realizedRewardAmt = isShort ? (entryVal - Number(s.exit_price)) : (Number(s.exit_price) - entryVal);
                                               rr = `${(realizedRewardAmt / riskAmt).toFixed(2)}`;
                                           }
                                       }
                                   }"""

content = content.replace(old_code, new_code)

with open('Tv-Alert-Mobile/src/app/page.tsx', 'w') as f:
    f.write(content)
