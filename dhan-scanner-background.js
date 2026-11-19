/**
 * TLCS Autonomous 15-Minute DhanHQ Black Box Scanner & Limit Execution Engine
 * Background Function: TLCS_Website_Deploy/netlify/functions/dhan-scanner-background.js
 * 
 * Runs as an asynchronous Netlify Background Function (up to 15-minute runtime budget).
 * Evaluates both NSE Top 100 Equities and MCX Commodities:
 * - NSE Equities: 09:15 AM to 03:30 PM IST (Cutoff 14:00 IST)
 * - MCX Commodities: 09:00 AM to 11:30 PM IST (Cutoff 23:00 IST)
 * 
 * Features:
 * 1. Autonomous Limit Order Touch-Point Fill Tracking:
 *    - Long Limit: low <= trade.entry -> transitions to '⚡ TRADE ACTIVE' (TradeFill)
 *    - Short Limit: high >= trade.entry -> transitions to '⚡ TRADE ACTIVE' (TradeFill)
 *    - Ab-Initio Invalidation: if price hits SL before entry -> 'CANCELLED'
 * 2. Active Trade Progress: dynamically evaluates TP1-TP4 targets and trailing SL.
 * 3. Autonomous Strategy Detections: Camarilla H4/L4 gating, CPR, EMAs, ATR, Day Types.
 * 4. Dual-Market EOD Close Sweeps: NSE at 15:30 IST, MCX at 23:30 IST.
 */

const { createClient } = require('@supabase/supabase-js');
const https = require('https');
const ws = require('ws');
const symbolsMap = require('./dhan-scanner-symbols.json');

// Initialize Supabase
const SUPABASE_URL = process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://dwepduvhzuhzeehbeaaz.supabase.co';
const SUPABASE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_SERVICE_KEY || process.env.SUPABASE_KEY;
const supabase = createClient(SUPABASE_URL, SUPABASE_KEY || 'placeholder', {
    auth: { persistSession: false },
    realtime: { transport: ws }
});

const { getValidDhanToken, DHAN_CLIENT_ID } = require('./dhan-auth.js');

// In-memory cache for daily levels (prev high, low, close) to minimize redundant API calls
const dailyLevelsCache = new Map();

// Helper: Get Current IST Date and Time
function getISTDate() {
    const now = new Date();
    return new Date(now.getTime() + (5.5 * 60 * 60 * 1000));
}

function getISTDateString() {
    const ist = getISTDate();
    const y = ist.getUTCFullYear();
    const m = String(ist.getUTCMonth() + 1).padStart(2, '0');
    const d = String(ist.getUTCDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
}

function getISTMinutes() {
    const ist = getISTDate();
    return ist.getUTCHours() * 60 + ist.getUTCMinutes();
}

function isNSEOpen() {
    const mins = getISTMinutes();
    return mins >= 555 && mins < 930; // 09:15 to 15:30 IST
}

function isMCXOpen() {
    const mins = getISTMinutes();
    return mins >= 540 && mins < 1410; // 09:00 to 23:30 IST
}

function isNSEEntryAllowed() {
    const mins = getISTMinutes();
    return mins >= 555 && mins < 840; // 09:15 to 14:00 IST (2:00 PM cutoff)
}

function isMCXEntryAllowed() {
    const mins = getISTMinutes();
    return mins >= 540 && mins < 1320; // 09:00 to 22:00 IST (10:00 PM cutoff)
}

// HTTP request helper to DhanHQ API (with automatic TOTP token refresh and 401 retry)
async function dhanRequest(endpoint, payload, isRetry = false) {
    const accessToken = await getValidDhanToken();
    const clientId = DHAN_CLIENT_ID || process.env.DHAN_CLIENT_ID || '';

    return new Promise((resolve) => {
        if (!clientId || !accessToken) {
            return resolve({ statusCode: 401, error: 'No Dhan credentials available' });
        }

        const dataStr = JSON.stringify(payload);
        const options = {
            hostname: 'api.dhan.co',
            port: 443,
            path: endpoint,
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'client-id': clientId,
                'access-token': accessToken,
                'Content-Length': Buffer.byteLength(dataStr)
            },
            timeout: 6000
        };

        const req = https.request(options, (res) => {
            let body = '';
            res.on('data', (chunk) => body += chunk);
            res.on('end', async () => {
                let parsed = null;
                try { parsed = JSON.parse(body || '{}'); } catch (e) {}

                const isAuthError = res.statusCode === 401 || res.statusCode === 400 || parsed?.errorCode === 'DH-906' || parsed?.errorType === 'AuthenticationException';
                if (isAuthError && !isRetry) {
                    console.warn('[DhanScanner] Auth error received from DhanHQ. Auto-refreshing token via TOTP...');
                    await getValidDhanToken(true);
                    const retried = await dhanRequest(endpoint, payload, true);
                    return resolve(retried);
                }

                resolve({ statusCode: res.statusCode, data: parsed });
            });
        });

        req.on('error', (err) => resolve({ statusCode: 500, error: err.message }));
        req.on('timeout', () => {
            req.destroy();
            resolve({ statusCode: 408, error: 'Request timeout' });
        });

        req.write(dataStr);
        req.end();
    });
}

// Fetch historical daily levels for a stock or commodity derived deterministically from live candles
async function fetchDailyLevels(symbol, info, existingCandles = null) {
    const todayStr = getISTDateString();
    const cacheKey = `${symbol}_${todayStr}`;
    if (dailyLevelsCache.has(cacheKey)) {
        return dailyLevelsCache.get(cacheKey);
    }

    const candles = existingCandles || await fetchIntradayCandles(symbol, info);
    if (candles && candles.length > 0) {
        const daysMap = new Map();
        for (const c of candles) {
            const istDate = new Date(c.timestamp * 1000 + 5.5 * 3600 * 1000).toISOString().split('T')[0];
            if (!daysMap.has(istDate)) daysMap.set(istDate, []);
            daysMap.get(istDate).push(c);
        }

        const allDates = Array.from(daysMap.keys()).sort();
        const closedDates = allDates.filter(dt => dt < todayStr);
        const datesToUse = closedDates.length > 0 ? closedDates : allDates;

        if (datesToUse.length > 0) {
            const yDate = datesToUse[datesToUse.length - 1];
            const yBars = daysMap.get(yDate);
            const yHigh = Math.max(...yBars.map(c => c.high));
            const yLow = Math.min(...yBars.map(c => c.low));
            const yClose = yBars[yBars.length - 1].close;

            const prevDate = datesToUse.length >= 2 ? datesToUse[datesToUse.length - 2] : yDate;
            const pBars = daysMap.get(prevDate);
            const pHigh = Math.max(...pBars.map(c => c.high));
            const pLow = Math.min(...pBars.map(c => c.low));
            const pClose = pBars[pBars.length - 1].close;

            const dailyCprWidths = [];
            for (let i = 0; i < datesToUse.length; i++) {
                const b = daysMap.get(datesToUse[i]);
                const dh = Math.max(...b.map(x => x.high));
                const dl = Math.min(...b.map(x => x.low));
                const dc = b[b.length - 1].close;
                dailyCprWidths.push(Math.abs((2 * dc - dh - dl) / 3.0));
            }
            const last14 = dailyCprWidths.slice(-14);
            const cprWidthAvg14 = last14.length > 0 ? (last14.reduce((a, b) => a + b, 0) / last14.length) : 0;

            const levels = {
                high: yHigh,
                low: yLow,
                close: yClose,
                prev_high: pHigh,
                prev_low: pLow,
                prev_close: pClose,
                cpr_width_avg14: cprWidthAvg14
            };
            dailyLevelsCache.set(cacheKey, levels);
            return levels;
        }
    }

    return null;
}

// Fetch 15-minute intraday candles from live DhanHQ Charts API
async function fetchIntradayCandles(symbol, info) {
    const todayStr = getISTDateString();
    const pastD = new Date();
    pastD.setDate(pastD.getDate() - 4); // DhanHQ allows up to 5 days of 15m intraday data
    const fromDateStr = `${pastD.getFullYear()}-${String(pastD.getMonth() + 1).padStart(2, '0')}-${String(pastD.getDate()).padStart(2, '0')}`;
    const secId = info.security_id;
    const isMCX = info.exchange_segment === 5 || info.instrument === 'COMMODITY' || info.instrument === 'FUTCOM';
    const exchSegment = isMCX ? 'MCX_COMM' : 'NSE_EQ';
    const instrument = isMCX ? 'FUTCOM' : 'EQUITY';

    const token = await getValidDhanToken();
    if (DHAN_CLIENT_ID && token) {
        const res = await dhanRequest('/v2/charts/intraday', {
            securityId: String(secId),
            exchangeSegment: exchSegment,
            instrument: instrument,
            interval: 15,
            fromDate: fromDateStr,
            toDate: todayStr
        });

        // DhanHQ v2 returns data directly in res.data without nested .data property
        const d = (res.data && res.data.data && res.data.data.open) ? res.data.data : (res.data && res.data.open ? res.data : null);
        if (res.statusCode === 200 && d && Array.isArray(d.open) && d.open.length > 0) {
            const opens = d.open;
            const highs = d.high;
            const lows = d.low;
            const closes = d.close;
            const vols = d.volume || [];
            const times = d.timestamp || [];

            const candles = [];
            for (let i = 0; i < opens.length; i++) {
                candles.push({
                    open: parseFloat(opens[i]),
                    high: parseFloat(highs[i]),
                    low: parseFloat(lows[i]),
                    close: parseFloat(closes[i]),
                    volume: vols[i] ? parseFloat(vols[i]) : 0,
                    timestamp: times[i] ? parseFloat(times[i]) : Math.floor(Date.now() / 1000)
                });
            }
            return candles;
        } else if (res.statusCode === 429) {
            console.warn(`[DhanScanner] ${symbol} rate limited (429). Retrying after 1000ms...`);
            await new Promise(r => setTimeout(r, 1000));
            const retryRes = await dhanRequest('/v2/charts/intraday', {
                securityId: String(secId),
                exchangeSegment: exchSegment,
                instrument: instrument,
                interval: 15,
                fromDate: fromDateStr,
                toDate: todayStr
            });
            const rd = (retryRes.data && retryRes.data.data && retryRes.data.data.open) ? retryRes.data.data : (retryRes.data && retryRes.data.open ? retryRes.data : null);
            if (retryRes.statusCode === 200 && rd && Array.isArray(rd.open) && rd.open.length > 0) {
                const opens = rd.open;
                const highs = rd.high;
                const lows = rd.low;
                const closes = rd.close;
                const vols = rd.volume || [];
                const times = rd.timestamp || [];

                const candles = [];
                for (let i = 0; i < opens.length; i++) {
                    candles.push({
                        open: parseFloat(opens[i]),
                        high: parseFloat(highs[i]),
                        low: parseFloat(lows[i]),
                        close: parseFloat(closes[i]),
                        volume: vols[i] ? parseFloat(vols[i]) : 0,
                        timestamp: times[i] ? parseFloat(times[i]) : Math.floor(Date.now() / 1000)
                    });
                }
                return candles;
            } else {
                console.warn(`[DhanScanner] ${symbol} retry after 429 failed: status=${retryRes.statusCode}`);
            }
        } else {
            console.warn(`[DhanScanner] ${symbol} intraday fetch failed or returned empty: status=${res.statusCode}`);
        }
    }

    return null;
}

// Fetch latest market quote / LTP from DhanHQ Marketfeed API (available without Charts Data API subscription)
async function fetchDhanLtpOrQuote(symbol, info) {
    if (!info || !info.security_id) return null;
    const secId = String(info.security_id);
    const isMCX = info.exchange_segment === 5 || info.instrument === 'COMMODITY' || info.instrument === 'FUTCOM';
    const exchSegment = isMCX ? 'MCX_COMM' : 'NSE_EQ';

    const token = await getValidDhanToken();
    if (!DHAN_CLIENT_ID || !token) return null;

    try {
        const payload = { [exchSegment]: [Number(secId)] };
        // 1. Try /v2/marketfeed/quote for full OHLC + LTP
        let res = await dhanRequest('/v2/marketfeed/quote', payload);
        let d = res && res.data ? res.data : null;
        let scripData = null;
        if (d && d.data && d.data[exchSegment] && d.data[exchSegment][secId]) {
            scripData = d.data[exchSegment][secId];
        } else if (d && d[exchSegment] && d[exchSegment][secId]) {
            scripData = d[exchSegment][secId];
        }

        if (scripData) {
            const ltp = parseFloat(scripData.last_price || scripData.ltp || 0);
            const ohlc = scripData.ohlc || {};
            const high = parseFloat(ohlc.high || ltp);
            const low = parseFloat(ohlc.low || ltp);
            const open = parseFloat(ohlc.open || ltp);
            const close = parseFloat(ohlc.close || ltp);
            if (ltp > 0) {
                return {
                    open,
                    high: Math.max(high, ltp),
                    low: Math.min(low > 0 ? low : ltp, ltp),
                    close: ltp,
                    timestamp: Math.floor(Date.now() / 1000)
                };
            }
        }

        // 2. Fallback to /v2/marketfeed/ltp
        res = await dhanRequest('/v2/marketfeed/ltp', payload);
        d = res && res.data ? res.data : null;
        let ltpVal = 0;
        if (d && d.data && d.data[exchSegment] && d.data[exchSegment][secId]) {
            ltpVal = parseFloat(d.data[exchSegment][secId].last_price || 0);
        } else if (d && d[exchSegment] && d[exchSegment][secId]) {
            ltpVal = parseFloat(d[exchSegment][secId].last_price || 0);
        }

        if (ltpVal > 0) {
            return {
                open: ltpVal,
                high: ltpVal,
                low: ltpVal,
                close: ltpVal,
                timestamp: Math.floor(Date.now() / 1000)
            };
        }
    } catch (e) {
        console.warn(`[DhanScanner] fetchDhanLtpOrQuote failed for ${symbol}: ${e.message}`);
    }

    return null;
}

