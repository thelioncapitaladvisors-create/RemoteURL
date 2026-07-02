const body = {
    "secret":"675d6a2593",
    "symbol":"BTCUSDT",
    "exchange":"BINANCE",
    "action":"LONG",
    "entry":"60000",
    "timenow": "2024-07-01T07:19:24.000Z"
};
const providedTs = body.timenow || body.time || body.signal_ts || body.entry_signal_ts || body.entry_time;
console.log("providedTs:", providedTs);
let tsMs = Date.now();
const tsNum = Number(providedTs);
console.log("tsNum:", tsNum, "isNaN:", isNaN(tsNum), " > 1e12:", tsNum > 1e12);

if (!isNaN(tsNum) && tsNum > 1e12) {
    tsMs = tsNum;
} else if (typeof providedTs === 'string' && providedTs.includes('T')) {
    tsMs = new Date(providedTs).getTime();
}
console.log("tsMs:", tsMs);

const getMarketTz = (sym, exch) => {
    if (!sym) return 'America/New_York';
    const s = sym.toUpperCase();
    const e = (exch || '').toUpperCase();
    if (s.includes('NIFTY') || s.endsWith('.NS') || s.endsWith('.BO') || ['ITC', 'SBIN', 'RELIANCE'].includes(s)) return 'Asia/Kolkata';
    if (['GOLD', 'CRUDEOIL', 'CRUDEOIL1!', 'NATURALGAS1!', 'NATURALGAS', 'SILVER', 'SILVERM', 'GOLDM'].includes(s)) return 'Asia/Kolkata';
    if (e === 'NSE' || e === 'MCX' || e === 'BSE') return 'Asia/Kolkata';
    return 'America/New_York';
};

const tz = getMarketTz(body.symbol, body.exchange);
const formatter = new Intl.DateTimeFormat('en-US', { timeZone: tz, year: 'numeric', month: '2-digit', day: '2-digit' });

const getTzDateStr = (ms) => {
    const parts = formatter.formatToParts(new Date(ms));
    const yr = parts.find(p=>p.type==='year').value;
    const mo = parts.find(p=>p.type==='month').value;
    const da = parts.find(p=>p.type==='day').value;
    return `${yr}-${mo}-${da}`;
};

const signalDateStr = getTzDateStr(tsMs);
const todayDateStr = getTzDateStr(Date.now());
console.log("signalDateStr:", signalDateStr, "todayDateStr:", todayDateStr);
if (signalDateStr !== todayDateStr) {
    console.log("REJECTED");
} else {
    console.log("ACCEPTED");
}