// ── Mathematical Pivots & Indicators ──────────────────────────────────────────

function computeCamarillaLevels(high, low, close) {
    const range = high - low;
    return {
        H5: (high / low) * close,
        H4: close + range * 0.55,
        H3: close + range * 0.275,
        H2: close + range * (1.1 / 6),
        H1: close + range * (1.1 / 12),
        L1: close - range * (1.1 / 12),
        L2: close - range * (1.1 / 6),
        L3: close - range * 0.275,
        L4: close - range * 0.55,
        L5: 2 * close - ((high / low) * close),
        range: range
    };
}

function computeCPR(high, low, close, cprWidthAvg14 = null) {
    const pivot = (high + low + close) / 3;
    const bc = (high + low) / 2;
    const tc = 2 * pivot - bc;
    const actualTC = Math.max(tc, bc);
    const actualBC = Math.min(tc, bc);
    const width = Math.abs(actualTC - actualBC);
    const range = high - low;
    const isNarrow = (cprWidthAvg14 && cprWidthAvg14 > 0)
        ? (width <= 0.50 * cprWidthAvg14)
        : ((range > 0 && (width / range) < 0.05) || (pivot > 0 && width < 0.002 * pivot));
    return { pivot, tc: actualTC, bc: actualBC, width, isNarrow, DP: pivot, DTc: actualTC, DBc: actualBC };
}

function computeDualCPR(d1, d2, cprWidthAvg14 = null) {
    const Pi = (d1.high + d1.low + d1.close) / 3.0;
    const Bcy = (d1.high + d1.low) / 2.0;
    const Tcy = Pi - Bcy + Pi;
    const DTc = Math.max(Tcy, Bcy);
    const DBc = Math.min(Tcy, Bcy);
    const DP = Pi;

    const d2_h = (d2 && d2.high) ? d2.high : d1.prev_high || d1.high;
    const d2_l = (d2 && d2.low) ? d2.low : d1.prev_low || d1.low;
    const d2_c = (d2 && d2.close) ? d2.close : d1.prev_close || d1.close;

    const YP = (d2_h + d2_l + d2_c) / 3.0;
    const BcY = (d2_h + d2_l) / 2.0;
    const TcY = YP - BcY + YP;
    const YTc = Math.max(TcY, BcY);
    const YBc = Math.min(TcY, BcY);

    const prevDayRange = Math.max(d1.high - d1.low, 0.05);
    const cprWidth = Math.abs(DTc - DBc);
    const ncprPct = (cprWidth / prevDayRange) * 100;
    const avg14 = cprWidthAvg14 || d1.cpr_width_avg14;
    const isNarrow = (avg14 && avg14 > 0) ? (cprWidth <= 0.50 * avg14) : (ncprPct < 5.0);

    return {
        DP, DTc, DBc,
        YP, YTc, YBc,
        width: cprWidth,
        isNarrow,
        ncprPct,
        cprWidthAvg14: avg14 || 0,
        pivot: DP,
        tc: DTc,
        bc: DBc
    };
}

function computeTPOValueArea(prevSessionCandles, d1) {
    if (prevSessionCandles && prevSessionCandles.length >= 8) {
        let sessionHigh = -Infinity;
        let sessionLow = Infinity;
        for (const c of prevSessionCandles) {
            if (c.high > sessionHigh) sessionHigh = c.high;
            if (c.low < sessionLow) sessionLow = c.low;
        }
        const sessionRange = sessionHigh - sessionLow;
        if (sessionRange > 0) {
            const sectionRange = sessionRange / 20.0;
            const tpoArray = new Array(21).fill(0);

            for (let i = 0; i <= 20; i++) {
                const upper = sessionHigh - sectionRange * i;
                const lower = sessionHigh - sectionRange * (i + 1);
                let freq = 0;
                for (const c of prevSessionCandles) {
                    if (c.close >= lower && c.close < upper) {
                        freq++;
                    }
                }
                tpoArray[i] = freq;
            }

            let tpoSum = 0;
            let pocPosition = 0;
            let pocValue = -1;
            for (let i = 0; i <= 20; i++) {
                tpoSum += tpoArray[i];
                if (tpoArray[i] >= pocValue) {
                    pocPosition = i;
                    pocValue = tpoArray[i];
                }
            }

            const targetSum = tpoSum * 0.68;
            let vahPos = pocPosition;
            let valPos = pocPosition;
            let currentSum = pocValue;

            for (let i = 0; i <= 20; i++) {
                if (currentSum < targetSum) {
                    vahPos = Math.max(0, vahPos - 1);
                    currentSum += tpoArray[Math.round(vahPos)];
                }
                if (currentSum < targetSum) {
                    valPos = Math.min(20, valPos + 1);
                    currentSum += tpoArray[Math.round(valPos)];
                }
            }

            const VAH = sessionHigh - sectionRange * vahPos;
            const VAL = sessionHigh - sectionRange * (valPos + 1);
            return { VAH, VAL, POC: sessionHigh - sectionRange * pocPosition };
        }
    }

    const range = d1.high - d1.low;
    const pivot = (d1.high + d1.low + d1.close) / 3.0;
    return {
        VAH: pivot + range * 0.25,
        VAL: pivot - range * 0.25,
        POC: pivot
    };
}

function computeMarketProfileAndBiases(todayOpen, lastClose, d1, cpr, va, cam) {
    const OO_ = todayOpen;
    const close = lastClose;
    const dDH_ = d1.high;
    const dDL_ = d1.low;
    const CC = d1.close;
    const { DTc, DBc, DP, YTc, YBc, YP } = cpr;
    const { VAH, VAL } = va;
    const { H4, L4, H3, L3 } = cam;

    // Market Profile Range States (Lines 767-769)
    const INRANGEINVALUE = (OO_ > dDL_ && OO_ < dDH_ && OO_ > VAL && OO_ < VAH);
    const INRANGEOUTOFVALUE = (OO_ > dDL_ && OO_ < dDH_ && (OO_ < VAL || OO_ > VAH));
    const OUTOFRANGEVALUE = ((OO_ < dDL_ && OO_ < VAL) || (OO_ > dDH_ && OO_ > VAH));

    // Opening Bias (Lines 776-786)
    const BULLISH = (DTc > YTc && DBc > YTc);
    const BEARISH = (DTc < YBc && DBc < YBc);
    const MODERATELYBULLISH = (DTc > YTc && DBc > YBc);
    const MODERATELYBEARISH = (DTc < YTc && DBc < YBc);
    const INSIDE = (DTc < YTc && DBc > YBc);
    const OUTSIDE = (DTc > YTc && DBc < YBc);
    const UNCHANGED = (DP === YP && DBc === YBc && DTc === YTc);

    const BREAKOUTDAY = (INSIDE || UNCHANGED);
    const OTHERDAYS = (OUTSIDE || BREAKOUTDAY);
    const ANYDAY = (BULLISH || MODERATELYBULLISH || BEARISH || MODERATELYBEARISH || INSIDE || OUTSIDE || UNCHANGED);

    const CONFIRMEDBULLISH = ((BULLISH || MODERATELYBULLISH || OTHERDAYS) && OO_ > DBc);
    const CONFIRMEDBEARISH = ((BEARISH || MODERATELYBEARISH || OTHERDAYS) && OO_ < DTc);
    const REJECTEDBULLISH = ((BULLISH || MODERATELYBULLISH || OTHERDAYS) && OO_ < DBc);
    const REJECTEDBEARISH = ((BEARISH || MODERATELYBEARISH || OTHERDAYS) && OO_ > DTc);

    // Institutional Bias (c1) (Line 802)
    let c1 = "WATCH";
    if (ANYDAY && close < DTc && close > DBc) {
        c1 = "WATCH";
    } else if (CONFIRMEDBULLISH && close > DTc) {
        c1 = "CONFIRMED BULLISH";
    } else if (CONFIRMEDBULLISH && close < DBc) {
        c1 = "REJECTION";
    } else if (CONFIRMEDBEARISH && close < DBc) {
        c1 = "CONFIRMED BEARISH";
    } else if (CONFIRMEDBEARISH && close > DTc) {
        c1 = "REJECTION";
    } else if (REJECTEDBULLISH && close < DBc) {
        c1 = "REJECTED BULLISH";
    } else if (REJECTEDBEARISH && close > DTc) {
        c1 = "REJECTED BEARISH";
    } else if (OUTSIDE) {
        c1 = "SIDEWAYS";
    } else if (UNCHANGED) {
        c1 = "SIDEWAYS/ BREAKOUT";
    } else if ((ANYDAY && (OO_ > H4 || OO_ < L4)) || INSIDE) {
        c1 = "BREAKOUT";
    }

    // Opening Bias Display (dX) (Line 808)
    let dX = "IN RANGE IN VALUE";
    if (INRANGEINVALUE) {
        dX = "IN RANGE IN VALUE";
    } else if (INRANGEOUTOFVALUE) {
        dX = "IN RANGE OUT OF VALUE";
    } else if (OUTOFRANGEVALUE) {
        dX = "OUT OF RANGE OUT OF VALUE";
    } else if (BULLISH) {
        dX = "BULLISH";
    } else if (BEARISH) {
        dX = "BEARISH";
    }

    // Day Type (mX) (Line 811)
    let mX = "TYPICAL DAY, TRADING RANGE, SIDEWAYS";
    if (INRANGEINVALUE && (close > dDL_ && close < dDH_ && close > VAL && close < VAH)) {
        mX = "TYPICAL DAY, TRADING RANGE, SIDEWAYS";
    } else if ((INRANGEINVALUE && ((close > dDH_ && close > VAH) || (close < dDL_ && close < VAL))) ||
               ((OO_ < dDL_ && OO_ < VAL && OO_ < DBc) || (OO_ > dDH_ && OO_ > VAH && OO_ > DTc))) {
        mX = "BIG MOVE";
    } else if (INRANGEOUTOFVALUE && (close < dDH_ && close > dDL_)) {
        mX = "TYPICAL DAY, TRADING RANGE, SIDEWAYS";
    } else if (INRANGEOUTOFVALUE && (close > dDH_ || close < dDL_)) {
        mX = "TREND DAY, DOUBLE DISTRIBUTION TREND, EXPANDED TYPICAL";
    } else if (OUTOFRANGEVALUE && (close < dDL_ || close > dDH_)) {
        mX = "TREND DAY, DOUBLE DISTRIBUTION TREND";
    } else if (OUTOFRANGEVALUE && (close > dDL_ && close < dDH_)) {
        mX = "TYPICAL DAY, EXPANDED TYPICAL DAY, TRADING RANGE";
    }

    // Webhook Zone (z1) (Line 3114)
    let z1 = "WAITING";
    const bullBiasZone = (BULLISH || MODERATELYBULLISH || REJECTEDBEARISH || BEARISH || MODERATELYBEARISH || REJECTEDBULLISH);
    if ((bullBiasZone && close > H3) || (ANYDAY && close > DBc && close > DTc)) {
        z1 = "LONG ZONE";
    } else if ((bullBiasZone && close < L3) || (ANYDAY && close < DTc && close < DBc)) {
        z1 = "SHORT ZONE";
    } else if (ANYDAY && close > DBc && close < DTc) {
        z1 = "WAIT FOR SIGNAL";
    }

    // Rejection Day (Lines 792 / 3050 / 3129)
    const isRejectionDay = (CONFIRMEDBULLISH && close < DBc) ||
                           (CONFIRMEDBEARISH && close > DTc) ||
                           (REJECTEDBULLISH && close < DBc) ||
                           (REJECTEDBULLISH && close > DTc) ||
                           (REJECTEDBEARISH && close > DTc) ||
                           (REJECTEDBEARISH && close < DBc);

    // Sideways Day Filter (Lines 3101-3108)
    const isSidewaysDay = (mX === "INRANGEINVALUE") ||
                          (mX === "TYPICAL DAY, TRADING RANGE, SIDEWAYS") ||
                          mX.includes("TRADING RANGE") ||
                          mX.includes("SIDEWAYS") ||
                          mX.includes("TYPICAL DAY") ||
                          (dX === "IN RANGE IN VALUE");

    const dayAllowed = !isSidewaysDay || isRejectionDay;

    return {
        OO_,
        INRANGEINVALUE,
        INRANGEOUTOFVALUE,
        OUTOFRANGEVALUE,
        BULLISH,
        BEARISH,
        MODERATELYBULLISH,
        MODERATELYBEARISH,
        INSIDE,
        OUTSIDE,
        UNCHANGED,
        CONFIRMEDBULLISH,
        CONFIRMEDBEARISH,
        REJECTEDBULLISH,
        REJECTEDBEARISH,
        c1,
        dX,
        mX,
        z1,
        isSidewaysDay,
        isRejectionDay,
        dayAllowed
    };
}

function computeATR(candles, period = 14) {
    if (!candles || candles.length === 0) return 5.0;
    const trs = [];
    for (let i = 0; i < candles.length; i++) {
        if (i === 0) {
            trs.push(candles[i].high - candles[i].low);
        } else {
            const h = candles[i].high;
            const l = candles[i].low;
            const prevC = candles[i - 1].close;
            trs.push(Math.max(h - l, Math.abs(h - prevC), Math.abs(l - prevC)));
        }
    }
    const len = Math.min(trs.length, period);
    const slice = trs.slice(trs.length - len);
    const sum = slice.reduce((acc, v) => acc + v, 0);
    return Math.max(0.5, sum / len);
}

function computeEMA(values, period) {
    if (!values || values.length === 0) return 0;
    const k = 2 / (period + 1);
    let ema = values[0];
    for (let i = 1; i < values.length; i++) {
        ema = values[i] * k + ema * (1 - k);
    }
    return ema;
}

function computeEMASeries(values, period) {
    if (!values || values.length === 0) return [];
    const k = 2 / (period + 1);
    const res = [values[0]];
    for (let i = 1; i < values.length; i++) {
        res.push(values[i] * k + res[i - 1] * (1 - k));
    }
    return res;
}

function computeDMI(candles, len = 14) {
    if (!candles || candles.length < 2) return { plus: 50, minus: 50 };
    const plusDMs = [];
    const minusDMs = [];
    const trs = [];

    for (let i = 1; i < candles.length; i++) {
        const up = candles[i].high - candles[i - 1].high;
        const down = candles[i - 1].low - candles[i].low;
        plusDMs.push((up > down && up > 0) ? up : 0);
        minusDMs.push((down > up && down > 0) ? down : 0);

        const h = candles[i].high;
        const l = candles[i].low;
        const prevC = candles[i - 1].close;
        trs.push(Math.max(h - l, Math.abs(h - prevC), Math.abs(l - prevC)));
    }

    const rma = (vals, period) => {
        if (!vals.length) return 0;
        let val = vals[0];
        for (let i = 1; i < vals.length; i++) {
            val = (val * (period - 1) + vals[i]) / period;
        }
        return val;
    };

    const trur = rma(trs, len);
    if (trur <= 0) return { plus: 50, minus: 50 };
    const plus = (100 * rma(plusDMs, len)) / trur;
    const minus = (100 * rma(minusDMs, len)) / trur;
    return { plus, minus };
}

function computeOscillatorTrend(candles) {
    if (!candles || candles.length === 0) return { m0: 0, m10: 0 };
    const outs = [];
    const lookback = Math.min(92, candles.length);
    for (let i = 0; i < candles.length; i++) {
        const start = Math.max(0, i - lookback + 1);
        let upper = -Infinity;
        let lower = Infinity;
        for (let j = start; j <= i; j++) {
            if (candles[j].high > upper) upper = candles[j].high;
            if (candles[j].low < lower) lower = candles[j].low;
        }
        const denom = (upper - lower) === 0 ? 1 : (upper - lower);
        const out = 100 * (candles[i].close - upper) / denom;
        outs.push(out);
    }

    const m0Series = computeEMASeries(outs, 21);
    const m0 = m0Series[m0Series.length - 1];

    const smaLen = Math.min(96, outs.length);
    const m10Slice = outs.slice(-smaLen);
    const m10 = m10Slice.reduce((a, b) => a + b, 0) / smaLen;

    return { m0, m10 };
}

function computePivotPDEMASlope(candles) {
    if (!candles || candles.length < 2) return { rising: false, falling: false };
    const fPivots = candles.map(c => (c.high + c.low + c.close) / 3);
    const ema1 = computeEMASeries(fPivots, 13);
    const ema2 = computeEMASeries(ema1, 13);
    const pdemas = ema1.map((v, idx) => v * 2 - ema2[idx]);
    const fPivotPDEMAS = computeEMASeries(pdemas, 13);

    const curr = fPivotPDEMAS[fPivotPDEMAS.length - 1];
    const prev = fPivotPDEMAS[fPivotPDEMAS.length - 2];
    return {
        rising: curr > prev,
        falling: curr < prev,
        curr,
        prev
    };
}

function computePivotPoints(candles, leftLen = 10) {
    if (!candles || candles.length <= leftLen) return { highLeftEmpty: false, lowLeftEmpty: false };
    const lastBar = candles[candles.length - 1];
    let isHigh = true;
    let isLow = true;
    for (let i = candles.length - 2; i >= Math.max(0, candles.length - 1 - leftLen); i--) {
        if (candles[i].high > lastBar.high) isHigh = false;
        if (candles[i].low < lastBar.low) isLow = false;
    }
    return { highLeftEmpty: isHigh, lowLeftEmpty: isLow };
}

function computePivotPDEMAs(candles) {
    if (!candles || candles.length === 0) return { fPivotPDEMAF: 0, fPivotPDEMAS: 0 };
    const fPivots = candles.map(c => (c.high + c.low + c.close) / 3.0);
    
    // Fast 5
    const emaF1 = computeEMASeries(fPivots, 5);
    const emaF2 = computeEMASeries(emaF1, 5);
    const pdemaf = emaF1.map((v, i) => v * 2 - emaF2[i]);
    const fPivotPDEMAFSeries = computeEMASeries(pdemaf, 5);
    const fPivotPDEMAF = fPivotPDEMAFSeries[fPivotPDEMAFSeries.length - 1];

    // Slow 13
    const emaS1 = computeEMASeries(fPivots, 13);
    const emaS2 = computeEMASeries(emaS1, 13);
    const pdemas = emaS1.map((v, i) => v * 2 - emaS2[i]);
    const fPivotPDEMASSeries = computeEMASeries(pdemas, 13);
    const fPivotPDEMAS = fPivotPDEMASSeries[fPivotPDEMASSeries.length - 1];

    return { fPivotPDEMAF, fPivotPDEMAS };
}

function computeOscillatorSeries(candles) {
    if (!candles || candles.length === 0) return { outs: [], m0: 0, m10: 0 };
    const outs = [];
    const lookback = Math.min(92, candles.length);
    for (let i = 0; i < candles.length; i++) {
        const start = Math.max(0, i - lookback + 1);
        let upper = -Infinity;
        let lower = Infinity;
        for (let j = start; j <= i; j++) {
            if (candles[j].high > upper) upper = candles[j].high;
            if (candles[j].low < lower) lower = candles[j].low;
        }
        const denom = (upper - lower) === 0 ? 1 : (upper - lower);
        const out = 100 * (candles[i].close - upper) / denom;
        outs.push(out);
    }
    const m0Series = computeEMASeries(outs, 21);
    const m0 = m0Series[m0Series.length - 1];

    const smaLen = Math.min(96, outs.length);
    const m10Slice = outs.slice(-smaLen);
    const m10 = m10Slice.reduce((a, b) => a + b, 0) / smaLen;

    return { outs, m0, m10 };
}

function isValidBounceUp(srLevel, bar) {
    if (srLevel == null || isNaN(srLevel)) return false;
    return bar.low <= srLevel && bar.open >= srLevel && bar.high > srLevel && bar.close > srLevel && bar.close > bar.open;
}

function isValidBounceDown(srLevel, bar) {
    if (srLevel == null || isNaN(srLevel)) return false;
    return bar.high >= srLevel && bar.open <= srLevel && bar.low < srLevel && bar.close < srLevel && bar.close < bar.open;
}

function extractRecentPivots(candles, lookbackLen = 10, maxPivots = 15) {
    const supports = [];
    const resistances = [];
    if (!candles || candles.length <= lookbackLen * 2) return { supports, resistances };

    for (let i = candles.length - 2; i >= lookbackLen; i--) {
        const bar = candles[i];
        let isHigh = true;
        let isLow = true;
        for (let j = 1; j <= lookbackLen; j++) {
            if (candles[i - j].high >= bar.high || (i + j < candles.length && candles[i + j].high >= bar.high)) {
                isHigh = false;
            }
            if (candles[i - j].low <= bar.low || (i + j < candles.length && candles[i + j].low <= bar.low)) {
                isLow = false;
            }
        }
        if (isHigh && resistances.length < maxPivots) resistances.push(bar.high);
        if (isLow && supports.length < maxPivots) supports.push(bar.low);
        if (resistances.length >= maxPivots && supports.length >= maxPivots) break;
    }
    return { supports, resistances };
}

function checkDivergences(candles, cpr, lookbackBars = 6, plus = 0, minus = 0) {
    if (!candles || candles.length < 15) {
        return { regBullDiv: false, regBearDiv: false, hiddenBullishConfirmed: false, hiddenBearishConfirmed: false };
    }

    const { outs } = computeOscillatorSeries(candles);
    const n = candles.length;
    const lastBar = candles[n - 1];
    const prevBar = candles[n - 2];

    let regBullDiv = false;
    let regBearDiv = false;
    let hiddenBullishConfirmed = false;
    let hiddenBearishConfirmed = false;

    const cprTop = Math.max(cpr.DTc, cpr.DBc);
    const cprBottom = Math.min(cpr.DTc, cpr.DBc);

    // Directional confirmation close on the latest completed bar
    const isBullishConfirmCandle = (lastBar.close > lastBar.open) && (lastBar.close > prevBar.close);
    const isBearishConfirmCandle = (lastBar.close < lastBar.open) && (lastBar.close < prevBar.close);

    // Scan divergence pivot bars within confirmation window (1 to 5 bars prior to lastBar)
    const minDivIdx = Math.max(2, n - 6);
    const maxDivIdx = n - 2;

    for (let i = maxDivIdx; i >= minDivIdx; i--) {
        const curC = candles[i];
        const curOsc = outs[i];

        // Check if price broke the extreme between divergence bar i and lastBar
        let bullInvalidated = false;
        let bearInvalidated = false;
        for (let m = i + 1; m < n; m++) {
            if (candles[m].low < curC.low || candles[m].close < curC.low) bullInvalidated = true;
            if (candles[m].high > curC.high || candles[m].close > curC.high) bearInvalidated = true;
        }

        // Compare against prior swing pivots j (must have at least 2 bars separation: i - j >= 2)
        for (let j = i - 2; j >= Math.max(1, i - 12); j--) {
            const priorC = candles[j];
            const priorOsc = outs[j];

            // Local swing extreme checks (ensures genuine structural pivot wave)
            const isPriorSwingLow = priorC.low <= candles[j - 1].low && priorC.low <= candles[j + 1].low;
            const isPriorSwingHigh = priorC.high >= candles[j - 1].high && priorC.high >= candles[j + 1].high;

            // Theoretical trendline slope validation: neither price nor oscillator may breach the slope line between j and i
            let validBullSlope = true;
            let validBearSlope = true;
            if (i > j + 1) {
                const px1 = j, py1_low = priorC.low, py1_high = priorC.high;
                const px2 = i, py2_low = curC.low, py2_high = curC.high;
                const oy1 = priorOsc, oy2 = curOsc;
                
                const pSlopeLow = (py2_low - py1_low) / (px2 - px1);
                const pSlopeHigh = (py2_high - py1_high) / (px2 - px1);
                const oSlope = (oy2 - oy1) / (px2 - px1);

                for (let k = j + 1; k < i; k++) {
                    const barK = candles[k];
                    const oscK = outs[k];
                    const pTheoLow = py1_low + pSlopeLow * (k - px1);
                    const pTheoHigh = py1_high + pSlopeHigh * (k - px1);
                    const oTheo = oy1 + oSlope * (k - px1);

                    // For bullish (lows): neither price low nor osc may breach below theoretical support line
                    if (barK.low < pTheoLow || oscK < oTheo) {
                        validBullSlope = false;
                    }
                    // For bearish (highs): neither price high nor osc may breach above theoretical resistance line
                    if (barK.high > pTheoHigh || oscK > oTheo) {
                        validBearSlope = false;
                    }
                }
            }

            // Regular Bullish Divergence: Lower Low on price, Higher Low on oscillator, valid slope, not invalidated, confirmed candle close, DMI aligned
            if (!regBullDiv && isPriorSwingLow && curC.low < priorC.low && curOsc > priorOsc && validBullSlope && !bullInvalidated) {
                if (isBullishConfirmCandle && !(minus > plus)) {
                    regBullDiv = true;
                }
            }

            // Regular Bearish Divergence: Higher High on price, Lower High on oscillator, valid slope, not invalidated, confirmed candle close, DMI aligned
            if (!regBearDiv && isPriorSwingHigh && curC.high > priorC.high && curOsc < priorOsc && validBearSlope && !bearInvalidated) {
                if (isBearishConfirmCandle && !(plus > minus)) {
                    regBearDiv = true;
                }
            }

            // Hidden Bullish: Higher Low on price, Lower Low on oscillator, inside CPR/VA, valid slope, not invalidated, confirmed candle close, DMI aligned
            if (!hiddenBullishConfirmed && isPriorSwingLow && curC.low > priorC.low && curOsc < priorOsc && validBullSlope && !bullInvalidated) {
                const insideCPR = (curC.close >= cprBottom && curC.close <= cprTop) ||
                                  (Math.min(curC.open, curC.close) <= cprTop && Math.max(curC.open, curC.close) >= cprBottom);
                if (insideCPR && isBullishConfirmCandle && !(minus > plus)) {
                    hiddenBullishConfirmed = true;
                }
            }

            // Hidden Bearish: Lower High on price, Higher High on oscillator, inside CPR/VA, valid slope, not invalidated, confirmed candle close, DMI aligned
            if (!hiddenBearishConfirmed && isPriorSwingHigh && curC.high < priorC.high && curOsc > priorOsc && validBearSlope && !bearInvalidated) {
                const insideCPR = (curC.close >= cprBottom && curC.close <= cprTop) ||
                                  (Math.min(curC.open, curC.close) <= cprTop && Math.max(curC.open, curC.close) >= cprBottom);
                if (insideCPR && isBearishConfirmCandle && !(plus > minus)) {
                    hiddenBearishConfirmed = true;
                }
            }
        }
    }

    return { regBullDiv, regBearDiv, hiddenBullishConfirmed, hiddenBearishConfirmed };
}

// ── Isolated Trade Lifecycle Helpers (Dedicated to public.shadow_signals) ──
async function updateShadowTrade(tradeId, updatePayload) {
    try {
        if (updatePayload && updatePayload.exit_at && updatePayload.metadata) {
            const exitMs = new Date(updatePayload.exit_at).getTime();
            const exitDayStr = new Date(exitMs + 5.5 * 3600000).toISOString().substring(0, 10);
            const exitDateTimeStr = new Date(exitMs).toISOString().replace('T', ' ').substring(0, 19);
            if (!updatePayload.metadata.close_date) updatePayload.metadata.close_date = exitDayStr;
            if (!updatePayload.metadata.closeDate) updatePayload.metadata.closeDate = exitDateTimeStr;
        }
        await supabase.from('shadow_signals').update(updatePayload).eq('id', tradeId);
    } catch (e) {
        console.error(`[DhanScanner] Error updating shadow_signals ${tradeId}:`, e.message);
    }
}

async function deleteShadowTrade(tradeId) {
    try {
        await supabase.from('shadow_signals').delete().eq('id', tradeId);
    } catch (e) {
        console.error(`[DhanScanner] Error deleting from shadow_signals ${tradeId}:`, e.message);
    }
}

// ── Autonomous Limit Fill & Active Trade Tracking ─────────────────────────────

async function processOpenTradesAndFills(symbol, latestCandle, ema32 = 0) {
    if (!latestCandle) return;

    try {
        const { data: openRows, error } = await supabase
            .from('shadow_signals')
            .select('*')
            .eq('symbol', symbol)
            .eq('source', 'blackbox_dhan')
            .or('status.eq.ACTIVE,status.eq.OPEN,status.eq.ACTIVE LIMIT,status.eq.Active Limit,status.ilike.%TRADE ACTIVE%');

        if (error || !openRows || openRows.length === 0) return;

        const nowIso = new Date().toISOString();

        for (const trade of openRows) {
            let meta = trade.metadata || {};
            if (typeof meta === 'string') {
                try { meta = JSON.parse(meta); } catch (e) { meta = {}; }
            }

            const statusUpper = (trade.status || '').toUpperCase();
            const isLiveActive = statusUpper.includes('TRADE ACTIVE') || statusUpper.includes('⚡') || Boolean(meta.real_entry_time);
            const isLong = (trade.type || '').toUpperCase().includes('LONG') || (trade.type || '').toUpperCase().includes('BUY');
            const entryPrice = parseFloat(trade.entry || trade.entry_price || 0);
            const stopPrice = parseFloat(trade.stop || trade.stop_loss || 0);

            // 1. EVALUATE PENDING LIMIT ORDER FILL (Bounce Touch-Point) & INVALIDATION
            if (!isLiveActive && entryPrice > 0) {
                if (isLong) {
                    // Check Stop Loss breach FIRST: if price touched or dropped below stop, limit order is INVALIDATED
                    if (stopPrice > 0 && latestCandle.low <= stopPrice) {
                        // Immediately hard-delete invalidated limit order (TradingView Zero-Ghost Parity)
                        await deleteShadowTrade(trade.id);
                        console.log(`[DhanScanner] Long limit ${symbol} invalidated & deleted (Stop breached @ ₹${latestCandle.low} <= ₹${stopPrice})`);
                        continue;
                    }

                    // LONG LIMIT TOUCH-POINT: Candle wicked down to or below entry, but held above stop loss
                    if (latestCandle.low <= entryPrice) {
                        // VALID BOUNCE LIMIT EXECUTION: Trigger TradeFill!
                        meta.real_entry_time = nowIso;
                        meta.fill_price = entryPrice;
                        meta.fill_candle_ts = latestCandle.timestamp;

                        await supabase.from('shadow_signals').update({
                            status: '⚡ TRADE ACTIVE',
                            trigger: 'TradeFill',
                            updated_at: nowIso,
                            metadata: meta
                        });
                        console.log(`[DhanScanner] ⚡ LIMIT FILLED: Long ${symbol} entered @ ₹${entryPrice}`);
                        continue;
                    }
                } else {
                    // Check Stop Loss breach FIRST: if price touched or spiked above stop, limit order is INVALIDATED
                    if (stopPrice > 0 && latestCandle.high >= stopPrice) {
                        // Immediately hard-delete invalidated limit order (TradingView Zero-Ghost Parity)
                        await deleteShadowTrade(trade.id);
                        console.log(`[DhanScanner] Short limit ${symbol} invalidated & deleted (Stop breached @ ₹${latestCandle.high} >= ₹${stopPrice})`);
                        continue;
                    }

                    // SHORT LIMIT TOUCH-POINT: Candle wicked up to or above entry, but held below stop loss
                    if (latestCandle.high >= entryPrice) {
                        // VALID BOUNCE LIMIT EXECUTION: Trigger TradeFill!
                        meta.real_entry_time = nowIso;
                        meta.fill_price = entryPrice;
                        meta.fill_candle_ts = latestCandle.timestamp;

                        await updateShadowTrade(trade.id, {
                            status: '⚡ TRADE ACTIVE',
                            trigger: 'TradeFill',
                            updated_at: nowIso,
                            metadata: meta
                        });
                        console.log(`[DhanScanner] ⚡ LIMIT FILLED: Short ${symbol} entered @ ₹${entryPrice}`);
                        continue;
                    }
                }
            }

            // 2. EVALUATE TARGETS, DYNAMIC EMA EXITS, AND TRAILING STOP LOSS FOR LIVE ACTIVE TRADES
            if (isLiveActive && entryPrice > 0) {
                const tp1 = parseFloat(trade.target || trade.tp1 || 0);
                const tp2 = parseFloat(trade.tp2 || 0);
                const tp3 = parseFloat(trade.tp3 || 0);
                const tp4 = parseFloat(trade.tp4 || 0);
                let currentSL = parseFloat(trade.trailing_stop || trade.trail_sl || trade.stop || 0);

                if (isLong) {
                    // ── POST-TP4 HIERARCHY EVALUATION (Indicator Code Parity) ──
                    if (meta.tp4_hit) {
                        // Check Dynamic EMA Exit: when EMA32 is above TP3, closing below EMA32 triggers 'Hit EMA'
                        if (ema32 > tp3 && latestCandle.close < ema32) {
                            const exactPct = Math.round(((latestCandle.close - entryPrice) / entryPrice) * 100 * 100) / 100;
                            meta.exact_pct = exactPct;
                            meta.exit_reason = 'HIT_EMA_POST_TP4';
                            meta.exit_level = 'EMA';
                            await updateShadowTrade(trade.id, {
                                status: 'Hit EMA',
                                outcome: 'WIN',
                                exit_price: latestCandle.close,
                                exit_at: nowIso,
                                updated_at: nowIso,
                                metadata: meta
                            });
                            console.log(`[DhanScanner] Trade Closed: Long ${symbol} -> Hit EMA (+${exactPct}%)`);
                            continue;
                        }

                        // Check TP3 Trailing Stop Hit: price retraced to TP3
                        if (latestCandle.low <= tp3) {
                            const exactPct = Math.round(((tp3 - entryPrice) / entryPrice) * 100 * 100) / 100;
                            meta.exact_pct = exactPct;
                            meta.exit_reason = 'HIT_TP3_TRAILING';
                            meta.exit_level = 'TP3';
                            await updateShadowTrade(trade.id, {
                                status: 'Hit TP3 Trailing',
                                outcome: 'WIN',
                                exit_price: tp3,
                                exit_at: nowIso,
                                updated_at: nowIso,
                                metadata: meta
                            });
                            console.log(`[DhanScanner] Trade Closed: Long ${symbol} -> Hit TP3 Trailing (+${exactPct}%)`);
                            continue;
                        }

                        // Runner continues: trail SL to max(TP3, EMA32)
                        const updatedEmaSL = ema32 > tp3 ? ema32 : tp3;
                        if (currentSL !== updatedEmaSL) {
                            await updateShadowTrade(trade.id, {
                                trailing_stop: updatedEmaSL,
                                updated_at: nowIso
                            });
                        }
                        continue;
                    }

                    // ── PRE-TP4 STOP LOSS CHECK ──
                    if (currentSL > 0 && latestCandle.low <= currentSL) {
                        const exactPct = Math.round(((currentSL - entryPrice) / entryPrice) * 100 * 100) / 100;
                        meta.exact_pct = exactPct;
                        meta.exit_reason = currentSL >= entryPrice ? 'TRAILING_STOP_HIT' : 'STOP_LOSS_HIT';
                        const outcome = exactPct > 0.005 ? 'WIN' : exactPct < -0.005 ? 'LOSS' : 'BREAKEVEN';

                        let statusLabel = 'Hit Initial SL';
                        if (meta.tp3_hit) statusLabel = 'Hit TP2 Trailing';
                        else if (meta.tp2_hit) statusLabel = 'Hit TP1 Trailing';
                        else if (meta.tp1_hit) statusLabel = 'Hit B/E';

                        await updateShadowTrade(trade.id, {
                            status: statusLabel,
                            outcome: outcome,
                            exit_price: currentSL,
                            exit_at: nowIso,
                            updated_at: nowIso,
                            metadata: meta
                        });
                        console.log(`[DhanScanner] Trade Closed: Long ${symbol} -> ${statusLabel} (${exactPct}%)`);
                        continue;
                    }

                    // ── TAKE PROFIT PROGRESSION ──
                    if (tp4 > 0 && latestCandle.high >= tp4) {
                        // Tagged TP4: lock stop loss at TP3, activate dynamic EMA trailing stop, trade continues!
                        meta.tp4_hit = true;
                        meta.tp3_hit = true;
                        meta.tp2_hit = true;
                        meta.tp1_hit = true;
                        const initialEmaSL = ema32 > tp3 ? ema32 : tp3;
                        await updateShadowTrade(trade.id, {
                            trailing_stop: initialEmaSL,
                            status: '⚡ TRADE ACTIVE (TP4 Hit)',
                            updated_at: nowIso,
                            metadata: meta
                        });
                        console.log(`[DhanScanner] 🎯 TP4 TAGGED: Long ${symbol} hit TP4 @ ₹${tp4}. Trailing SL locked at TP3.`);
                        continue;
                    } else if (tp3 > 0 && latestCandle.high >= tp3 && !meta.tp3_hit) {
                        meta.tp3_hit = true;
                        meta.tp2_hit = true;
                        meta.tp1_hit = true;
                        await updateShadowTrade(trade.id, {
                            trailing_stop: tp2,
                            status: 'Trailing (TP3 Met)',
                            updated_at: nowIso,
                            metadata: meta
                        });
                    } else if (tp2 > 0 && latestCandle.high >= tp2 && !meta.tp2_hit) {
                        meta.tp2_hit = true;
                        meta.tp1_hit = true;
                        await updateShadowTrade(trade.id, {
                            trailing_stop: tp1,
                            status: 'Trailing (TP2 Met)',
                            updated_at: nowIso,
                            metadata: meta
                        });
                    } else if (tp1 > 0 && tp2 > 0 && latestCandle.high >= ((tp1 + tp2) / 2.0) && !meta.mid_tp1_tp2_hit && !meta.tp2_hit) {
                        meta.mid_tp1_tp2_hit = true;
                        meta.tp1_hit = true;
                        await updateShadowTrade(trade.id, {
                            trailing_stop: entryPrice,
                            status: 'Trailing (Mid TP1-TP2 Met)',
                            updated_at: nowIso,
                            metadata: meta
                        });
                    } else if (tp1 > 0 && latestCandle.high >= tp1 && !meta.tp1_hit) {
                        meta.tp1_hit = true;
                        await updateShadowTrade(trade.id, {
                            status: '🎯 TP1 Hit',
                            updated_at: nowIso,
                            metadata: meta
                        });
                    }
                } else {
                    // ── SHORT TRADE EVALUATION ──
                    // ── POST-TP4 HIERARCHY EVALUATION (Indicator Code Parity) ──
                    if (meta.tp4_hit) {
                        // Check Dynamic EMA Exit: when EMA32 is below TP3, closing above EMA32 triggers 'Hit EMA'
                        if (ema32 > 0 && ema32 < tp3 && latestCandle.close > ema32) {
                            const exactPct = Math.round(((entryPrice - latestCandle.close) / entryPrice) * 100 * 100) / 100;
                            meta.exact_pct = exactPct;
                            meta.exit_reason = 'HIT_EMA_POST_TP4';
                            meta.exit_level = 'EMA';
                            await updateShadowTrade(trade.id, {
                                status: 'Hit EMA',
                                outcome: 'WIN',
                                exit_price: latestCandle.close,
                                exit_at: nowIso,
                                updated_at: nowIso,
                                metadata: meta
                            });
                            console.log(`[DhanScanner] Trade Closed: Short ${symbol} -> Hit EMA (+${exactPct}%)`);
                            continue;
                        }

                        // Check TP3 Trailing Stop Hit: price retraced to TP3
                        if (latestCandle.high >= tp3) {
                            const exactPct = Math.round(((entryPrice - tp3) / entryPrice) * 100 * 100) / 100;
                            meta.exact_pct = exactPct;
                            meta.exit_reason = 'HIT_TP3_TRAILING';
                            meta.exit_level = 'TP3';
                            await updateShadowTrade(trade.id, {
                                status: 'Hit TP3 Trailing',
                                outcome: 'WIN',
                                exit_price: tp3,
                                exit_at: nowIso,
                                updated_at: nowIso,
                                metadata: meta
                            });
                            console.log(`[DhanScanner] Trade Closed: Short ${symbol} -> Hit TP3 Trailing (+${exactPct}%)`);
                            continue;
                        }

                        // Runner continues: trail SL to min(TP3, EMA32)
                        const updatedEmaSL = (ema32 > 0 && ema32 < tp3) ? ema32 : tp3;
                        if (currentSL !== updatedEmaSL) {
                            await updateShadowTrade(trade.id, {
                                trailing_stop: updatedEmaSL,
                                updated_at: nowIso
                            });
                        }
                        continue;
                    }

                    // ── PRE-TP4 STOP LOSS CHECK ──
                    if (currentSL > 0 && latestCandle.high >= currentSL) {
                        const exactPct = Math.round(((entryPrice - currentSL) / entryPrice) * 100 * 100) / 100;
                        meta.exact_pct = exactPct;
                        meta.exit_reason = currentSL <= entryPrice ? 'TRAILING_STOP_HIT' : 'STOP_LOSS_HIT';
                        const outcome = exactPct > 0.005 ? 'WIN' : exactPct < -0.005 ? 'LOSS' : 'BREAKEVEN';

                        let statusLabel = 'Hit Initial SL';
                        if (meta.tp3_hit) statusLabel = 'Hit TP2 Trailing';
                        else if (meta.tp2_hit) statusLabel = 'Hit TP1 Trailing';
                        else if (meta.tp1_hit) statusLabel = 'Hit B/E';

                        await updateShadowTrade(trade.id, {
                            status: statusLabel,
                            outcome: outcome,
                            exit_price: currentSL,
                            exit_at: nowIso,
                            updated_at: nowIso,
                            metadata: meta
                        });
                        console.log(`[DhanScanner] Trade Closed: Short ${symbol} -> ${statusLabel} (${exactPct}%)`);
                        continue;
                    }

                    // ── TAKE PROFIT PROGRESSION ──
                    if (tp4 > 0 && latestCandle.low <= tp4) {
                        // Tagged TP4: lock stop loss at TP3, activate dynamic EMA trailing stop, trade continues!
                        meta.tp4_hit = true;
                        meta.tp3_hit = true;
                        meta.tp2_hit = true;
                        meta.tp1_hit = true;
                        const initialEmaSL = (ema32 > 0 && ema32 < tp3) ? ema32 : tp3;
                        await updateShadowTrade(trade.id, {
                            trailing_stop: initialEmaSL,
                            status: '⚡ TRADE ACTIVE (TP4 Hit)',
                            updated_at: nowIso,
                            metadata: meta
                        });
                        console.log(`[DhanScanner] 🎯 TP4 TAGGED: Short ${symbol} hit TP4 @ ₹${tp4}. Trailing SL locked at TP3.`);
                        continue;
                    } else if (tp3 > 0 && latestCandle.low <= tp3 && !meta.tp3_hit) {
                        meta.tp3_hit = true;
                        meta.tp2_hit = true;
                        meta.tp1_hit = true;
                        await updateShadowTrade(trade.id, {
                            trailing_stop: tp2,
                            status: 'Trailing (TP3 Met)',
                            updated_at: nowIso,
                            metadata: meta
                        });
                    } else if (tp2 > 0 && latestCandle.low <= tp2 && !meta.tp2_hit) {
                        meta.tp2_hit = true;
                        meta.tp1_hit = true;
                        await updateShadowTrade(trade.id, {
                            trailing_stop: tp1,
                            status: 'Trailing (TP2 Met)',
                            updated_at: nowIso,
                            metadata: meta
                        });
                    } else if (tp1 > 0 && tp2 > 0 && latestCandle.low <= ((tp1 + tp2) / 2.0) && !meta.mid_tp1_tp2_hit && !meta.tp2_hit) {
                        meta.mid_tp1_tp2_hit = true;
                        meta.tp1_hit = true;
                        await updateShadowTrade(trade.id, {
                            trailing_stop: entryPrice,
                            status: 'Trailing (Mid TP1-TP2 Met)',
                            updated_at: nowIso,
                            metadata: meta
                        });
                    } else if (tp1 > 0 && latestCandle.low <= tp1 && !meta.tp1_hit) {
                        meta.tp1_hit = true;
                        await updateShadowTrade(trade.id, {
                            status: '🎯 TP1 Hit',
                            updated_at: nowIso,
                            metadata: meta
                        });
                    }
                }
            }
        }
    } catch (e) {
        console.error(`[DhanScanner] Error processing fills/targets for ${symbol}:`, e.message);
    }
}

// ── Decoupled Open Trade Lifecycle Sweep (Preserves Existing Trades till EOD/EMA/SL) ──

async function sweepAllOpenTradesAndFills(symbolsMap) {
    try {
        const { data: openRows, error } = await supabase
            .from('shadow_signals')
            .select('*')
            .eq('source', 'blackbox_dhan')
            .or('status.eq.ACTIVE,status.eq.OPEN,status.eq.ACTIVE LIMIT,status.eq.Active Limit,status.ilike.%TRADE ACTIVE%');

        if (error || !openRows || openRows.length === 0) return 0;

        console.log(`[DhanScanner] Decoupled Position Manager: Sweeping ${openRows.length} open/pending trade(s)...`);
        const now = new Date();
        const ist = new Date(now.toLocaleString("en-US", { timeZone: "Asia/Kolkata" }));
        const istHours = ist.getHours() + (ist.getMinutes() / 60);
        const dayOfWeek = ist.getDay(); // 0 = Sun, 6 = Sat
        const isWeekend = dayOfWeek === 0 || dayOfWeek === 6;

        // Group open trades by symbol
        const bySym = {};
        for (const t of openRows) {
            if (!bySym[t.symbol]) bySym[t.symbol] = [];
            bySym[t.symbol].push(t);
        }

        for (const sym of Object.keys(bySym)) {
            const trades = bySym[sym];
            const info = symbolsMap[sym];
            const isCommodity = info ? (info.exchange_segment === 5 || info.instrument === 'COMMODITY' || info.instrument === 'FUTCOM') : (sym.includes('MCX') || sym.includes('NATURAL') || sym.includes('ALUMIN'));
            const marketClosed = isWeekend || (isCommodity ? (istHours >= 23.5 || istHours < 9.0) : (istHours >= 15.5 || istHours < 9.25));

            // If market session is closed for this symbol:
            if (marketClosed) {
                for (const trade of trades) {
                    let meta = trade.metadata || {};
                    if (typeof meta === 'string') {
                        try { meta = JSON.parse(meta); } catch (e) { meta = {}; }
                    }
                    const statusUpper = (trade.status || '').toUpperCase();
                    const isLiveActive = statusUpper.includes('TRADE ACTIVE') || statusUpper.includes('⚡') || Boolean(meta.real_entry_time) || trade.trigger === 'TradeFill';

                    if (!isLiveActive) {
                        // Zero-Ghost Mandate: Hard delete unexecuted pending limits at session close
                        await deleteShadowTrade(trade.id);
                        console.log(`[DhanScanner] Zero-Ghost: Hard deleted expired limit ${sym} (${trade.id}) at session close`);
                    } else if (trade.exit_price == null) {
                        // Live executed trade reached EOD: Close as EOD Exit
                        const entryPrice = parseFloat(trade.entry || trade.entry_price || 0);
                        const exitPrice = parseFloat(trade.trailing_stop || trade.stop || trade.target || entryPrice);
                        const isShort = (trade.type || '').toUpperCase().includes('SHORT') || (trade.type || '').toUpperCase().includes('SELL');
                        let exactPct = 0;
                        if (entryPrice > 0) {
                            exactPct = isShort ? ((entryPrice - exitPrice) / entryPrice) * 100 : ((exitPrice - entryPrice) / entryPrice) * 100;
                            exactPct = Math.round(exactPct * 100) / 100;
                        }
                        meta.exact_pct = exactPct;
                        meta.exit_reason = 'EOD_SESSION_CLOSE';
                        meta.exit_level = 'EOD';
                        const outcome = exactPct > 0.005 ? 'WIN' : exactPct < -0.005 ? 'LOSS' : 'BREAKEVEN';
                        const statusLabel = exactPct > 0.005 ? 'EOD Exit (TP)' : exactPct < -0.005 ? 'EOD Exit (SL)' : 'EOD Exit (BE)';
                        const nowIso = now.toISOString();

                        await updateShadowTrade(trade.id, {
                            status: statusLabel,
                            outcome: outcome,
                            exit_price: exitPrice,
                            exit_at: nowIso,
                            updated_at: nowIso,
                            metadata: meta
                        });
                        console.log(`[DhanScanner] Closed live trade at EOD: ${sym} -> ${statusLabel} (${exactPct}%)`);
                    }
                }
                continue;
            }

            // Market session is OPEN: Monitor trade lifecycle
            if (info) {
                // 1. Attempt live intraday candles
                const candles = await fetchIntradayCandles(sym, info);
                if (candles && candles.length > 0) {
                    const lastBar = candles[candles.length - 1];
                    const closes = candles.map(c => c.close);
                    const ema32 = computeEMA(closes, 32);
                    await processOpenTradesAndFills(sym, lastBar, ema32);
                } else {
                    // 2. Fallback to DhanHQ Market Quote / LTP API (active even when Charts API returns DH-902)
                    const quoteBar = await fetchDhanLtpOrQuote(sym, info);
                    if (quoteBar) {
                        console.log(`[DhanScanner] Monitored ${sym} via live Quote/LTP fallback (DH-902 active): Close=₹${quoteBar.close}`);
                        await processOpenTradesAndFills(sym, quoteBar, 0);
                    }
                }
            }
        }
    } catch (err) {
        console.error('[DhanScanner] Error in sweepAllOpenTradesAndFills:', err.message);
    }
}

// ── Market Close Exit Sweep ────────────────────────────────────────────────────

async function sweepMarketCloseExits(targetMarket = 'ALL') {
    console.log(`[DhanScanner] Running Market Close Exit Sweep for ${targetMarket}...`);
    try {
        let query = supabase
            .from('shadow_signals')
            .select('*')
            .eq('source', 'blackbox_dhan')
            .or('outcome.eq.OPEN,outcome.eq.Open,outcome.is.null,status.ilike.%active%,status.ilike.%open%');

        if (targetMarket === 'NSE') query = query.eq('exchange', 'nifty');
        else if (targetMarket === 'MCX') query = query.eq('exchange', 'mcx');

        const { data: openRows, error } = await query;
        if (error || !openRows || openRows.length === 0) return 0;

        let settled = 0;
        const nowIso = new Date().toISOString();

        for (const row of openRows) {
            const statusUpper = (row.status || '').toUpperCase();
            const outcomeUpper = (row.outcome || '').toUpperCase();
            if (statusUpper.includes('CANCEL') || outcomeUpper.includes('CANCEL') || row.exit_price != null) {
                continue;
            }

            let meta = row.metadata || {};
            if (typeof meta === 'string') {
                try { meta = JSON.parse(meta); } catch (e) { meta = {}; }
            }

            const isExecuted = statusUpper.includes('TRADE ACTIVE') ||
                               statusUpper.includes('⚡') ||
                               Boolean(meta.real_entry_time) ||
                               row.trigger === 'TradeFill';

            if (!isExecuted) {
                // Hard-delete unexecuted limit orders at market close (TradingView Zero-Ghost Parity)
                await deleteShadowTrade(row.id);
                console.log(`[DhanScanner] Deleted unexecuted expired limit at market close: ${row.symbol} (${row.id})`);
                settled++;
            } else {
                const entry = parseFloat(row.entry || row.entry_price || 0);
                const exitPrice = parseFloat(row.target || entry);
                const isShort = (row.type || '').toUpperCase().includes('SHORT') || (row.type || '').toUpperCase().includes('SELL');

                let exactPct = 0.0;
                if (entry > 0) {
                    exactPct = isShort ? ((entry - exitPrice) / entry) * 100 : ((exitPrice - entry) / entry) * 100;
                    exactPct = Math.round(exactPct * 100) / 100;
                }

                meta.exact_pct = exactPct;
                meta.exit_reason = 'MARKET_CLOSE_EOD_EXIT';
                meta.exit_level = 'EOD';

                const finalOutcome = exactPct > 0.005 ? 'WIN' : exactPct < -0.005 ? 'LOSS' : 'BREAKEVEN';
                const finalStatus = exactPct > 0.005 ? 'EOD Exit (TP)' : exactPct < -0.005 ? 'EOD Exit (SL)' : 'EOD Exit (BE)';

                await updateShadowTrade(row.id, {
                    status: finalStatus,
                    outcome: finalOutcome,
                    exit_price: exitPrice,
                    exit_at: nowIso,
                    updated_at: nowIso,
                    metadata: meta
                });
                settled++;
            }
        }

        console.log(`[DhanScanner] Market close sweep settled ${settled} trades.`);
        return settled;
    } catch (e) {
        console.error('[DhanScanner] Error during market close sweep:', e);
        return 0;
    }
}

// ── Main Scan Execution ────────────────────────────────────────────────────────

async function runDhanScan(limitCount = null) {
    const ist = getISTDate();
    const mins = getISTMinutes();
    console.log(`[DhanScanner] Starting scan cycle at ${ist.toISOString()} IST (Mins: ${mins})`);

    // 0. DECOUPLED POSITION MANAGEMENT: Sweep all open trades & pending limits FIRST
    // Guarantees that existing trades continue their journey till EOD or EMA or SL exits
    // even if candidate scanning is restricted (e.g. DH-902 unsubscribed Data API).
    await sweepAllOpenTradesAndFills(symbolsMap);

    // Check EOD sweeps
    if (mins >= 930 && mins < 945) {
        // At 15:30 IST: Sweep NSE Equities
        await sweepMarketCloseExits('NSE');
    }
    if (mins >= 1410) {
        // At 23:30 IST: Sweep MCX Commodities
        await sweepMarketCloseExits('MCX');
        return { message: 'MCX EOD sweep completed', newSignals: 0 };
    }

    // 0. Dynamically sync active MCX front-month contracts from Supabase system_config
    try {
        if (supabase) {
            const { data: configData } = await supabase
                .from('system_config')
                .select('value, updated_at')
                .eq('key', 'mcx_front_month_symbols')
                .maybeSingle();
            if (configData && configData.value) {
                let dynamicCount = 0;
                for (const [sym, info] of Object.entries(configData.value)) {
                    if (symbolsMap[sym] && info.security_id) {
                        symbolsMap[sym].security_id = String(info.security_id);
                        if (info.trading_symbol) symbolsMap[sym].trading_symbol = info.trading_symbol;
                        if (info.expiry) symbolsMap[sym].expiry = info.expiry;
                        dynamicCount++;
                    }
                }
                console.log(`[DhanScanner] Dynamically synced ${dynamicCount} MCX front-month contracts from Supabase.`);
            }
        }
    } catch (syncErr) {
        console.warn('[DhanScanner] Dynamic MCX contract sync notice:', syncErr.message);
    }

    // Determine active symbols based on market sessions:
    // If between 09:15 and 15:30 IST: scan both NSE Equities and MCX Commodities.
    // If after 15:30 IST (up to 23:30 IST): scan MCX Commodities ONLY.
    const allSymbols = Object.keys(symbolsMap);
    const nseOpen = isNSEOpen();
    const mcxOpen = isMCXOpen();

    let targetSymbols = allSymbols;
    if (nseOpen || mcxOpen) {
        targetSymbols = allSymbols.filter(sym => {
            const info = symbolsMap[sym];
            const isCommodity = info.exchange_segment === 5 || info.instrument === 'COMMODITY' || info.instrument === 'FUTCOM';
            if (isCommodity) return mcxOpen;
            return nseOpen;
        });
    }

    if (limitCount) {
        targetSymbols = targetSymbols.slice(0, limitCount);
    }

    console.log(`[DhanScanner] Active universe: ${targetSymbols.length} assets (NSE: ${nseOpen ? 'OPEN' : 'CLOSED'}, MCX: ${mcxOpen ? 'OPEN' : 'CLOSED'})`);
    if (targetSymbols.length === 0) {
        return { message: 'No markets currently open for trading', newSignals: 0 };
    }

    const detectedSignals = [];
    const screenerCandidates = [];
    const BATCH_SIZE = 2;

    for (let i = 0; i < targetSymbols.length; i += BATCH_SIZE) {
        const batch = targetSymbols.slice(i, i + BATCH_SIZE);
        const batchPromises = batch.map(async (sym) => {
            try {
                const info = symbolsMap[sym];
                const isCommodity = info.exchange_segment === 5 || info.instrument === 'COMMODITY' || info.instrument === 'FUTCOM';
                const marketName = isCommodity ? 'mcx' : 'nifty';

                const candles = await fetchIntradayCandles(sym, info);
                if (!candles || candles.length < 3) {
                    console.warn(`[DhanScanner] ${sym} intraday candles unavailable (DH-902 subscription requirement / feed restriction). Gating NEW trade consideration. Existing trades preserved.`);
                    return null;
                }

                const daily = await fetchDailyLevels(sym, info, candles);
                if (!daily) return null;

                const cam = computeCamarillaLevels(daily.high, daily.low, daily.close);
                const cpr = computeDualCPR(daily, { high: daily.prev_high, low: daily.prev_low, close: daily.prev_close });

                const lastBar = candles[candles.length - 1];
                const prevBar = candles[candles.length - 2];

                // 1. Separate today's session candles and yesterday's session candles
                const todayStr = getISTDateString();
                const todayCandles = [];
                const yesterdayCandles = [];
                for (const c of candles) {
                    const cd = new Date((c.timestamp * 1000) + (5.5 * 60 * 60 * 1000));
                    const cdStr = cd.toISOString().split('T')[0];
                    if (cdStr === todayStr) {
                        todayCandles.push(c);
                    } else {
                        yesterdayCandles.push(c);
                    }
                }

                const va = computeTPOValueArea(yesterdayCandles, daily);
                const todayOpen = todayCandles.length > 0 ? todayCandles[0].open : lastBar.open;
                const profile = computeMarketProfileAndBiases(todayOpen, lastBar.close, daily, cpr, va, cam);
                const { dX, mX, c1, z1, isSidewaysDay, dayAllowed } = profile;

                const prevDayRange = Math.max(daily.high - daily.low, 0.05);
                const vaWidth = Math.abs(va.VAH - va.VAL);
                const vaRatio = prevDayRange > 0 ? (vaWidth / prevDayRange) * 100 : 0;
                const isNcpr = Boolean(cpr.isNarrow);
                const isInsideCpr = Boolean(profile.isInsideCPR || (cpr.DTc < cpr.YTc && cpr.DBc > cpr.YBc));
                const isRejection = Boolean(profile.isRejectionDay);
                const isNva = Boolean(vaRatio < 38.0);
                const isOor = Boolean((dX && dX.includes('OUT OF RANGE')) || (todayOpen > daily.high && todayOpen > va.VAH) || (todayOpen < daily.low && todayOpen < va.VAL));
                const isContinuation = Boolean(c1 && c1.toUpperCase().includes('CONTINUATION'));
                const nowIso = new Date().toISOString();

                // Candidate Watchlist Collection: Record symbols exhibiting day-type setups
                if (isNcpr || isInsideCpr || isRejection || isNva || isOor || isContinuation) {
                    screenerCandidates.push({
                        symbol: sym,
                        type: 'SCREENER SETUP',
                        trigger: isNcpr ? 'NCPR Breakout' : isInsideCpr ? 'Inside CPR' : isRejection ? 'Rejection Day' : isOor ? 'Out of Range' : isNva ? 'Narrow Value' : 'Day Type Candidate',
                        entry: lastBar.close,
                        stop: cam.L4,
                        target: cam.H4,
                        status: 'WATCHLIST',
                        outcome: 'OPEN',
                        source: 'blackbox_dhan',
                        exchange: marketName,
                        signal_ts: nowIso,
                        metadata: {
                            source_feed: 'DhanHQ',
                            market_category: isCommodity ? 'MCX' : 'NIFTY',
                            day_type: mX,
                            opening_bias: dX,
                            institutional_bias: c1,
                            zone: z1,
                            is_ncpr: isNcpr,
                            cpr_type: isNcpr ? 'NCPR' : 'NORMAL',
                            is_inside_cpr: isInsideCpr,
                            is_rejection: isRejection,
                            is_rejection_day: isRejection,
                            is_nva: isNva,
                            is_narrow_value: isNva,
                            is_oor: isOor,
                            is_continuation: isContinuation,
                            cpr: { pivot: cpr.DP, tc: cpr.DTc, bc: cpr.DBc },
                            dtc: cpr.DTc,
                            dbc: cpr.DBc,
                            ytc: cpr.YTc,
                            ybc: cpr.YBc,
                            prev_range: prevDayRange,
                            prev_high: daily.high,
                            prev_low: daily.low,
                            vah: va.VAH,
                            val: va.VAL,
                            va_width: vaWidth,
                            va_ratio: vaRatio,
                            h4: cam.H4,
                            l4: cam.L4,
                            c1: c1
                        }
                    });
                }

                const closes = candles.map(c => c.close);
                const ema13 = computeEMA(closes, 13);
                const ema32 = computeEMA(closes, 32);
                const atr = computeATR(candles, 14);

                // 2. Process limit order touchpoints & trailing stops for existing positions (passes ema32 for Post-TP4 Dynamic EMA check)
                await processOpenTradesAndFills(sym, lastBar, ema32);

                // 3. Check if new trade entry is allowed (market open and within entry cutoff hours)
                const entryAllowed = isCommodity ? (mcxOpen && isMCXEntryAllowed()) : (nseOpen && isNSEEntryAllowed());
                if (!entryAllowed) {
                    return null;
                }

                // ── Strict Gating Rule Mandate:
                // Long: strictly low < H4
                // Short: strictly high > L4
                const longAllowed = lastBar.low < cam.H4;
                const shortAllowed = lastBar.high > cam.L4;

                const signalsForSym = [];

                // ── Compute Indicators from Master Pine Script ──────────────────
                const { plus, minus } = computeDMI(candles, 14);
                const { m0, m10 } = computeOscillatorTrend(candles);
                const { fPivotPDEMAF, fPivotPDEMAS } = computePivotPDEMAs(candles);
                const pDemaSlope = computePivotPDEMASlope(candles, 13);
                const { highLeftEmpty, lowLeftEmpty } = computePivotPoints(candles, 10);

                const fPivots = candles.map(c => (c.high + c.low + c.close) / 3.0);
                const fShortEMA = computeEMA(fPivots, 13);
                const fMedEMA = computeEMA(fPivots, 32);

                const GREEN1 = (plus > minus) && (m0 > m10);
                const RED1 = (minus > plus) && (m0 < m10);
                const Greenzone = (plus > minus) && (fShortEMA > fMedEMA) && (fPivotPDEMAF > fPivotPDEMAS);
                const Redzone = (minus > plus) && (fShortEMA < fMedEMA) && (fPivotPDEMAF < fPivotPDEMAS);
                const emaCanBuy = Greenzone || !Redzone;
                const emaCanSell = Redzone || !Greenzone;

                // Support & Resistance Swings & Bounces (Lines 1920-2040 & 2942-3029)
                const { supports: pSups, resistances: pRes } = extractRecentPivots(candles, 10, 15);
                const allSups = [cam.L3, cam.L4, cpr.DBc, va.VAL, ...pSups];
                const allRes = [cam.H3, cam.H4, cpr.DTc, va.VAH, ...pRes];

                const bouncedOffSR_Up = allSups.some(lvl => isValidBounceUp(lvl, lastBar));
                const bouncedOffSR_Down = allRes.some(lvl => isValidBounceDown(lvl, lastBar));

                const GrS = GREEN1 && bouncedOffSR_Up;
                const ReS = RED1 && bouncedOffSR_Down;

                // Authentic Retest-Only Midpoint Logic (Strictly mirroring Pine Script lines 3144-3152)
                // Midpoint is established by a prior Power Candle and must be retested by a subsequent bar
                let priorGrsMid = null;
                let priorResMid = null;
                for (let bIdx = candles.length - 2; bIdx >= Math.max(0, candles.length - 12); bIdx--) {
                    const pBar = candles[bIdx];
                    const pBounceUp = allSups.some(lvl => isValidBounceUp(lvl, pBar));
                    const pBounceDown = allRes.some(lvl => isValidBounceDown(lvl, pBar));
                    if (pBounceUp && !priorGrsMid) {
                        priorGrsMid = (pBar.high + pBar.low) / 2.0;
                    }
                    if (pBounceDown && !priorResMid) {
                        priorResMid = (pBar.high + pBar.low) / 2.0;
                    }
                }
                const bouncedOffActualGrsMid = priorGrsMid ? isValidBounceUp(priorGrsMid, lastBar) : false;
                const bouncedOffActualResMid = priorResMid ? isValidBounceDown(priorResMid, lastBar) : false;

                // Final Bounce Flags used for Signals: Exclusively enters on the retest of the Power Candle Midpoint
                const bouncedOffGrsMid = bouncedOffActualGrsMid;
                const bouncedOffResMid = bouncedOffActualResMid;

                // Candle averages for Extreme Reversal
                const Wbarsback = Math.min(50, candles.length);
                const candleSlice = candles.slice(-Wbarsback);
                const WAverageCandle = candleSlice.reduce((acc, c) => acc + (c.high - c.low), 0) / Wbarsback;
                const WAverageBody = candleSlice.reduce((acc, c) => acc + Math.abs(c.close - c.open), 0) / Wbarsback;

                const O = lastBar.open;
                const C = lastBar.close;
                const H = lastBar.high;
                const L = lastBar.low;

                // 1. Extreme Reversal System (L02)
                const bodysize = 0.75;
                const bodymultiplier = 2.0;
                const prevRange = prevBar.high - prevBar.low;

                const Elongsig = GREEN1 &&
                    (prevBar.open - prevBar.close >= bodysize * prevRange) &&
                    (prevRange > WAverageCandle * bodymultiplier) &&
                    (prevBar.open - prevBar.close > WAverageBody) &&
                    (C > O);

                const Eshortsig = RED1 &&
                    (prevBar.close - prevBar.open >= bodysize * prevRange) &&
                    (prevRange > WAverageCandle * bodymultiplier) &&
                    (prevBar.close - prevBar.open > WAverageBody) &&
                    (O > C);

                const Elongsignal = pDemaSlope.rising && Elongsig;
                const Eshortsignal = pDemaSlope.falling && Eshortsig;

                // 2. Zone conditions and Missile (Lines 3033-3085)
                const bullConds = (mX === 'BIG MOVE') ||
                                  (mX.includes('TREND DAY') && mX.includes('DOUBLE DISTRIBUTION')) ||
                                  (dX === 'OUT OF RANGE OUT OF VALUE') ||
                                  (c1 === 'CONFIRMED BULLISH') ||
                                  (c1 === 'REJECTED BEARISH') ||
                                  (c1 === 'WATCH') ||
                                  (profile.REJECTEDBEARISH || (profile.CONFIRMEDBEARISH && lastBar.close > cpr.DTc) || (profile.REJECTEDBULLISH && lastBar.close > cpr.DTc) || (profile.REJECTEDBEARISH && lastBar.close > cpr.DTc));

                const bearConds = (mX === 'BIG MOVE') ||
                                  (mX.includes('TREND DAY') && mX.includes('DOUBLE DISTRIBUTION')) ||
                                  (dX === 'OUT OF RANGE OUT OF VALUE') ||
                                  (c1 === 'CONFIRMED BEARISH') ||
                                  (c1 === 'REJECTED BULLISH') ||
                                  (c1 === 'WATCH') ||
                                  (profile.REJECTEDBULLISH || (profile.CONFIRMEDBULLISH && lastBar.close < cpr.DBc) || (profile.REJECTEDBULLISH && lastBar.close < cpr.DBc) || (profile.REJECTEDBEARISH && lastBar.close < cpr.DBc));

                const RisingUP = bullConds;
                const FallingDOWN = bearConds;
                const RisingUp = (plus >= minus) && (fPivotPDEMAF >= fPivotPDEMAS) && bullConds;
                const FallingDown = (minus >= plus) && (fPivotPDEMAF <= fPivotPDEMAS) && bearConds;

                const R_up = RisingUp && C > O;
                const R_dn = FallingDown && C < O;

                const MissUP = (RisingUp || RisingUP) && C > O && (L < va.VAH && O > va.VAH && H > va.VAH && C > va.VAH);
                const MissDOWN = (FallingDown || FallingDOWN) && C < O && (H > va.VAL && O < va.VAL && L < va.VAL && C < va.VAL);

                const MissU = MissUP || (R_up && ((L < va.VAH && C > va.VAH) || (L < fMedEMA && C > fMedEMA) || (L < cpr.DP && C > cpr.DP)));
                const MissD = MissDOWN || (R_dn && ((H > va.VAL && C < va.VAL) || (H > fMedEMA && C < fMedEMA) || (H > cpr.DP && C < cpr.DP)));

                const RangingUp = (plus >= minus) && (fPivotPDEMAF >= fPivotPDEMAS) && (m0 >= m10) && isSidewaysDay;
                const RangingDown = (minus >= plus) && (fPivotPDEMAF <= fPivotPDEMAS) && (m0 <= m10) && isSidewaysDay;

                const BounceUp = (RangingUp && C > O) && ((L < va.VAL && C > va.VAL) || (L < cpr.DP && C > cpr.DP));
                const BounceDown = (RangingDown && C < O) && ((H > va.VAH && C < va.VAH) || (H > cpr.DP && C < cpr.DP));

                const CanBuy = (emaCanBuy && MissU) || (emaCanBuy && BounceUp);
                const CanSell = (emaCanSell && MissD) || (emaCanSell && BounceDown);

                const cleanTrendBullish = CanBuy ? true : CanSell ? false : RisingUp ? true : false;
                const cleanTrendBearish = CanSell ? true : CanBuy ? false : FallingDown ? true : false;

                const StepUp = (cleanTrendBullish || GREEN1) && bouncedOffGrsMid;
                const StepDn = (cleanTrendBearish || RED1) && bouncedOffResMid;

                const ScalpBuy = emaCanBuy && StepUp;
                const ScalpSell = emaCanSell && StepDn;

                // 3. Divergence Checks (Lines 3121-3148)
                const { regBullDiv, regBearDiv, hiddenBullishConfirmed, hiddenBearishConfirmed } = checkDivergences(candles, cpr, 6, plus, minus);

                // 4. Strategy Triggers (Lines 3139-3166 - Ungated per v4.0 mandate)
                const standardLightningBuy = (CanBuy && ScalpBuy);
                const standardLightningSell = (CanSell && ScalpSell);
                const LightningBuy = standardLightningBuy;
                const LightningSell = standardLightningSell;

                // Extreme Reversal strategies are exempt from dayAllowed and H4/L4 gating per v4.0 mandate
                const ExtremeReversalBuy = Elongsignal;
                const ExtremeReversalSell = Eshortsignal;

                // Divergence strategies are exempt from dayAllowed and H4/L4 gating (confirmed on candle close)
                // Version 3.0: Symmetrical DMI Directional Filter (Avoid Long D when minus > plus, avoid Short D when plus > minus)
                const DivergenceBuy = Boolean(regBullDiv) && !(minus > plus);
                const DivergenceSell = Boolean(regBearDiv) && !(plus > minus);

                // Version 3.0: Symmetrical DMI Directional Filter for Hidden Divergence (Avoid Long H when minus > plus, avoid Short H when plus > minus)
                const HiddenDivBuy = Boolean(hiddenBullishConfirmed) && !(minus > plus);
                const HiddenDivSell = Boolean(hiddenBearishConfirmed) && !(plus > minus);

                // Decoupled Missile & Scalp (Lines 3162-3166)
                const JustMissileBuy = CanBuy && !LightningBuy && !ExtremeReversalBuy && !DivergenceBuy && !HiddenDivBuy && longAllowed && dayAllowed;
                const JustMissileSell = CanSell && !LightningSell && !ExtremeReversalSell && !DivergenceSell && !HiddenDivSell && shortAllowed && dayAllowed;

                const JustScalpBuy = ScalpBuy && !LightningBuy && !ExtremeReversalBuy && !DivergenceBuy && !HiddenDivBuy && longAllowed && dayAllowed;
                const JustScalpSell = ScalpSell && !LightningSell && !ExtremeReversalSell && !DivergenceSell && !HiddenDivSell && shortAllowed && dayAllowed;

                // 5. Canonical Priority Selector
                let selectedSignal = null;
                if (LightningBuy) {
                    selectedSignal = { type: 'LONG LIGHTNING', trigger: 'Lightning Trigger', isLong: true };
                } else if (LightningSell) {
                    selectedSignal = { type: 'SHORT LIGHTNING', trigger: 'Lightning Trigger', isLong: false };
                } else if (ExtremeReversalBuy) {
                    selectedSignal = { type: 'LONG EXTREME REVERSAL', trigger: 'Extreme Reversal Trigger', isLong: true };
                } else if (ExtremeReversalSell) {
                    selectedSignal = { type: 'SHORT EXTREME REVERSAL', trigger: 'Extreme Reversal Trigger', isLong: false };
                } else if (DivergenceBuy) {
                    selectedSignal = { type: 'LONG DIVERGENCE', trigger: 'Divergence Trigger', isLong: true };
                } else if (DivergenceSell) {
                    selectedSignal = { type: 'SHORT DIVERGENCE', trigger: 'Divergence Trigger', isLong: false };
                } else if (HiddenDivBuy) {
                    selectedSignal = { type: 'LONG HIDDEN DIVERGENCE', trigger: 'Hidden Divergence Trigger', isLong: true };
                } else if (HiddenDivSell) {
                    selectedSignal = { type: 'SHORT HIDDEN DIVERGENCE', trigger: 'Hidden Divergence Trigger', isLong: false };
                } else if (JustMissileBuy) {
                    selectedSignal = { type: 'LONG MISSILE', trigger: 'Missile Breakout Trigger', isLong: true };
                } else if (JustMissileSell) {
                    selectedSignal = { type: 'SHORT MISSILE', trigger: 'Missile Breakout Trigger', isLong: false };
                } else if (JustScalpBuy) {
                    selectedSignal = { type: 'LONG SCALP', trigger: 'Scalp Trigger', isLong: true };
                } else if (JustScalpSell) {
                    selectedSignal = { type: 'SHORT SCALP', trigger: 'Scalp Trigger', isLong: false };
                }

                if (selectedSignal) {
                    const isLong = selectedSignal.isLong;
                    // Session midpoint (trendLine) matching Pine Script line 2492
                    const activeSessionCandles = todayCandles.length > 0 ? todayCandles : candles.slice(-8);
                    const sessionHighs = activeSessionCandles.map(c => c.high);
                    const sessionLows = activeSessionCandles.map(c => c.low);
                    const highestHigh = Math.max(...sessionHighs);
                    const lowestLow = Math.min(...sessionLows);
                    const trendLine = (highestHigh + lowestLow) / 2.0;

                    const entryPrice = Math.round(trendLine * 100) / 100;
                    const stopPrice = Math.round((isLong ? entryPrice - 0.75 * atr : entryPrice + 0.75 * atr) * 100) / 100;
                    const tp1Price = Math.round((isLong ? entryPrice + 2.5 * atr : entryPrice - 2.5 * atr) * 100) / 100;
                    const tp2Price = Math.round((isLong ? entryPrice + 4.0 * atr : entryPrice - 4.0 * atr) * 100) / 100;
                    const tp3Price = Math.round((isLong ? entryPrice + 6.5 * atr : entryPrice - 6.5 * atr) * 100) / 100;
                    const tp4Price = Math.round((isLong ? entryPrice + 8.0 * atr : entryPrice - 8.0 * atr) * 100) / 100;

                    const nowMs = Date.now();
                    const tradeId = `SCAN_${sym}_${nowMs}_${selectedSignal.type.replace(/\s+/g, '_')}`;
                    const entryDayStr = new Date(nowMs + 5.5 * 3600000).toISOString().substring(0, 10);
                    const entryDateTimeStr = new Date(nowMs).toISOString().replace('T', ' ').substring(0, 19);

                    // Confluence Qualification (Orthogonal Trend + Structural Divergence Confluence)
                    const isBullDivWindow = !!(regBullDiv || hiddenBullishConfirmed);
                    const isBearDivWindow = !!(regBearDiv || hiddenBearishConfirmed);
                    let isConfluence = false;
                    let confluenceType = null;

                    if (isLong && isBullDivWindow) {
                        if (selectedSignal.type.includes('MISSILE')) {
                            isConfluence = true;
                            confluenceType = 'MISSILE_DIV';
                        } else if (selectedSignal.type.includes('SCALP')) {
                            isConfluence = true;
                            confluenceType = 'SCALP_DIV';
                        } else if (selectedSignal.type.includes('LIGHTNING')) {
                            isConfluence = true;
                            confluenceType = 'LIGHTNING_TRIPLE';
                        }
                    } else if (!isLong && isBearDivWindow) {
                        if (selectedSignal.type.includes('MISSILE')) {
                            isConfluence = true;
                            confluenceType = 'MISSILE_DIV';
                        } else if (selectedSignal.type.includes('SCALP')) {
                            isConfluence = true;
                            confluenceType = 'SCALP_DIV';
                        } else if (selectedSignal.type.includes('LIGHTNING')) {
                            isConfluence = true;
                            confluenceType = 'LIGHTNING_TRIPLE';
                        }
                    }

                    signalsForSym.push({
                        symbol: sym,
                        type: selectedSignal.type,
                        trigger: selectedSignal.trigger,
                        entry: entryPrice,
                        stop: stopPrice,
                        target: tp1Price,
                        tp2: tp2Price,
                        tp3: tp3Price,
                        tp4: tp4Price,
                        status: 'ACTIVE LIMIT',
                        outcome: 'OPEN',
                        source: 'blackbox_dhan',
                        exchange: marketName,
                        signal_ts: nowIso,
                        metadata: {
                            trade_id: tradeId,
                            entry_date: entryDayStr,
                            entryDate: entryDateTimeStr,
                            entry_time: nowIso,
                            timeframe: '15m',
                            day_type: mX,
                            opening_bias: dX,
                            institutional_bias: c1,
                            zone: z1,
                            market_category: isCommodity ? 'MCX' : 'NIFTY',
                            source_feed: 'DhanHQ',
                            h4: cam.H4,
                            l4: cam.L4,
                            cpr: { pivot: cpr.DP, tc: cpr.DTc, bc: cpr.DBc },
                            dtc: cpr.DTc,
                            dbc: cpr.DBc,
                            prev_range: prevDayRange,
                            prev_high: d1.high,
                            prev_low: d1.low,
                            is_ncpr: cpr.isNarrow,
                            cpr_type: cpr.isNarrow ? 'NCPR' : 'NORMAL',
                            is_inside_cpr: Boolean(profile.isInsideCPR || (cpr.DTc < cpr.YTc && cpr.DBc > cpr.YBc)),
                            is_rejection_day: profile.isRejectionDay,
                            is_rejection: profile.isRejectionDay,
                            vah: va.VAH,
                            val: va.VAL,
                            va_width: Math.abs(va.VAH - va.VAL),
                            va_ratio: prevDayRange > 0 ? (Math.abs(va.VAH - va.VAL) / prevDayRange) * 100 : 0,
                            is_nva: prevDayRange > 0 ? (Math.abs(va.VAH - va.VAL) / prevDayRange) * 100 < 38.0 : false,
                            is_narrow_value: prevDayRange > 0 ? (Math.abs(va.VAH - va.VAL) / prevDayRange) * 100 < 38.0 : false,
                            c1: c1,
                            is_continuation: Boolean(c1 && c1.toUpperCase().includes('CONTINUATION')),
                            trend_line: trendLine,
                            highest_high: highestHigh,
                            lowest_low: lowestLow,
                            is_confluence: isConfluence,
                            confluence_type: confluenceType
                        }
                    });
                }

                return signalsForSym;
            } catch (err) {
                console.error(`[DhanScanner] Error scanning ${sym}:`, err.message);
                return null;
            }
        });

        const batchResults = await Promise.all(batchPromises);
        for (const res of batchResults) {
            if (res && res.length > 0) {
                detectedSignals.push(...res);
            }
        }

        // Throttle 300ms between batches to stay comfortably within DhanHQ rate limits
        if (i + BATCH_SIZE < targetSymbols.length) {
            await new Promise(r => setTimeout(r, 300));
        }
    }

    console.log(`[DhanScanner] Scan cycle detected ${detectedSignals.length} potential setups.`);

    // Upsert into Supabase shadow_signals
    const CANONICAL_TRIGGERS = new Set([
        'LONG MISSILE', 'SHORT MISSILE',
        'LONG LIGHTNING', 'SHORT LIGHTNING',
        'LONG SCALP', 'SHORT SCALP',
        'LONG DIVERGENCE', 'SHORT DIVERGENCE',
        'LONG HIDDEN DIVERGENCE', 'SHORT HIDDEN DIVERGENCE',
        'LONG EXTREME REVERSAL', 'SHORT EXTREME REVERSAL',
        'LONG VIRGIN CPR', 'SHORT VIRGIN CPR'
    ]);

    let insertedCount = 0;
    if (detectedSignals.length > 0) {
        for (const sig of detectedSignals) {
            if (!CANONICAL_TRIGGERS.has(sig.type) || sig.type.includes('BLUEPRINT') || sig.type.includes('SEQUENCE')) {
                console.warn(`[DhanScanner] Rejected non-canonical signal type: ${sig.type}`);
                continue;
            }
            try {
                const thirtyMinsAgo = new Date(Date.now() - 30 * 60000).toISOString();
                const { data: existing } = await supabase
                    .from('shadow_signals')
                    .select('id')
                    .eq('symbol', sig.symbol)
                    .eq('type', sig.type)
                    .gt('created_at', thirtyMinsAgo)
                    .limit(1);

                if (!existing || existing.length === 0) {
                    const { error: insErr } = await supabase.from('shadow_signals').insert(sig);
                    if (!insErr) {
                        insertedCount++;
                        console.log(`[DhanScanner] Synced signal to shadow_signals: ${sig.symbol} (${sig.type}) @ ₹${sig.entry}`);
                    }
                }
            } catch (dbErr) {
                console.error('[DhanScanner] DB sync error:', dbErr.message);
            }
        }
    }

    // Persist screener snapshot to system_config under key 'dhan_screener_snapshot'
    if (screenerCandidates.length > 0 && supabase) {
        try {
            await supabase.from('system_config').upsert({
                key: 'dhan_screener_snapshot',
                value: screenerCandidates,
                updated_at: new Date().toISOString()
            }, { onConflict: 'key' });
            console.log(`[DhanScanner] Persisted ${screenerCandidates.length} candidate setups to system_config (dhan_screener_snapshot).`);
        } catch (snapErr) {
            console.error('[DhanScanner] Screener snapshot error:', snapErr.message);
        }

        // Also upsert watchlist candidate rows to shadow_signals if no active trade order exists
        for (const cand of screenerCandidates) {
            try {
                const todayIsoStart = new Date(new Date().setHours(0, 0, 0, 0)).toISOString();
                const { data: activeTrade } = await supabase
                    .from('shadow_signals')
                    .select('id, metadata, status')
                    .eq('symbol', cand.symbol)
                    .neq('status', 'WATCHLIST')
                    .gte('created_at', todayIsoStart)
                    .limit(1);

                if (activeTrade && activeTrade.length > 0) {
                    // Symbol has an active trade today, merge screener metadata without disturbing trade
                    const mergedMeta = { ...(activeTrade[0].metadata || {}), ...cand.metadata };
                    await supabase.from('shadow_signals').update({ metadata: mergedMeta }).eq('id', activeTrade[0].id);
                } else {
                    // Check if watchlist row already exists today
                    const { data: existingWl } = await supabase
                        .from('shadow_signals')
                        .select('id')
                        .eq('symbol', cand.symbol)
                        .eq('status', 'WATCHLIST')
                        .gte('created_at', todayIsoStart)
                        .limit(1);

                    if (existingWl && existingWl.length > 0) {
                        await supabase.from('shadow_signals').update({
                            metadata: cand.metadata,
                            entry: cand.entry,
                            signal_ts: cand.signal_ts
                        }).eq('id', existingWl[0].id);
                    } else {
                        await supabase.from('shadow_signals').insert(cand);
                    }
                }
            } catch (candDbErr) {
                console.error(`[DhanScanner] Watchlist candidate sync error for ${cand.symbol}:`, candDbErr.message);
            }
        }
    }

    // Autonomous Watchdog Sweep: Purge any non-canonical blueprint rows
    try {
        await supabase.from('shadow_signals').delete().or('type.ilike.%BLUEPRINT%,type.ilike.%SEQUENCE%');
    } catch (ePurge) {}

    // Autonomous F&O Buildup Sweep: Keep F&O stocks and EOD snapshot fresh in Supabase
    try {
        const { sweepFnoEodSnapshot } = require('./cron-eod-close.js');
        await sweepFnoEodSnapshot(true);
    } catch (eFnoSweep) {
        console.warn('[DhanScanner] F&O Buildup sweep warning:', eFnoSweep?.message || eFnoSweep);
    }

    console.log(`[DhanScanner] Completed cycle. Synced ${insertedCount} new signals to shadow_signals.`);
    return {
        message: 'Scan completed successfully',
        detected: detectedSignals.length,
        inserted: insertedCount
    };
}

// Netlify Background Function Handler
exports.handler = async function(event, context) {
    console.log('[DhanScanner Background] Invocation received.');

    const internalSecret = event.headers['x-internal-secret'] || event.headers['x-webhook-secret'] || '';
    const configuredSecret = process.env.INTERNAL_CRON_SECRET || process.env.WEBHOOK_SECRET || '';
    
    let isAuthorized = Boolean(configuredSecret && internalSecret === configuredSecret);

    if (!isAuthorized) {
        // Check Supabase Bearer Auth for Admin
        const authHeader = event.headers.authorization || event.headers.Authorization || '';
        const token = authHeader.replace('Bearer ', '').trim();
        if (token && process.env.SUPABASE_URL && (process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_SERVICE_KEY)) {
            try {
                const { createClient } = require('@supabase/supabase-js');
                const adminClient = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_SERVICE_KEY);
                const { data: { user } } = await adminClient.auth.getUser(token);
                if (user && user.email) {
                    const APPROVED_ADMIN_EMAILS = [
                        'owner@tlcs.com',
                        'vishantmeshram@gmail.com',
                        'thelioncapitaladvisors@gmail.com',
                        'connect@thelioncapitalsolutions.com'
                    ];
                    if (APPROVED_ADMIN_EMAILS.includes(user.email.toLowerCase().trim())) {
                        isAuthorized = true;
                    }
                }
            } catch (e) {}
        }
    }

    if (!isAuthorized) {
        return {
            statusCode: 401,
            body: JSON.stringify({ error: 'Unauthorized: Internal secret or admin auth required' })
        };
    }

    let limit = null;
    if (event.queryStringParameters && event.queryStringParameters.limit) {
        limit = parseInt(event.queryStringParameters.limit, 10);
    }

    try {
        const result = await runDhanScan(limit);
        return {
            statusCode: 200,
            body: JSON.stringify(result)
        };
    } catch (e) {
        console.error('[DhanScanner Background] Fatal execution error:', e);
        return {
            statusCode: 500,
            body: JSON.stringify({ error: e.message })
        };
    }
};

module.exports.runDhanScan = runDhanScan;
module.exports.sweepMarketCloseExits = sweepMarketCloseExits;
module.exports.processOpenTradesAndFills = processOpenTradesAndFills;
