import { NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabaseServer';
import crypto from 'crypto';
import { nymexToMcxMap, getActiveMcxSecurityId, getActiveOptionSecurityId, getLivePrice, placeLimitOrder, placeMarketOrder } from '@/lib/dhan';
export const dynamic = 'force-dynamic';


// VAPT: Webhook authentication secret — stored ONLY in server-side env vars
const WEBHOOK_SECRET = process.env.WEBHOOK_SECRET || '';

// ── Telegram Notification Dispatcher ─────────────────────────────────────────
function getMarketForSymbol(symbol?: string): string | null {
  if (!symbol) return null;
  const clean = symbol.toString().toUpperCase().replace(/^.*:/, '').replace(/1!$/, '').replace(/!$/, '').trim();
  
  const nifty = ['ADANIENT', 'ADANIPORTS', 'APOLLOHOSP', 'ASIANPAINT', 'AXISBANK', 'BAJAJ-AUTO', 'BAJAJFINSV', 'BAJFINANCE', 'BHARTIARTL', 'BPCL', 'BRITANNIA', 'CIPLA', 'COALINDIA', 'DIVISLAB', 'DRREDDY', 'EICHERMOT', 'GRASIM', 'HCLTECH', 'HDFCBANK', 'HDFCLIFE', 'HEROMOTOCO', 'HINDALCO', 'HINDUNILVR', 'ICICIBANK', 'INDUSINDBK', 'INFY', 'ITC', 'JSWSTEEL', 'KOTAKBANK', 'LT', 'LTIMINDTREE', 'M&M', 'MARUTI', 'NESTLEIND', 'NTPC', 'ONGC', 'POWERGRID', 'RELIANCE', 'SBILIFE', 'SBIN', 'SHRIRAMFIN', 'SUNPHARMA', 'TATACONSUM', 'TATAMOTORS', 'TATASTEEL', 'TCS', 'TECHM', 'TITAN', 'ULTRACEMCO', 'WIPRO'];
  const mcx = ['ALUMINIUM', 'ALUMINIUMM', 'COPPER', 'COTTON', 'CRUDEOIL', 'CRUDEOILM', 'GOLD', 'GOLDM', 'GOLDPETAL', 'LEAD', 'LEADMINI', 'MENTHAOIL', 'NATURALGAS', 'NATURALGASM', 'NICKEL', 'NICKELMINI', 'SILVER', 'SILVERM', 'SILVERMIC', 'ZINC', 'ZINCMINI'];
  const nymex = ['CL', 'GC', 'HG', 'HO', 'NG', 'PA', 'PL', 'RB', 'SI'];
  const crypto = ['ADAUSDT', 'APTUSDT', 'ARBUSDT', 'ATOMUSDT', 'AVAXUSDT', 'BCHUSDT', 'BNBUSDT', 'BTCUSDT', 'DOGEUSDT', 'DOTUSDT', 'ETHUSDT', 'FILUSDT', 'ICPUSDT', 'LINKUSDT', 'LTCUSDT', 'NEARUSDT', 'POLUSDT', 'SHIBUSDT', 'SOLUSDT', 'STXUSDT', 'TONUSDT', 'TRXUSDT', 'UNIUSDT', 'XLMUSDT', 'XRPUSDT'];
  const forex = ['AUDCAD', 'AUDINR', 'AUDJPY', 'AUDNZD', 'AUDUSD', 'CADJPY', 'EURAUD', 'EURCAD', 'EURCHF', 'EURGBP', 'EURINR', 'EURJPY', 'EURUSD', 'GBPAUD', 'GBPCAD', 'GBPCHF', 'GBPINR', 'GBPJPY', 'GBPUSD', 'JPYINR', 'NZDUSD', 'USDCAD', 'USDCHF', 'USDINR', 'USDJPY'];
  const world = ['AU200', 'DE40', 'EU50', 'FR40', 'HK50', 'JP225', 'NAS100', 'SPX500', 'UK100', 'US2000', 'US30'];

  if (nifty.includes(clean) || clean.includes('GIFTNIFTY') || clean.includes('GIFT NIFTY')) return 'nifty';
  if (mcx.includes(clean)) return 'mcx';
  if (nymex.includes(clean)) return 'nymex';
  if (crypto.includes(clean)) return 'crypto';
  if (forex.includes(clean)) return 'forex';
  if (world.includes(clean)) return 'world';

  return null;
}

async function sendTelegramAlert(msgText: string, symbol?: string, isFireAlert?: boolean) {
  const market = getMarketForSymbol(symbol);
  if (symbol && !market && !isFireAlert) {
    console.log(`[Telegram Dispatcher] Skipped ${symbol}: Market not found.`);
    return;
  }
  const telegramBotToken = process.env.TELEGRAM_BOT_TOKEN;
  if (!telegramBotToken) {
    console.log('[Telegram Dispatcher] Skipped: TELEGRAM_BOT_TOKEN not set in env.');
    return;
  }

  // Resolve chat IDs: Market channel + Dedicated Fire Alert channel if configured
  const chatIds = new Set<string>();
  const marketChatId = (market ? process.env[`TELEGRAM_CHAT_ID_${market.toUpperCase()}`] : null) || process.env.TELEGRAM_CHAT_ID || '-1001555378566';
  if (marketChatId) chatIds.add(marketChatId);

  if (isFireAlert) {
    const fireChatId = process.env.TELEGRAM_CHAT_ID_FIRE || process.env.TELEGRAM_CHAT_ID_FIRE_ALERT;
    if (fireChatId) chatIds.add(fireChatId);
  }

  let htmlMsg = msgText
    .replace(/\*(.*?)\*/g, '<b>$1</b>')
    .replace(/`(.*?)`/g, '<code>$1</code>');

  for (const chatId of Array.from(chatIds)) {
    try {
      const res = await fetch(`https://api.telegram.org/bot${telegramBotToken}/sendMessage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          chat_id: chatId,
          text: htmlMsg,
          parse_mode: 'HTML'
        }),
        signal: AbortSignal.timeout(4000)
      });
      const data = await res.json();
      if (!data.ok) {
        console.error(`[Telegram Dispatch Failed] (${chatId})`, data.description);
      } else {
        console.log(`[Telegram Dispatch Success] Alert sent to Telegram channel ${chatId}.`);
      }
    } catch (e: any) {
      console.error(`[Telegram Dispatch Error] (${chatId})`, e.message);
    }
  }
}



// ── Market Hours Guard (RCA Fix: After-Hours Signal Prevention) ─────────────
// RCA: FINNIFTY and other NSE/NFO signals were firing after market close because
// TradingView replays historical bars / fires alerts on higher-timeframe bar closes
// even after 3:30 PM IST. This guard permanently prevents after-hours signals.
//
// Only NSE/BSE and MCX symbols are guarded. Crypto, Forex, and world indices are 24/7.
// TradeClose, PivotUpdate, and TrailingSLUpdate are ALWAYS accepted (outcome updates).
function isNSESymbol(symbol: string, exchange: string | null): boolean {
  const sym  = (symbol   || '').toUpperCase();
  const exch = (exchange || '').toUpperCase();
  if (['NSE', 'BSE', 'NFO', 'INDEX'].includes(exch)) return true;
  if (/^(NIFTY|BANKNIFTY|FINNIFTY|MIDCPNIFTY|SENSEX)/.test(sym)) return true;
  return false;
}

function isMCXSymbol(symbol: string, exchange: string | null): boolean {
  const sym  = (symbol   || '').toUpperCase().replace(/^.*:/, '').replace(/1!$/, '').replace(/!$/, '').trim();
  const exch = (exchange || '').toUpperCase();
  if (exch === 'MCX') return true;
  const mcxList = ['ALUMINIUM', 'ALUMINIUMM', 'COPPER', 'COTTON', 'CRUDEOIL', 'CRUDEOILM', 'GOLD', 'GOLDM', 'GOLDPETAL', 'LEAD', 'LEADMINI', 'MENTHAOIL', 'NATURALGAS', 'NATURALGASM', 'NICKEL', 'NICKELMINI', 'SILVER', 'SILVERM', 'SILVERMIC', 'ZINC', 'ZINCMINI'];
  return mcxList.includes(sym);
}

function is24x7Symbol(symbol: string, exchange: string | null): boolean {
  const sym  = (symbol   || '').toUpperCase();
  const exch = (exchange || '').toUpperCase();
  if (sym.includes('GIFTNIFTY') || sym.includes('GIFT NIFTY')) return true;
  if (sym.endsWith('USDT') || sym.endsWith('BTC') || sym.endsWith('ETH')) return true;
  if (['BINANCE', 'COINBASE', 'CRYPTO'].includes(exch)) return true;
  if (['FX_IDC', 'FX', 'OANDA', 'FXCM'].includes(exch)) return true;
  if (sym.length === 6 && /^[A-Z]{6}$/.test(sym)) return true; // forex pairs
  const worldIdx = ['UKX','HSI','NI225','DAX','CAC40','SX5E','DJI','SPX','NDX','RUT','XJO'];
  if (worldIdx.includes(sym)) return true;
  // NYMEX base/continuous futures (GC, SI, CL, NG, GC1!, etc.) — global, not NSE
  const nymexBaseList = ['GC','SI','CL','NG','HG','PL','PA','RB','HO'];
  if (nymexBaseList.includes(sym)) return true;
  // NYMEX continuous futures (GC1!, CL1!, NG1! …) — not NSE-bound
  if (/^[A-Z]{2}1!$/.test(sym) && !sym.startsWith('NIFTY') && !sym.startsWith('BANK') && !sym.startsWith('FINN')) return true;
  return false;
}

function isWithinNSEMarketHours(signalTsMs: number): boolean {
  const dt = new Date(signalTsMs);
  if (isNaN(dt.getTime())) return false;
  // Convert UTC → IST (UTC+5:30)
  const IST_OFFSET_MS = (5 * 60 + 30) * 60 * 1000;
  const ist = new Date(dt.getTime() + IST_OFFSET_MS);
  const dayOfWeek  = ist.getUTCDay();    // 0=Sun … 6=Sat
  const timeInMins = ist.getUTCHours() * 60 + ist.getUTCMinutes();
  // NSE: 9:15 AM – 3:30 PM spot, 3:45 PM derivatives settlement
  const NSE_OPEN  = 9  * 60 + 15;  // 555
  const NSE_CLOSE = 15 * 60 + 45;  // 945  (includes 15-min derivatives buffer)
  const isWeekday = dayOfWeek >= 1 && dayOfWeek <= 5;
  return isWeekday && timeInMins >= NSE_OPEN && timeInMins <= NSE_CLOSE;
}

function isWithinMCXMarketHours(signalTsMs: number): boolean {
  const dt = new Date(signalTsMs);
  if (isNaN(dt.getTime())) return false;
  // Convert UTC → IST (UTC+5:30)
  const IST_OFFSET_MS = (5 * 60 + 30) * 60 * 1000;
  const ist = new Date(dt.getTime() + IST_OFFSET_MS);
  const dayOfWeek  = ist.getUTCDay();    // 0=Sun … 6=Sat
  const timeInMins = ist.getUTCHours() * 60 + ist.getUTCMinutes();
  // MCX: 9:00 AM – 11:30 PM (or 11:55 PM US daylight saving)
  const MCX_OPEN  = 9  * 60;       // 540 (09:00 AM)
  const MCX_CLOSE = 23 * 60 + 55;  // 1435 (11:55 PM)
  const isWeekday = dayOfWeek >= 1 && dayOfWeek <= 5;
  return isWeekday && timeInMins >= MCX_OPEN && timeInMins <= MCX_CLOSE;
}

// SECURITY: Allowed origins for CORS
const ALLOWED_ORIGINS = [
  'https://thelioncapitalsolutions.com',
  'https://market-store.online',
  'https://www.thelioncapitalsolutions.com',
];

function getCorsHeaders(req: Request) {
  const origin = req.headers.get('origin') || '';
  const allowedOrigin = ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0];
  return {
    'Access-Control-Allow-Origin': allowedOrigin,
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, X-Webhook-Secret, Authorization',
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'Cache-Control': 'no-store, no-cache, must-revalidate',
  };
}

// VAPT: In-memory rate limiter — 30 requests per minute per IP
const rateLimitMap = new Map<string, { count: number; resetAt: number }>();
const RATE_LIMIT = 60;
const RATE_WINDOW_MS = 60_000;

function isRateLimited(ip: string): boolean {
  const now = Date.now();
  const entry = rateLimitMap.get(ip);
  
  if (!entry || now > entry.resetAt) {
    rateLimitMap.set(ip, { count: 1, resetAt: now + RATE_WINDOW_MS });
    return false;
  }
  
  entry.count++;
  if (entry.count > RATE_LIMIT) return true;
  return false;
}

// SECURITY: Scrub sensitive fields from metadata before storage
function scrubSecrets(payload: any): any {
  if (!payload || typeof payload !== 'object') return payload;
  const scrubbed = { ...payload };
  const sensitiveKeys = ['secret', 'webhook_secret', 'api_key', 'password', 'token', 'authorization'];
  for (const key of sensitiveKeys) {
    if (key in scrubbed) delete scrubbed[key];
    // Also check case-insensitive
    const lowerKeys = Object.keys(scrubbed).filter(k => k.toLowerCase() === key.toLowerCase());
    lowerKeys.forEach(k => delete scrubbed[k]);
  }
  return scrubbed;
}

function validateSecret(provided: string): boolean {
  if (!provided) return false;
  const expectedSecret = WEBHOOK_SECRET || process.env.INTERNAL_CRON_SECRET || '';
  if (!expectedSecret) return false;
  
  try {
    const a = Buffer.from(provided.trim(), 'utf8');
    const b = Buffer.from(expectedSecret.trim(), 'utf8');
    if (a.length === b.length && crypto.timingSafeEqual(a, b)) return true;
    return false;
  } catch {
    return false;
  }
}

function cleanBiasOrDayType(val: any): string | null {
  if (val === undefined || val === null) return null;
  let s = String(val).toUpperCase();
  s = s.replace(/\\N/gi, ' ')
       .replace(/[\r\n]+/g, ' ')
       .replace(/\s+/g, ' ')
       .replace(/DOUBLE DISTRIBUTION/g, 'DD')
       .trim();
  s = s.split(',')
       .map(p => p.trim())
       .filter(Boolean)
       .join(', ');
  return s || null;
}

// ── Symbol + Exchange Resolver ──────────────────────────────────────────────────
// Pine screeners omit the "exchange" field — they only send
// "symbol": "BINANCE:BTCUSDT" or "BTCUSDT". This helper:
//   1. Extracts the exchange prefix embedded in the symbol.
//   2. Falls back to symbol-name pattern matching.
// Returns { symbol, exchange } both as clean uppercase strings.
function resolveSymbolAndExchange(rawSymbol: string, providedExchange?: string): { symbol: string; exchange: string | null } {
  let sym      = (rawSymbol       || '').trim();
  let exchange = (providedExchange || '').trim().toUpperCase();

  // 1. Strip embedded prefix (e.g. "BINANCE:BTCUSDT" → sym="BTCUSDT", exchange="BINANCE")
  const colonIdx = sym.indexOf(':');
  if (colonIdx !== -1) {
    const prefix = sym.substring(0, colonIdx).toUpperCase();
    sym = sym.substring(colonIdx + 1);
    if (!exchange) exchange = prefix;
  }
  sym = sym.toUpperCase();

  // 2. Infer exchange from symbol name when still unknown
  if (!exchange) {
    const cryptoList = ['BTCUSDT','ETHUSDT','BNBUSDT','SOLUSDT','XRPUSDT','DOGEUSDT','ADAUSDT',
      'AVAXUSDT','TRXUSDT','TONUSDT','SHIBUSDT','DOTUSDT','LINKUSDT','MATICUSDT','POLUSDT',
      'LTCUSDT','BCHUSDT','NEARUSDT','UNIUSDT','APTUSDT','XLMUSDT','ATOMUSDT','ICPUSDT',
      'STXUSDT','FILUSDT','ARBUSDT'];
    const forexList = ['EURUSD','GBPUSD','USDJPY','USDCHF','AUDUSD','USDCAD','NZDUSD',
      'EURGBP','EURJPY','EURAUD','EURCHF','EURCAD','GBPJPY','GBPAUD','GBPCAD','GBPCHF',
      'AUDJPY','AUDCAD','AUDNZD','CADJPY','USDINR','EURINR','GBPINR','JPYINR','AUDINR'];
    const mcxList   = ['GOLD','GOLDM','GOLDPETAL','SILVER','SILVERM','SILVERMIC',
      'CRUDEOIL','CRUDEOILM','NATURALGAS','NATURALGASM','COPPER','ZINC','ZINCMINI',
      'NICKEL','NICKELMINI','LEAD','LEADMINI','ALUMINIUM','ALUMINIUMM','COTTON','MENTHAOIL'];
    const nymexList = ['GC1!','SI1!','CL1!','NG1!','HG1!','PL1!','PA1!','RB1!','HO1!','GC','SI','CL','NG','HG','PL','PA','RB','HO'];
    const worldIdx  = ['XJO','NI225','HSI','NIFTY','UKX','DAX','CAC40','SX5E','DJI','SPX','NDX','RUT'];
    const nse50     = ['RELIANCE','TCS','HDFCBANK','INFY','ICICIBANK','HINDUNILVR','ITC','SBIN',
      'BHARTIARTL','KOTAKBANK','LT','AXISBANK','HCLTECH','ASIANPAINT','MARUTI','GRASIM','CIPLA','DRREDDY','EICHERMOT','HEROMOTOCO','HINDALCO','INDUSINDBK','JSWSTEEL','M&M','NTPC','ONGC','POWERGRID','SUNPHARMA','TATACONSUM','TATAMOTORS','TATASTEEL','TECHM','TITAN','ULTRACEMCO','WIPRO'];

    if (cryptoList.includes(sym) || sym.endsWith('USDT') || sym.endsWith('BTC') || sym.endsWith('ETH')) {
      exchange = 'BINANCE';
    } else if (forexList.includes(sym) || (sym.length === 6 && /^[A-Z]{6}$/.test(sym) && !nse50.includes(sym))) {
      exchange = 'FX_IDC';
    } else if (nymexList.includes(sym)) {
      exchange = 'NYMEX';
    } else if (mcxList.includes(sym)) {
      exchange = 'MCX';
    } else if (worldIdx.includes(sym)) {
      exchange = 'INDEX';
    } else if (nse50.includes(sym)) {
      exchange = 'NSE';
    }
  }

  return { symbol: sym || rawSymbol, exchange: exchange || null };
}

function getMarketTz(sym: string, exch?: string | null): string {
  if (!sym) return 'America/New_York';
  const s = String(sym).toUpperCase();
  const e = (exch || '').toUpperCase();
  if (s.includes('NIFTY') || s.endsWith('.NS') || s.endsWith('.BO') || ['ITC', 'SBIN', 'RELIANCE', 'TCS', 'HDFCBANK', 'INFY'].includes(s)) return 'Asia/Kolkata';
  if (['GOLD', 'CRUDEOIL', 'CRUDEOIL1!', 'NATURALGAS1!', 'NATURALGAS', 'SILVER', 'SILVERM', 'GOLDM', 'COPPER', 'ZINC', 'ALUMINI', 'ALUMINIUM'].includes(s)) return 'Asia/Kolkata';
  if (e === 'NSE' || e === 'MCX' || e === 'BSE' || e === 'NFO') return 'Asia/Kolkata';
  return 'America/New_York';
}

function getTzDateStr(ms: number, tz?: string): string {
  const formatter = new Intl.DateTimeFormat('en-US', { timeZone: tz || 'Asia/Kolkata', year: 'numeric', month: '2-digit', day: '2-digit' });
  const parts = formatter.formatToParts(new Date(ms));
  const yr = parts.find(p => p.type === 'year')?.value;
  const mo = parts.find(p => p.type === 'month')?.value;
  const da = parts.find(p => p.type === 'day')?.value;
  return `${yr}-${mo}-${da}`;
}

export async function OPTIONS(req: Request) {
  return new NextResponse(null, { status: 204, headers: getCorsHeaders(req) });
}

export async function POST(req: Request) {
  const clientIP = req.headers.get('x-forwarded-for')?.split(',')[0]?.trim() || 'unknown';
  const CORS = getCorsHeaders(req);
  
  // VAPT: Rate limiting
  if (isRateLimited(clientIP)) {
    console.warn(`[SIEM][RATE_LIMIT] IP ${clientIP.substring(0, 8)}... exceeded rate limit`);
    return NextResponse.json(
      { success: false, error: 'Rate limit exceeded. Try again later.' },
      { status: 429, headers: CORS }
    );
  }

  let rawBody = '';
  try {
    rawBody = await req.text();
    
    // SECURITY: Reject oversized payloads (max 10KB)
    if (rawBody.length > 10240) {
      console.warn(`[SIEM][PAYLOAD_OVERFLOW] Payload size: ${rawBody.length} bytes from ${clientIP.substring(0, 8)}...`);
      return NextResponse.json(
        { success: false, error: 'Payload too large.' },
        { status: 413, headers: CORS }
      );
    }

    const url = new URL(req.url);

    let cleanBody = rawBody;
    
    // SECURITY & ROBUSTNESS: Clean TradingView webhook payload
    // TradingView sometimes appends plain text to the end of alerts (e.g. "#Antigravity Alerts# ...")
    // or formats strings with literal newlines which breaks JSON.parse().
    const trimmedClean = cleanBody.trim();
    const firstBrace = cleanBody.indexOf('{');
    const lastBrace = cleanBody.lastIndexOf('}');
    if (firstBrace !== -1 && lastBrace !== -1 && lastBrace >= firstBrace) {
      cleanBody = cleanBody.substring(firstBrace, lastBrace + 1);
    } else if (trimmedClean.startsWith('[') && trimmedClean.endsWith(']')) {
      const firstArr = cleanBody.indexOf('[');
      const lastArr = cleanBody.lastIndexOf(']');
      if (firstArr !== -1 && lastArr !== -1 && lastArr >= firstArr) {
        cleanBody = cleanBody.substring(firstArr, lastArr + 1);
      }
    }
    // Replace all literal newlines and carriage returns with spaces
    cleanBody = cleanBody.replace(/[\n\r]+/g, ' ');
    
    // Pine Script's str.tostring(na) outputs unquoted NaN, which is invalid JSON.
    cleanBody = cleanBody.replace(/:\s*NaN/g, ': null');

    // VAPT: Authenticate webhook requests
    let bodyPayload: any = null;
    try { bodyPayload = JSON.parse(cleanBody); } catch(e) { /* parsed later */ }
    
    // Check for secret in headers, query params, or body
    const authToken = req.headers.get('x-webhook-secret') 
      || req.headers.get('authorization')?.replace('Bearer ', '')
      || url.searchParams.get('secret')
      || bodyPayload?.secret;

    const isValidAuth = validateSecret(authToken || '');
      
    if (!isValidAuth) {
      console.warn(`[SIEM][WEBHOOK_DENIED] Unauthorized attempt from ${clientIP.substring(0, 8)}...`);
      return NextResponse.json(
        { success: false, error: 'Unauthorized' },
        { status: 401, headers: CORS }
      );
    }

    let payload: any;
    try {
      payload = JSON.parse(cleanBody);
    } catch (e: any) {
      // ── DEFENSIVE PARSER: TradingView Plain-Text VCPR / Signal Alert ──
      const rawText = cleanBody.toUpperCase();
      if (rawText.includes('VCPR') || rawText.includes('VIRGIN CPR') || rawText.includes('VIRGIN')) {
        let extractedSym = 'UNKNOWN';
        const alertMatch = cleanBody.match(/\[VCPR Alert\]\s+([A-Z0-9_\-&!:]+)/i);
        const bracketMatch = cleanBody.match(/\[([A-Z0-9_\-&!:]+)(?:\s|\()/i);
        if (alertMatch && alertMatch[1]) {
          extractedSym = alertMatch[1].trim();
        } else if (bracketMatch && bracketMatch[1] && !bracketMatch[1].toUpperCase().includes('VCPR') && !bracketMatch[1].toUpperCase().includes('ALERT')) {
          extractedSym = bracketMatch[1].trim();
        } else {
          const symWordMatch = cleanBody.match(/\b([A-Z0-9_\-&!]{2,15}(?:1!)?)\b/);
          if (symWordMatch) extractedSym = symWordMatch[1].trim();
        }

        const isBull = rawText.includes('BULLISH') || rawText.includes('SUPPORT') || rawText.includes('BOUNCE') || rawText.includes('BUY') || rawText.includes('LONG');
        const priceMatch = cleanBody.match(/(?:Touch Price|Price|at|close)[:\s]+([0-9]+(?:\.[0-9]+)?)/i);
        const extractedPrice = priceMatch ? Number(priceMatch[1]) : 0;
        
        const dateMatch = cleanBody.match(/VCPR Dated\s+([0-9]{1,2}-[A-Za-z]{3}-[0-9]{4})/i) || cleanBody.match(/([0-9]{1,2}-[A-Za-z]{3}-[0-9]{4})/);
        const extractedDate = dateMatch ? dateMatch[1] : null;

        const zoneMatch = cleanBody.match(/Zone:\s*\[\s*([0-9.]+)\s*-\s*([0-9.]+)\s*\]/i);
        const zBottom = zoneMatch ? Number(zoneMatch[1]) : null;
        const zTop = zoneMatch ? Number(zoneMatch[2]) : null;

        const tf = rawText.includes('WEEKLY') ? 'W' : rawText.includes('MONTHLY') ? 'M' : rawText.includes('YEARLY') ? 'Y' : 'D';

        payload = {
          symbol: extractedSym,
          ticker: extractedSym,
          type: isBull ? 'LONG VIRGIN CPR' : 'SHORT VIRGIN CPR',
          action: isBull ? 'buy' : 'sell',
          price: extractedPrice,
          entry: extractedPrice,
          touch_price: extractedPrice,
          trigger: isBull ? 'LONG VIRGIN CPR' : 'SHORT VIRGIN CPR',
          status: 'ACTIVE',
          analysis: cleanBody.trim(),
          metadata: {
            is_vcpr: true,
            is_vcpr_touch: true,
            setup_family: 'VIRGIN_CPR',
            signal_family: 'VIRGIN_CPR',
            vcpr_date: extractedDate,
            vcpr_touch_date: extractedDate,
            vcpr_touch_price: extractedPrice,
            vcpr_top: zTop,
            vcpr_bottom: zBottom,
            vcpr_timeframe: tf,
            vcpr_direction: isBull ? 'BULLISH' : 'BEARISH',
            source_feed: 'TradingView_VCPR'
          }
        };
      } else if (rawText.includes('DIVERGENCE') || rawText.startsWith('ALERT :') || rawText.startsWith('ALERT:')) {
        let extractedSym = 'UNKNOWN';
        const bracketMatch = cleanBody.match(/\[([A-Z0-9_\-&!:]+)\]/i);
        const headerSymMatch = req.headers.get('x-symbol') || req.headers.get('symbol');
        if (headerSymMatch) {
          extractedSym = headerSymMatch.trim();
        } else if (bracketMatch && bracketMatch[1]) {
          extractedSym = bracketMatch[1].trim();
        } else {
          // Look for MCX / NYMEX / NSE symbols in query or text
          const symWordMatch = cleanBody.match(/\b(CRUDEOIL|NATURALGAS|GOLD|SILVER|COPPER|ZINC|ALUMINIUM|NG|CL|GC|SI|NIFTY|BANKNIFTY)(?:1!)?\b/i) || cleanBody.match(/\b([A-Z0-9_\-&!]{2,15}(?:1!)?)\b/);
          if (symWordMatch) extractedSym = symWordMatch[1].trim();
        }

        const isBull = rawText.includes('BULLISH') || rawText.includes('BUY') || rawText.includes('LONG');
        const priceMatch = cleanBody.match(/Price\s*:\s*([0-9]+(?:\.[0-9]+)?)/i) || cleanBody.match(/(?:at|close)[:\s]+([0-9]+(?:\.[0-9]+)?)/i);
        const extractedPrice = priceMatch ? Number(priceMatch[1]) : 0;

        payload = {
          symbol: extractedSym,
          ticker: extractedSym,
          type: isBull ? 'LONG DIVERGENCE' : 'SHORT DIVERGENCE',
          action: isBull ? 'buy' : 'sell',
          price: extractedPrice,
          entry: extractedPrice,
          trigger: isBull ? 'LONG DIVERGENCE' : 'SHORT DIVERGENCE',
          status: 'ACTIVE',
          analysis: cleanBody.trim(),
          metadata: {
            is_confluence: false,
            signal_family: 'DIVERGENCE',
            setup_family: 'DIVERGENCE',
            has_divergence_confluence: true,
            source_feed: 'TradingView_Divergence'
          }
        };
      } else {
        console.error(`[SIEM][JSON_PARSE_ERROR] Error: ${e.message} | Payload: ${cleanBody}`);
        return NextResponse.json(
          { success: false, error: 'Invalid JSON format.' },
          { status: 400, headers: CORS }
        );
      }
    }

    // Initialize Supabase Admin Client (Stateless)
    const supabase = supabaseAdmin;
    
    // Normalize symbol: strip exchange prefix (e.g. "NSE:NIFTY" → "NIFTY", "COMEX:XAUUSD" → "XAUUSD")
    const rawSymbol = payload.symbol || payload.ticker || 'UNKNOWN';
    const symbol = rawSymbol.includes(':') ? rawSymbol.split(':').pop()! : rawSymbol;

    // ── Guard: Discard test/debug symbols from polluting production DB ──
    const checkSym = symbol.toUpperCase().trim();
    if (checkSym.startsWith('DEBUG_') || checkSym === 'TEST' || checkSym === 'TEST_SCRIPT' || checkSym === 'PING') {
      console.log(`[Webhook Route] Ignored test/debug symbol: ${checkSym}`);
      return NextResponse.json({ success: true, message: 'Dropped test/debug signal' }, { headers: CORS });
    }

    // ── DEDICATED PROVISION: Virgin CPR (VCPR) Webhook Alert Handler ─────────
    const isVcprSignal = Boolean(
      payload.metadata?.is_vcpr === true ||
      payload.metadata?.is_vcpr_touch === true ||
      (payload.type && (payload.type.toUpperCase().includes('VIRGIN') || payload.type.toUpperCase().includes('VCPR'))) ||
      (payload.trigger && (payload.trigger.toUpperCase().includes('VIRGIN') || payload.trigger.toUpperCase().includes('VCPR'))) ||
      (payload.action && (payload.action.toUpperCase().includes('VIRGIN') || payload.action.toUpperCase().includes('VCPR')))
    );

    if (isVcprSignal) {
      console.log(`[Webhook Route][VCPR] Dedicated Virgin CPR Provision Triggered for ${symbol}`);
      
      const resolved = resolveSymbolAndExchange(
        payload.symbol || payload.ticker || symbol || 'UNKNOWN',
        payload.exchange
      );

      const isBull = Boolean(
        payload.metadata?.vcpr_direction === 'BULLISH' ||
        (payload.type && payload.type.toUpperCase().includes('LONG')) ||
        (payload.action && payload.action.toLowerCase().includes('buy')) ||
        (payload.analysis && (payload.analysis.toUpperCase().includes('BULLISH') || payload.analysis.toUpperCase().includes('SUPPORT') || payload.analysis.toUpperCase().includes('BOUNCE')))
      );

      const touchPrice = Number(
        payload.metadata?.vcpr_touch_price ||
        payload.touch_price ||
        payload.price ||
        payload.entry ||
        payload.entryPrice ||
        0
      );

      const zTop = payload.metadata?.vcpr_top != null ? Number(payload.metadata.vcpr_top) : null;
      const zBottom = payload.metadata?.vcpr_bottom != null ? Number(payload.metadata.vcpr_bottom) : null;
      const tf = payload.metadata?.vcpr_timeframe || payload.timeframe || 'D';
      const touchDate = payload.metadata?.vcpr_touch_date || payload.metadata?.vcpr_date || payload.vcpr_date || null;

      const signalTs = (payload.signal_ts || payload.entry_time || payload.entryTime) != null
        ? (() => {
            const rawTs = payload.signal_ts || payload.entry_time || payload.entryTime;
            const ts = Number(rawTs);
            if (!isNaN(ts) && ts > 1e12) return new Date(ts).toISOString();
            if (!isNaN(ts) && ts > 1e9)  return new Date(ts * 1000).toISOString();
            return typeof rawTs === 'string' ? rawTs : new Date().toISOString();
          })()
        : new Date().toISOString();

      const tz = getMarketTz(resolved.symbol, resolved.exchange);
      const signalTsMs = new Date(signalTs).getTime();
      const formattedDayStr = getTzDateStr(signalTsMs, tz);
      const formattedDateTimeStr = new Date(signalTsMs).toISOString().replace('T', ' ').substring(0, 19);

      // Clean metadata with strict source_feed segregation
      const vcprMetadata: Record<string, any> = {
        ...(payload.metadata || {}),
        is_vcpr: true,
        is_vcpr_touch: true,
        setup_family: 'VIRGIN_CPR',
        signal_family: 'VIRGIN_CPR',
        vcpr_direction: isBull ? 'BULLISH' : 'BEARISH',
        vcpr_touch_price: touchPrice,
        vcpr_top: zTop,
        vcpr_bottom: zBottom,
        vcpr_timeframe: tf,
        vcpr_touch_date: touchDate,
        source_feed: 'TradingView_VCPR',
        source: 'webhook_tradingview',
        entry_date: formattedDayStr,
        entryDate: formattedDateTimeStr,
        entry_time: signalTs,
        analysis: payload.analysis || `Virgin CPR ${isBull ? 'Bullish Support Bounce' : 'Bearish Resistance Rejection'} test at ${touchPrice}`
      };

      const newVcprSignal = {
        symbol: resolved.symbol,
        exchange: resolved.exchange,
        type: isBull ? 'LONG VIRGIN CPR' : 'SHORT VIRGIN CPR',
        entry: touchPrice,
        stop: zBottom && isBull ? zBottom * 0.995 : (zTop && !isBull ? zTop * 1.005 : null),
        target: zTop && isBull ? zTop * 1.01 : (zBottom && !isBull ? zBottom * 0.99 : null),
        status: 'ACTIVE',
        profit: 0,
        pricing_type: 'LIVE',
        signal_ts: signalTs,
        message: `⚡ [VCPR ${tf}] ${resolved.symbol} ${isBull ? 'Bullish Support Bounce' : 'Bearish Resistance Rejection'} at ${touchPrice}`,
        metadata: vcprMetadata
      };

      // Insert into canonical TradingView Webhook table (public.signals)
      const { data: insertedVcpr, error: vcprInsertErr } = await supabaseAdmin
        .from('signals')
        .insert([newVcprSignal])
        .select()
        .single();

      if (vcprInsertErr) {
        console.error('[VCPR_INSERT_ERROR]', vcprInsertErr.message);
        return NextResponse.json({ success: false, error: vcprInsertErr.message }, { status: 500, headers: CORS });
      }

      console.log(`[SIEM][VCPR_STORED] ID: ${insertedVcpr.id} | Symbol: ${resolved.symbol} | Direction: ${isBull ? 'BULLISH' : 'BEARISH'} | Price: ${touchPrice}`);

      // Dispatch Telegram Notification for Virgin CPR Alert
      const tgMsg = `⚡ <b>TLCS VIRGIN CPR ALERT</b>\n\n` +
        `📌 Asset: <b>${resolved.symbol}</b> (${resolved.exchange})\n` +
        `🎯 Signal: <b>${isBull ? '▲ LONG (Support Bounce)' : '▼ SHORT (Resistance Rejection)'}</b>\n` +
        `💰 Touch Price: <b>${touchPrice}</b>\n` +
        (zBottom != null && zTop != null ? `📊 Zone: <b>[${zBottom} - ${zTop}]</b>\n` : '') +
        (touchDate ? `📅 Level Date: <b>${touchDate}</b>\n` : '') +
        `⏱ Timeframe: <b>${tf}</b>\n` +
        `📡 Feed: <b>TradingView Webhook</b>`;

      await sendTelegramAlert(tgMsg, resolved.symbol);

      return NextResponse.json({
        success: true,
        mode: 'VirginCPR',
        signal_id: insertedVcpr.id,
        symbol: resolved.symbol,
        direction: isBull ? 'BULLISH' : 'BEARISH',
        feed: 'TradingView_VCPR'
      }, { headers: CORS });
    }

    // ── DEDICATED PROVISION: PivotBoss 7-Day Blueprint & Sequence Matrix Scans ─
    // Intercepts SessionOpenMatrix, PivotBossScan, and SevenDayMatrixScan payloads.
    // These payloads belong strictly to `public.pivotboss_scans` (id = 1) for the
    // Screener Matrix. They must NEVER bleed into trade signals or public.signals.
    const isScanPayload = payload.type === 'PivotBossScan' ||
                          payload.trigger === 'PivotBossScan' ||
                          payload.trigger === 'SessionOpenMatrix' ||
                          payload.type === 'SessionOpenMatrix' ||
                          payload.type === 'SevenDayMatrixScan';

    if (isScanPayload) {
      console.log(`[Webhook Route][Scanner] Intercepted Blueprint Matrix Payload (${payload.trigger || payload.type}) for ${payload.ticker || payload.symbol || 'MULTI-ASSET'}`);

      let parsedScanData: any[] = [];

      // Format 1: Full 7-Day Matrix array (col 0 to 6)
      if (Array.isArray(payload.matrix_days)) {
        payload.matrix_days.forEach((dayItem: any) => {
          const col = dayItem.col != null ? Number(dayItem.col) : 0;
          const symMap: Record<string, any> = {};
          const getRow = (sym: string) => {
            const s = (sym || '').trim().replace(/^(NSE_DLY|NSE|MCX|NYMEX|COMEX|BINANCE|TVC):/i, '').replace(/1!$/, '').replace(/!$/, '').trim();
            if (!s) return null;
            if (!symMap[s]) symMap[s] = { sym: s, dayOffset: col };
            return symMap[s];
          };
          const addField = (csv: any, field: string, val: string) => {
            if (!csv) return;
            csv.toString().split(/[\n,]+/).forEach((sym: string) => {
              const r = getRow(sym);
              if (r) r[field] = val;
            });
          };

          addField(dayItem.bM, 'missile', 'Bullish');
          addField(dayItem.sM, 'missile', 'Bearish');
          addField(dayItem.bSc, 'scalp', 'Bullish');
          addField(dayItem.sSc, 'scalp', 'Bearish');
          addField(dayItem.bL, 'light', 'Bullish');
          addField(dayItem.sL, 'light', 'Bearish');
          addField(dayItem.bD, 'div', 'Bullish');
          addField(dayItem.sD, 'div', 'Bearish');
          addField(dayItem.bR, 'rej', 'Bullish');
          addField(dayItem.sR, 'rej', 'Bearish');
          addField(dayItem.bAb, 'abs', 'Bullish');
          addField(dayItem.sAb, 'abs', 'Bearish');
          addField(dayItem.bFn, 'fnl', 'Bullish');
          addField(dayItem.sFn, 'fnl', 'Bearish');
          addField(dayItem.bOd, 'out', 'Bullish');
          addField(dayItem.sOd, 'out', 'Bearish');
          addField(dayItem.bSr, 'srd', 'Bullish');
          addField(dayItem.sSr, 'srd', 'Bearish');
          addField(dayItem.bFb, 'fb', 'Bullish');
          addField(dayItem.sFb, 'fb', 'Bearish');
          addField(dayItem.bAc, 'acc', 'Bullish');
          addField(dayItem.sAc, 'acc', 'Bearish');
          addField(dayItem.bExt, 'extRev', 'Bullish');
          addField(dayItem.sExt, 'extRev', 'Bearish');

          Object.values(symMap).forEach(row => parsedScanData.push(row));
        });
      } else if (payload.signals && typeof payload.signals === 'object') {
        // Format 2: SessionOpenMatrix sending day 0 (Today)
        const symMap: Record<string, any> = {};
        const getRow = (sym: string) => {
          const s = (sym || '').trim().replace(/^(NSE_DLY|NSE|MCX|NYMEX|COMEX|BINANCE|TVC):/i, '').replace(/1!$/, '').replace(/!$/, '').trim();
          if (!s) return null;
          if (!symMap[s]) symMap[s] = { sym: s, dayOffset: 0 };
          return symMap[s];
        };
        const addField = (csv: any, field: string, val: string) => {
          if (!csv) return;
          csv.toString().split(/[\n,]+/).forEach((sym: string) => {
            const r = getRow(sym);
            if (r) r[field] = val;
          });
        };
        const sigs = payload.signals;
        addField(sigs.bullMissile, 'missile', 'Bullish');
        addField(sigs.bearMissile, 'missile', 'Bearish');
        addField(sigs.bullScalp, 'scalp', 'Bullish');
        addField(sigs.bearScalp, 'scalp', 'Bearish');
        addField(sigs.bullLight, 'light', 'Bullish');
        addField(sigs.bearLight, 'light', 'Bearish');
        addField(sigs.bullDiv, 'div', 'Bullish');
        addField(sigs.bearDiv, 'div', 'Bearish');
        addField(sigs.bullRej, 'rej', 'Bullish');
        addField(sigs.bearRej, 'rej', 'Bearish');
        addField(sigs.bullAbs, 'abs', 'Bullish');
        addField(sigs.bearAbs, 'abs', 'Bearish');
        addField(sigs.bullFnl, 'fnl', 'Bullish');
        addField(sigs.bearFnh, 'fnl', 'Bearish');
        addField(sigs.bullOd, 'out', 'Bullish');
        addField(sigs.bearOd, 'out', 'Bearish');
        addField(sigs.bullSrd, 'srd', 'Bullish');
        addField(sigs.bearSrd, 'srd', 'Bearish');
        addField(sigs.bullFb, 'fb', 'Bullish');
        addField(sigs.bearFb, 'fb', 'Bearish');
        addField(sigs.bullAcc, 'acc', 'Bullish');
        addField(sigs.bearAcc, 'acc', 'Bearish');
        addField(sigs.bullExt || sigs.bullExtRev, 'extRev', 'Bullish');
        addField(sigs.bearExt || sigs.bearExtRev, 'extRev', 'Bearish');
        Object.values(symMap).forEach(row => parsedScanData.push(row));
      } else if (Array.isArray(payload.scan_data)) {
        // Format 3: Direct scan_data array
        parsedScanData = payload.scan_data;
      }

      if (parsedScanData.length > 0) {
        // Fetch existing scan data to merge if updating partial days
        const { data: existingPb } = await supabaseAdmin
          .from('pivotboss_scans')
          .select('scan_data')
          .eq('id', 1)
          .maybeSingle();

        let mergedData = parsedScanData;
        if (existingPb && Array.isArray(existingPb.scan_data) && !Array.isArray(payload.matrix_days)) {
          // If sending single day (e.g. SessionOpenMatrix dayOffset 0), preserve past days (dayOffset > 0)
          const pastDaysData = existingPb.scan_data.filter((r: any) => r && r.dayOffset != null && r.dayOffset > 0);
          mergedData = [...pastDaysData, ...parsedScanData];
        }

        const { error: pbErr } = await supabaseAdmin
          .from('pivotboss_scans')
          .upsert({
            id: 1,
            scan_data: mergedData,
            updated_at: new Date().toISOString()
          }, { onConflict: 'id' });

        if (pbErr) {
          console.error('[ScanPayload] DB Upsert error in Next.js webhook:', pbErr.message);
          return NextResponse.json({ success: false, error: pbErr.message }, { status: 500, headers: CORS });
        }

        console.log(`[ScanPayload] Successfully updated pivotboss_scans with ${mergedData.length} records.`);
      }

      return NextResponse.json({
        success: true,
        mode: 'PivotBossScan',
        trigger: payload.trigger || payload.type,
        count: parsedScanData.length,
        feed: 'TradingView_Screener'
      }, { headers: CORS });
    }

    const pivots = payload.pivots || payload;
    const isPivotUpdate = payload.type === 'PivotUpdate' || payload.trigger === 'PivotUpdate' || payload.pivots || (payload.trigger !== 'TradeClose' && payload.trigger !== 'TrailingSLUpdate' && (pivots.opening_bias || pivots.day_type || pivots.bias || pivots.c1 || pivots.mx || pivots.mX));
    
    // Handle Pivot Point Updates
    if (isPivotUpdate) {
      // Relaxed gate: save whenever type/trigger is explicitly PivotUpdate OR any key pivot field is present
      // (previously 0-values like pivot=0 caused the condition to fail and silently drop data)
      const hasPivotFields = payload.type === 'PivotUpdate' || payload.trigger === 'PivotUpdate' || !!(pivots.pivot || pivots.vah || pivots.tc || pivots.r1 || pivots.s1 || pivots.opening_bias || pivots.day_type || pivots.bias);
      if (hasPivotFields) {
          const pivotData = {
              symbol,
              pivot: Number(pivots.pivot) || 0,
              tc: Number(pivots.tc || pivots.tt) || null,
              bc: Number(pivots.bc || pivots.bbb) || null,
              ytc: Number(pivots.ytc || pivots.tt1) || null,
              ybc: Number(pivots.ybc || pivots.bbb1) || null,
              vah: Number(pivots.vah) || null,
              val: Number(pivots.val) || null,
              poc: Number(pivots.poc || pivots.current_poc_value) || null,
              open: Number(pivots.open || payload.open) || null,
              ph: Number(pivots.ph || pivots.dh) || null,
              pl: Number(pivots.pl || pivots.dl) || null,
              h3: Number(pivots.h3) || null,
              l3: Number(pivots.l3) || null,
              h4: Number(pivots.h4) || null,
              l4: Number(pivots.l4) || null,
              r1: Number(pivots.r1) || 0,
              s1: Number(pivots.s1) || 0,
              r2: Number(pivots.r2) || 0,
              s2: Number(pivots.s2) || 0,
              opening_bias: cleanBiasOrDayType(pivots.opening_bias || pivots.metadata?.opening_bias || pivots.marketType || pivots.metadata?.marketType || pivots.c1 || pivots.metadata?.c1 || pivots.bias || pivots.metadata?.bias),
              day_type: cleanBiasOrDayType(pivots.day_type || pivots.metadata?.day_type || pivots.dayType || pivots.metadata?.dayType || pivots.mx || pivots.mX || pivots.metadata?.mx || pivots.metadata?.mX),
              market_status: pivots.market_status || pivots.metadata?.market_status || pivots.metadata?.c1 || pivots.c1 || null,
              trade_zone: pivots.trade_zone || pivots.metadata?.trade_zone || pivots.zone || pivots.metadata?.zone || pivots.m1 || pivots.metadata?.m1 || null,
              metadata: (() => {
                  let rawMeta = scrubSecrets(pivots.metadata || pivots) || {};
                  let cleanMeta: Record<string, any> = {};
                  if (rawMeta && typeof rawMeta === 'object') {
                      for (const k of Object.keys(rawMeta)) {
                          let v = rawMeta[k];
                          if (['opening_bias', 'day_type', 'opening_print', 'bias', 'c1', 'mx', 'mX', 'marketType', 'dayType'].includes(k)) {
                              v = cleanBiasOrDayType(v);
                          }
                          cleanMeta[k] = v;
                      }
                  }
                  return Object.keys(cleanMeta).length > 0 ? cleanMeta : null;
              })(),
              updated_at: new Date().toISOString()
          };
          const { error: pivErr } = await supabaseAdmin.from('pivots').upsert(pivotData, { onConflict: 'symbol' });
          if (pivErr) console.error('[PIVOT_UPSERT_ERROR]', pivErr.message);
          else console.log(`[PIVOT] Stored pivot for ${symbol}`);
      }

      if (payload.type === 'PivotUpdate' || payload.trigger === 'PivotUpdate') {
         return NextResponse.json({ success: true, mode: 'PivotUpdate' }, { headers: CORS });
      }
    }

    // ── Screener Watchlist Update (TV Webhook) ──
    if (payload.type === 'ScreenerUpdate' || payload.trigger === 'ScreenerUpdate') {
      const { symbol, exchange } = resolveSymbolAndExchange(payload.symbol || payload.ticker || 'UNKNOWN', payload.exchange);
      const isNcpr = Boolean(payload.is_ncpr);
      const isInsideCpr = Boolean(payload.is_inside_cpr);
      const isRejection = Boolean(payload.is_rejection);
      const isNva = Boolean(payload.is_nva);
      const isOor = Boolean(payload.opening_bias && String(payload.opening_bias).toUpperCase().includes('OUT OF RANGE'));
      const isContinuation = Boolean(payload.is_continuation || (payload.c1 && String(payload.c1).toUpperCase().includes('CONTINUATION')));

      const triggerName = isNcpr ? 'NCPR Breakout' : isInsideCpr ? 'Inside CPR' : isRejection ? 'Rejection Day' : isOor ? 'Out of Range' : isNva ? 'Narrow Value' : 'Screener Setup';
      const cleanMeta = scrubSecrets({
        ...(payload.metadata || {}),
        ...payload,
        source_feed: 'TradingView_Screener',
        is_ncpr: isNcpr,
        cpr_type: isNcpr ? 'NCPR' : 'NORMAL',
        is_inside_cpr: isInsideCpr,
        is_rejection: isRejection,
        is_rejection_day: isRejection,
        is_nva: isNva,
        is_narrow_value: isNva,
        is_oor: isOor,
        is_continuation: isContinuation
      });

      const todayStartIso = new Date(new Date().setHours(0, 0, 0, 0)).toISOString();
      const { data: existingActive } = await supabaseAdmin
        .from('signals')
        .select('id, metadata, status')
        .eq('symbol', symbol)
        .neq('status', 'WATCHLIST')
        .gte('created_at', todayStartIso)
        .limit(1);

      if (existingActive && existingActive.length > 0) {
        const merged = { ...(existingActive[0].metadata || {}), ...cleanMeta };
        await supabaseAdmin.from('signals').update({ metadata: merged }).eq('id', existingActive[0].id);
        console.log(`[SIEM][SCREENER_UPDATE] Updated active trade metadata for ${symbol}`);
      } else {
        const { data: existingWl } = await supabaseAdmin
          .from('signals')
          .select('id')
          .eq('symbol', symbol)
          .eq('status', 'WATCHLIST')
          .gte('created_at', todayStartIso)
          .limit(1);

        if (existingWl && existingWl.length > 0) {
          await supabaseAdmin.from('signals').update({
            metadata: cleanMeta,
            signal_ts: new Date().toISOString()
          }).eq('id', existingWl[0].id);
          console.log(`[SIEM][SCREENER_UPDATE] Updated WATCHLIST signal for ${symbol}`);
        } else {
          await supabaseAdmin.from('signals').insert([{
            symbol,
            exchange,
            type: 'SCREENER SETUP',
            trigger: triggerName,
            status: 'WATCHLIST',
            outcome: 'OPEN',
            pricing_type: 'LIVE',
            signal_ts: new Date().toISOString(),
            metadata: cleanMeta
          }]);
          console.log(`[SIEM][SCREENER_UPDATE] Inserted new WATCHLIST signal for ${symbol}`);
        }
      }

      return NextResponse.json({ success: true, mode: 'ScreenerUpdate', symbol }, { headers: CORS });
    }

    // Handle Trade Close alerts
    const payloadStatusLower = (payload.status || '').toLowerCase();
    const isCloseTrigger = payload.trigger === 'TradeClose';
    const isCloseStatus = payloadStatusLower.includes('sl') || payloadStatusLower.includes('tp') || payloadStatusLower.includes('target') || payloadStatusLower.includes('stop') || payloadStatusLower.includes('closed') || payloadStatusLower.includes('loss') || payloadStatusLower.includes('win') || payloadStatusLower.includes('b/e') || payloadStatusLower.includes('breakeven') || payloadStatusLower.includes('cancel') || payloadStatusLower.includes('unknown');
    
    const isTrailingUpdate = payload.trigger === 'TrailingSLUpdate' || (payloadStatusLower.includes('update') && payloadStatusLower.includes('trail'));
    if (isCloseTrigger || (isCloseStatus && !isTrailingUpdate && payload.trigger !== 'TradeUpdate')) {
      let profitPct = payload.profit_pct != null ? Number(payload.profit_pct) : null;
      const status = payload.status || 'Closed';
      const statusLower = status.toLowerCase();
      const { symbol } = resolveSymbolAndExchange(payload.symbol || payload.ticker || 'UNKNOWN', payload.exchange);
      
      let rMultiple = null;
      let finalOutcomePct = profitPct;
      let activeSignal = null;
      let holdMins: number | null = null;
      const parseValidNumber = (val: any) => {
        if (val == null || val === '') return null;
        const num = Number(val);
        return !isNaN(num) ? num : null;
      };
      
      let exitPrice: number | null = parseValidNumber(payload.close_price) || parseValidNumber(payload.exit_price) || parseValidNumber(payload.closePrice) || parseValidNumber(payload.exitPrice) || parseValidNumber(payload.price) || null;
      
      let computedEntry: number | null = null;
      let profitAmount: number | null = null;
      try {
        // 0. Exact Identity Anchor via trade_id (100% deterministic 1:1 match)
        if (payload.trade_id) {
          const { data: tData } = await supabaseAdmin
            .from('signals')
            .select('*')
            .eq('metadata->>trade_id', payload.trade_id)
            .in('status', ['Active', 'OPEN', 'Open', 'ACTIVE LIMIT'])
            .order('created_at', { ascending: false })
            .limit(1)
            .maybeSingle();
          if (tData) {
            activeSignal = tData;
          }
        }

        if (!activeSignal) {
          let activeQuery = supabaseAdmin
            .from('signals')
            .select('*')
            .eq('symbol', symbol)
            .in('status', ['Active', 'OPEN', 'Open', 'ACTIVE LIMIT']);

          // 1. Entry Price matching (Exact or 0.1% tolerance binder)
          const rawEntry = payload.entryPrice || payload.entry || payload.entry_price;
          if (rawEntry != null) {
            const entryNum = Number(rawEntry);
            if (!isNaN(entryNum) && entryNum > 0) {
              const minEntry = entryNum * 0.999;
              const maxEntry = entryNum * 1.001;
              activeQuery = activeQuery.gte('entry', minEntry).lte('entry', maxEntry);
            }
          }

          // 2. Entry Timestamp matching (Supports ms 13-digit, sec 10-digit Unix timestamps, and ISO/formatted date strings)
          const rawTs = payload.entryTime || payload.entry_time || payload.entry_signal_ts || payload.entryDate;
          if (rawTs) {
              let parsedEntryTs = null;
              const tsNum = Number(rawTs);
              if (!isNaN(tsNum) && tsNum > 0) {
                  const ms = tsNum > 1e12 ? tsNum : (tsNum > 1e9 ? tsNum * 1000 : tsNum);
                  parsedEntryTs = new Date(ms).toISOString();
              } else if (typeof rawTs === 'string') {
                  const d = new Date(rawTs.includes('T') || rawTs.includes('Z') ? rawTs : rawTs.replace(' ', 'T') + 'Z');
                  if (!isNaN(d.getTime())) parsedEntryTs = d.toISOString();
              }
              if (parsedEntryTs) {
                  const entryMs = new Date(parsedEntryTs).getTime();
                  const tsStart = new Date(entryMs - 60000).toISOString();
                  const tsEnd   = new Date(entryMs + 60000).toISOString();
                  activeQuery = activeQuery.gte('signal_ts', tsStart).lte('signal_ts', tsEnd);
              }
          }

          const { data, error: fetchErr } = await activeQuery
            .order('created_at', { ascending: false })
            .limit(1)
            .maybeSingle();

          if (!fetchErr && data) {
            activeSignal = data;
          } else {
            // Fallback: Get the oldest open signal for this symbol to resolve trades in FIFO order
            const { data: fallbackData } = await supabaseAdmin
              .from('signals')
              .select('*')
              .eq('symbol', symbol)
              .in('status', ['Active', 'OPEN', 'Open'])
              .order('created_at', { ascending: true })
              .limit(1)
              .maybeSingle();
            if (fallbackData) activeSignal = fallbackData;
          }
        }
        
        // Attempt to calculate the math ourselves
        let activeOrBodyType = (activeSignal && activeSignal.type) ? activeSignal.type : payload.type;
        computedEntry = parseValidNumber(activeSignal?.entry) || parseValidNumber(payload.entry) || null;
        let computedStop = parseValidNumber(activeSignal?.stop) || parseValidNumber(payload.stop) || null;

        // Fallback for missing close_price using implied price based on status
        if (exitPrice === null) {
            if (statusLower.includes('trail')) {
                exitPrice = parseValidNumber(activeSignal?.trail_sl) || computedStop;
            } else if (statusLower.includes('sl') || statusLower.includes('stop') || statusLower.includes('loss')) {
                exitPrice = computedStop;
            } else if (statusLower.includes('tp') || statusLower.includes('target') || statusLower.includes('win')) {
                if ((statusLower.includes('tp4') || statusLower.includes('target 4')) && activeSignal && activeSignal.tp4) {
                    exitPrice = parseValidNumber(activeSignal.tp4);
                } else if ((statusLower.includes('tp3') || statusLower.includes('target 3')) && activeSignal && activeSignal.tp3) {
                    exitPrice = parseValidNumber(activeSignal.tp3);
                } else if ((statusLower.includes('tp2') || statusLower.includes('target 2')) && activeSignal && activeSignal.tp2) {
                    exitPrice = parseValidNumber(activeSignal.tp2);
                } else {
                    exitPrice = parseValidNumber(activeSignal?.target) || null;
                }
            } else if (statusLower.includes('b/e') || statusLower.includes('breakeven')) {
                exitPrice = computedEntry;
            }
        }

        let isLong = true;
        if (activeOrBodyType) {
          const t = activeOrBodyType.toUpperCase();
          if (t.includes('SHORT') || t.includes('SELL')) isLong = false;
        }

        // ── EXIT PRICE SANITY GUARD ──
        // If the trade exited via Initial SL / Stop Loss, the exit price CANNOT be on the profitable side of entry.
        // A contaminated bar close (e.g. market falling on a SHORT stopped trade) must be bound to the actual Stop Loss.
        if (statusLower.includes('initial sl') || statusLower === 'hit sl') {
          const isInProfit = isLong ? (computedEntry && exitPrice && exitPrice > computedEntry) : (computedEntry && exitPrice && exitPrice < computedEntry);
          if (isInProfit || exitPrice === null) {
            exitPrice = computedStop || (activeSignal ? activeSignal.stop : null) || exitPrice;
          }
        }

        if (computedEntry !== null && exitPrice !== null) {
          profitAmount = isLong ? (exitPrice - computedEntry) : (computedEntry - exitPrice);
          const calculatedPct = (profitAmount / computedEntry) * 100;
          finalOutcomePct = Number(calculatedPct.toFixed(3));
        }

        try {
          if (activeSignal && activeSignal.id) {
            const created = new Date(activeSignal.created_at);
            if (created && !isNaN(created.getTime())) {
              const now = new Date();
              const diffMs = now.getTime() - created.getTime();
              holdMins = Math.max(0, Math.floor(diffMs / 60000));
            }
          }
        } catch (e: any) {
          console.warn('[TradeClose Webhook] Existing signal fetch skipped or failed:', e.message);
        }
      } catch (e) {
        console.warn('Existing signal fetch skipped:', e);
      }

      // Determine outcome using ALL available evidence (Exact percentage math takes precedence)
      let outcome = 'OPEN';
      
      if (finalOutcomePct !== null && !isNaN(finalOutcomePct)) {
        if (finalOutcomePct > 0.005) {
          outcome = 'WIN';
        } else if (finalOutcomePct < -0.005) {
          outcome = 'LOSS';
        } else {
          outcome = 'BREAKEVEN';
          finalOutcomePct = 0.0;
        }
      } else if (statusLower.includes('tp') || statusLower.includes('target') || statusLower.includes('win') || statusLower.includes('completed')) {
        outcome = 'WIN';
      } else if (statusLower.includes('b/e') || statusLower.includes('breakeven') || statusLower.includes('break even')) {
        outcome = 'BREAKEVEN';
        if (finalOutcomePct === null) finalOutcomePct = 0.0;
      } else if (statusLower === 'hit sl' || statusLower.includes('initial sl') || statusLower.includes('invalidated')) {
        outcome = 'LOSS';
      } else if (statusLower.includes('stop') || statusLower.includes('loss') || statusLower.includes('force') || statusLower.includes('sl')) {
        outcome = 'LOSS';
      }

      let exitTimeISO = new Date().toISOString();

      // Safeguard against time travel: ensure exit_at is never before the entry time
      if (activeSignal && (activeSignal.signal_ts || activeSignal.created_at)) {
         const entryTs = new Date(activeSignal.signal_ts || activeSignal.created_at).getTime();
         const exitTs = new Date(exitTimeISO).getTime();
         if (exitTs < entryTs) {
             exitTimeISO = new Date(entryTs + 1000).toISOString(); // +1 second
         }
      }

      let rawMeta = activeSignal?.metadata || {};
      if (typeof rawMeta === 'string') {
        try { rawMeta = JSON.parse(rawMeta); } catch (e) { rawMeta = {}; }
      }
      let finalMetadata = { ...rawMeta };
      if (finalOutcomePct !== null) {
        finalMetadata.exact_pct = Number(finalOutcomePct.toFixed(2));
      }
      if (payload.pnlAmount != null && !isNaN(Number(payload.pnlAmount))) {
        let pts = Number(Number(payload.pnlAmount).toFixed(2));
        if (outcome === 'LOSS' && pts > 0) pts = -pts;
        if (outcome === 'WIN' && pts < 0) pts = Math.abs(pts);
        if (outcome === 'BREAKEVEN') pts = 0;
        finalMetadata.exact_pts = pts;
      } else if (profitAmount !== null && !isNaN(profitAmount)) {
        let pts = Number(profitAmount.toFixed(2));
        if (outcome === 'LOSS' && pts > 0) pts = -pts;
        if (outcome === 'WIN' && pts < 0) pts = Math.abs(pts);
        if (outcome === 'BREAKEVEN') pts = 0;
        finalMetadata.exact_pts = pts;
      }

      const closeTz = getMarketTz(symbol, payload.exchange);
      const exitMs = new Date(exitTimeISO).getTime();
      if (!finalMetadata.close_date) finalMetadata.close_date = getTzDateStr(exitMs, closeTz);
      if (!finalMetadata.closeDate) finalMetadata.closeDate = new Date(exitMs).toISOString().replace('T', ' ').substring(0, 19);

      const closeTrailSL = payload.slLevel || payload.stop || payload.trail_sl || payload.trailing_stop || payload.sl || null;
        const closeUpdateData: any = {
          status:        status,
          outcome:       outcome,
          exit_price:    exitPrice,
          exit_at:       exitTimeISO,
          metadata:      Object.keys(finalMetadata).length > 0 ? finalMetadata : null
        };
        if (closeTrailSL) closeUpdateData.trail_sl = closeTrailSL;

        let updateQuery = supabase.from('signals').update(closeUpdateData);

        if (activeSignal && activeSignal.id) {
          updateQuery = updateQuery.eq('id', activeSignal.id);
        } else {
          updateQuery = updateQuery.eq('symbol', symbol).in('status', ['Active', 'OPEN', 'Open']);
        }
        
        const { data: updatedData, error: closeErr } = await updateQuery.select();

      if (closeErr) {
        console.error('[SIEM][DATABASE_ERROR] TradeClose failed:', closeErr);
        return NextResponse.json({ success: false, error: 'Database transaction failed' }, { status: 500, headers: CORS });
      }

      console.log(`[SIEM][TRADE_CLOSED] Symbol: ${symbol} | Outcome: ${outcome}`);

      // ── Dispatch Telegram Notification for Trade Close ──
      const outcomeIcon = outcome === 'WIN' ? '🎯' : (outcome === 'LOSS' ? '❌' : '⚖️');
      const exactPctStr = finalOutcomePct != null ? `${finalOutcomePct > 0 ? '+' : ''}${finalOutcomePct.toFixed(2)}%` : '--';
      const exitPriceStr = exitPrice != null ? exitPrice : '--';
      const entryPriceStr = computedEntry != null ? computedEntry : '--';
      
      const tgExitMsg = `${outcomeIcon} *TRADE CLOSED* — *${symbol}*\n`
                      + `📊 *Outcome*: *${outcome}* (\`${exactPctStr}\`)\n`
                      + `📍 *Exit Price*: \`${exitPriceStr}\` | *Entry*: \`${entryPriceStr}\`\n`
                      + `🏷️ *Status*: \`${status}\``;
      
      sendTelegramAlert(tgExitMsg).catch(e => console.error('[Telegram Exit Dispatch Error]', e));

      return NextResponse.json({ success: true, mode: 'TradeClose', updatedCount: updatedData?.length || 0 }, { headers: CORS });
    }

    // Handle TrailingSLUpdate alerts
    if (payload.trigger === 'TrailingSLUpdate') {
      const { symbol } = resolveSymbolAndExchange(payload.symbol || payload.ticker || 'UNKNOWN', payload.exchange);
      const trailLevel = payload.slLevel || payload.stop || payload.trail_sl || payload.trailing_stop || payload.sl || null;
      const trailMsg = payload.tradeMessage || payload.analysis || (trailLevel ? `Trailing SL moved to ${trailLevel}` : null);
      const updateData: any = {
        trail_sl: trailLevel,
        updated_at: new Date().toISOString()
      };
      if (trailMsg) updateData.message = trailMsg;

      let updateQuery = supabaseAdmin
        .from('signals')
        .update(updateData);

      if (payload.entryTime || payload.entry_time || payload.entry_signal_ts) {
        let parsedEntryTs = null;
        const rawTs = payload.entryTime || payload.entry_time || payload.entry_signal_ts;
        const tsNum = Number(rawTs);
        if (!isNaN(tsNum) && tsNum > 1e12) {
            parsedEntryTs = new Date(tsNum).toISOString();
        } else if (typeof rawTs === 'string' && rawTs.includes('T')) {
            parsedEntryTs = rawTs;
        }
        if (parsedEntryTs) {
            // Use a ±5-second window to tolerate sub-second precision mismatches (TradingView
            // sends whole-second bar timestamps; DB stores sub-millisecond precision).
            const entryMs = new Date(parsedEntryTs).getTime();
            const tsStart = new Date(entryMs - 5000).toISOString();
            const tsEnd   = new Date(entryMs + 5000).toISOString();
            updateQuery = updateQuery.gte('signal_ts', tsStart).lte('signal_ts', tsEnd);
        }
      }
      
      updateQuery = updateQuery.eq('symbol', symbol).in('status', ['Active', 'OPEN', 'Open']);

      const { error: tslErr } = await updateQuery;
      if (tslErr) {
        console.error('[SIEM][DATABASE_ERROR] TrailingSLUpdate failed:', tslErr);
        return NextResponse.json({ success: false, error: 'Database transaction failed' }, { status: 500, headers: CORS });
      }

      if (trailLevel) {
        const tgTrailMsg = `📈 *TRAILING SL UPDATED* — *${symbol}*\n`
                         + `🛡️ *New Trailing Stop*: \`${trailLevel}\`\n`
                         + `📝 ${trailMsg || 'Trailing stop level locked.'}`;
        sendTelegramAlert(tgTrailMsg).catch(e => console.error('[Telegram Trailing Dispatch Error]', e));
      }

      return NextResponse.json({ success: true, mode: 'TrailingSLUpdate' }, { headers: CORS });
    }

    // SECURITY & ROBUSTNESS: Construct a pristine metadata object
    const safePayload = scrubSecrets(payload);
    let finalMetadata: Record<string, any> = {};
    
    // First, if payload has a nested 'metadata' object, merge it in
    if (safePayload.metadata && typeof safePayload.metadata === 'object') {
      finalMetadata = { ...safePayload.metadata };
    }
    
    // Then explicitly grab all known strategy properties from the top level (if they exist)
    const strategyKeys = [
      'opening_bias', 'day_type', 'opening_print', 'cpr_type', 'trade_zone', 'order_id', 
      'trade_id', 'market_status', 'c1', 'm1', 'mx', 'mX', 'd1', 'dayType', 'marketType', 
      'zone', 'tradeMessage', 'is_confluence', 'confluence_type', 'confluence_tag', 
      'has_divergence_confluence', 'is_ncpr', 'is_inside_cpr', 'dtc', 'dbc', 'prev_range', 'cpr_width',
      'is_nva', 'is_narrow_value', 'vah', 'val', 'va_width', 'is_rejection', 'is_continuation',
      'timeframe', 'interval'
    ];
    for (const key of strategyKeys) {
      if (safePayload[key] !== undefined && safePayload[key] !== null) {
        finalMetadata[key] = safePayload[key];
      }
    }

    // Explicitly guarantee timeframe presence (defaults to 15m if not provided)
    if (safePayload.timeframe || safePayload.interval) {
      finalMetadata.timeframe = safePayload.timeframe || safePayload.interval;
    }
    if (safePayload.interval) {
      finalMetadata.interval = safePayload.interval;
    }

    if (safePayload.is_confluence !== undefined) {
      finalMetadata.is_confluence = safePayload.is_confluence === true || safePayload.is_confluence === 'true' || safePayload.is_confluence === 1 || safePayload.is_confluence === '1';
    }
    if (safePayload.confluence_type !== undefined) {
      finalMetadata.confluence_type = safePayload.confluence_type;
    }
    if (safePayload.confluence_tag !== undefined) {
      finalMetadata.confluence_tag = safePayload.confluence_tag;
    }
    if (safePayload.has_divergence_confluence !== undefined) {
      finalMetadata.has_divergence_confluence = safePayload.has_divergence_confluence === true || safePayload.has_divergence_confluence === 'true';
    }
    if (safePayload.is_ncpr !== undefined) {
      finalMetadata.is_ncpr = safePayload.is_ncpr === true || safePayload.is_ncpr === 'true' || safePayload.is_ncpr === 1 || safePayload.is_ncpr === '1';
    }
    if (safePayload.is_inside_cpr !== undefined) {
      finalMetadata.is_inside_cpr = safePayload.is_inside_cpr === true || safePayload.is_inside_cpr === 'true' || safePayload.is_inside_cpr === 1 || safePayload.is_inside_cpr === '1';
    }
    if (safePayload.is_nva !== undefined) {
      finalMetadata.is_nva = safePayload.is_nva === true || safePayload.is_nva === 'true' || safePayload.is_nva === 1 || safePayload.is_nva === '1';
    }
    if (safePayload.is_narrow_value !== undefined) {
      finalMetadata.is_narrow_value = safePayload.is_narrow_value === true || safePayload.is_narrow_value === 'true' || safePayload.is_narrow_value === 1 || safePayload.is_narrow_value === '1';
    }
    if (safePayload.is_rejection !== undefined) {
      finalMetadata.is_rejection = safePayload.is_rejection === true || safePayload.is_rejection === 'true' || safePayload.is_rejection === 1 || safePayload.is_rejection === '1';
    }
    if (safePayload.is_continuation !== undefined) {
      finalMetadata.is_continuation = safePayload.is_continuation === true || safePayload.is_continuation === 'true' || safePayload.is_continuation === 1 || safePayload.is_continuation === '1';
    }

    // Mathematical CPR & NCPR Enrichment: if dtc, dbc, and prev_range exist, calculate exact NCPR (< 5.0% range)
    const dtcVal = Number(finalMetadata.dtc || safePayload.dtc || 0);
    const dbcVal = Number(finalMetadata.dbc || safePayload.dbc || 0);
    const prevRangeVal = Number(finalMetadata.prev_range || safePayload.prev_range || 0);
    if (dtcVal > 0 && dbcVal > 0 && prevRangeVal > 0) {
      const cprW = Math.abs(dtcVal - dbcVal);
      finalMetadata.cpr_width = cprW;
      if ((cprW / prevRangeVal) * 100 < 5.0) {
        finalMetadata.is_ncpr = true;
        if (!finalMetadata.cpr_type) finalMetadata.cpr_type = 'NCPR';
      }
    }
    if (finalMetadata.is_ncpr && !finalMetadata.cpr_type) {
      finalMetadata.cpr_type = 'NCPR';
    }

    // Mathematical Value Area & NVA Enrichment: if vah, val, and prev_range exist, calculate exact NVA (< 38.0% range)
    const vahVal = Number(finalMetadata.vah || safePayload.vah || 0);
    const valVal = Number(finalMetadata.val || safePayload.val || 0);
    if (vahVal > 0 && valVal > 0) {
      const vaW = Math.abs(vahVal - valVal);
      finalMetadata.va_width = vaW;
      if (prevRangeVal > 0 && (vaW / prevRangeVal) * 100 < 38.0) {
        finalMetadata.is_narrow_value = true;
        finalMetadata.is_nva = true;
      }
    }

    // c1 Pattern Derivation for Rejections and Continuations
    const c1Text = String(finalMetadata.c1 || safePayload.c1 || '').toUpperCase();
    if (c1Text.includes('REJECTION')) {
      finalMetadata.is_rejection = true;
    }
    if (c1Text.includes('CONTINUATION')) {
      finalMetadata.is_continuation = true;
    }

    // Map alternate names for metadata properties
    if (finalMetadata.dayType !== undefined && (finalMetadata.day_type === undefined || finalMetadata.day_type === null)) {
      finalMetadata.day_type = finalMetadata.dayType;
    }
    if (finalMetadata.marketType !== undefined && (finalMetadata.opening_bias === undefined || finalMetadata.opening_bias === null)) {
      finalMetadata.opening_bias = finalMetadata.marketType;
    }
    if (finalMetadata.zone !== undefined && (finalMetadata.trade_zone === undefined || finalMetadata.trade_zone === null)) {
      finalMetadata.trade_zone = finalMetadata.zone;
    }
    if (finalMetadata.tradeMessage !== undefined && (finalMetadata.analysis === undefined || finalMetadata.analysis === null)) {
      finalMetadata.analysis = finalMetadata.tradeMessage;
    }
    if (finalMetadata.c1 !== undefined && (finalMetadata.opening_bias === undefined || finalMetadata.opening_bias === null)) {
      finalMetadata.opening_bias = finalMetadata.c1;
    }
    if (finalMetadata.m1 !== undefined && (finalMetadata.trade_zone === undefined || finalMetadata.trade_zone === null)) {
      finalMetadata.trade_zone = finalMetadata.m1;
    }
    if (finalMetadata.mx !== undefined && (finalMetadata.day_type === undefined || finalMetadata.day_type === null)) {
      finalMetadata.day_type = finalMetadata.mx;
    }
    if (finalMetadata.mX !== undefined && (finalMetadata.day_type === undefined || finalMetadata.day_type === null)) {
      finalMetadata.day_type = finalMetadata.mX;
    }
    const rawSwingMobile = finalMetadata.market_status || finalMetadata.d1 || finalMetadata.SWING || finalMetadata.swing || finalMetadata.tradeMessage || payload.market_status || payload.d1 || payload.SWING || payload.swing || payload.tradeMessage;
    if (rawSwingMobile) {
      const cleanMobS = cleanBiasOrDayType(rawSwingMobile);
      if (cleanMobS) {
        finalMetadata.market_status = cleanMobS;
        finalMetadata.d1            = cleanMobS;
        finalMetadata.SWING         = cleanMobS;
      }
    }
    if (finalMetadata.opening_bias) finalMetadata.opening_bias = cleanBiasOrDayType(finalMetadata.opening_bias);
    if (finalMetadata.day_type) finalMetadata.day_type = cleanBiasOrDayType(finalMetadata.day_type);
    if (finalMetadata.opening_print) finalMetadata.opening_print = cleanBiasOrDayType(finalMetadata.opening_print);
    if (finalMetadata.bias) finalMetadata.bias = cleanBiasOrDayType(finalMetadata.bias);
    if (finalMetadata.c1) finalMetadata.c1 = cleanBiasOrDayType(finalMetadata.c1);
    if (finalMetadata.mx) finalMetadata.mx = cleanBiasOrDayType(finalMetadata.mx);
    if (finalMetadata.mX) finalMetadata.mX = cleanBiasOrDayType(finalMetadata.mX);

    // Resolve clean symbol and inferred exchange (handles "BINANCE:BTCUSDT" etc.)
    const resolved = resolveSymbolAndExchange(
      payload.symbol || payload.ticker || 'UNKNOWN',
      payload.exchange
    );

    // Mobile Alert Firezone Gate (Strictly applied ONLY to fire_alert signals):
    // All canonical signals must generate within firezone to consider for fire_alerts on mobile application.
    // All canonical signals generate as usual independently irrespective of firezone.
    const fireZoneVal = payload.fire_zone || payload.metadata?.fire_zone || finalMetadata.fire_zone;
    if (fireZoneVal) {
      finalMetadata.fire_zone = fireZoneVal;
      finalMetadata.fire_alert = fireZoneVal === 'FIREZONE';
    }

    const isExplicitFireAlert = (payload.trigger || '').toUpperCase() === 'FIREALERT' || 
                                (payload.trigger || '').toUpperCase() === 'CONFLUENCE' ||
                                (payload.trigger || '').toUpperCase() === 'CONFLUENCEALERT' ||
                                (payload.type || '').toUpperCase() === 'FIREALERT' ||
                                (payload.type || '').toUpperCase() === 'FIRE_ALERT' ||
                                (payload.type || '').toUpperCase() === 'CONFLUENCE' ||
                                (payload.type || '').toUpperCase() === 'CONFLUENCE_ALERT' ||
                                payload.fire_alert === true ||
                                payload.confluence === true;

    if (isExplicitFireAlert && fireZoneVal === 'ZONE') {
      console.log(`[Webhook Route] FIREZONE GATE: Mobile alert suppressed for fire_alert ${resolved.symbol} (${payload.type}): Generated outside firezone (fire_zone: ZONE).`);
      return NextResponse.json({ 
        success: true, 
        message: 'Mobile fire_alert suppressed: signal generated outside firezone',
        symbol: resolved.symbol,
        type: payload.type,
        fire_zone: 'ZONE'
      }, { headers: CORS });
    }

    if (isExplicitFireAlert && !finalMetadata.fire_zone) {
      finalMetadata.fire_zone = 'FIREZONE';
      finalMetadata.fire_alert = true;
    }

    const newSignal: Record<string, any> = {
      symbol:        resolved.symbol,
      exchange:      resolved.exchange,          // Reliably resolved — never null for known assets
      type:          payload.type ? payload.type.toUpperCase() : (payload.action === 'buy' ? 'LONG' : payload.action === 'sell' ? 'SHORT' : 'ALERT'),
      entry:         Number(payload.entry || payload.entryPrice || payload.price) || 0,
      stop:          Number(payload.stop  || payload.slLevel || payload.sl)   || null,
      trailing_stop: Number(payload.trailing_stop || payload.tsl) || null,
      target:        Number(payload.target || payload.tpLevel || payload.tp)  || null,
      status:        payload.status || 'Active',
      updated_at:    payload.trigger === 'TradeFill' ? new Date().toISOString() : undefined,
      profit:        Number(payload.profit) || 0,
      exit_price:    payload.closePrice != null ? Number(payload.closePrice) : (payload.exitPrice != null ? Number(payload.exitPrice) : (payload.close_price != null ? Number(payload.close_price) : (payload.exit_price != null ? Number(payload.exit_price) : null))),
      message:       payload.analysis || payload.tradeMessage || payload.message || `Signal detected for ${resolved.symbol}.`,
      pricing_type:  payload.pricing_type || 'LIVE',

      // ── Alerts Intelligence v2.4.1 fields ──────────────────────────
      // Populated by canBuy / canSell / ScalpBuy / ScalpSell triggers
      rr:          payload.rr        != null ? Number(payload.rr)  : null,
      tp2:         payload.tp2       != null ? Number(payload.tp2) : null,
      tp3:         payload.tp3       != null ? Number(payload.tp3) : null,
      tp4:         payload.tp4       != null ? Number(payload.tp4) : null,
      signal_ts:   (payload.signal_ts || payload.entry_signal_ts || payload.entry_time) != null
                     ? (() => {
                         const rawTs = payload.signal_ts || payload.entry_signal_ts || payload.entry_time;
                         const ts = Number(rawTs);
                         // TradingView sends timenow in ms (>1e12). Seconds ts (10 digits) also supported.
                         if (!isNaN(ts) && ts > 1e12) return new Date(ts).toISOString();
                         if (!isNaN(ts) && ts > 1e9)  return new Date(ts * 1000).toISOString();
                         // Already an ISO string
                         return typeof rawTs === 'string' ? rawTs : new Date().toISOString();
                       })()
                     : new Date().toISOString(),
      // 'trigger' stored in metadata (scrubbed below, but kept in cleanMetadata)
      // outcome, outcome_pct, r_multiple, exit_price, exit_at → filled later via DB update

      metadata: Object.keys(finalMetadata).length > 0 ? finalMetadata : null
    };

    // ── PIVOT FALLBACK (Double Assurance for BIAS/DAY TYPE) ─────────
    // If the entry alert was missing opening_bias or day_type, fetch it from pivots table
    if (!finalMetadata.opening_bias || !finalMetadata.day_type) {
      const { data: pivData } = await supabaseAdmin
        .from('pivots')
        .select('opening_bias, day_type, trade_zone, metadata')
        .eq('symbol', resolved.symbol)
        .maybeSingle();
      
      if (pivData) {
        const pivBias = pivData.opening_bias || pivData.metadata?.opening_bias;
        const pivDayType = pivData.day_type || pivData.metadata?.day_type;
        if (pivBias && !finalMetadata.opening_bias) finalMetadata.opening_bias = pivBias;
        if (pivDayType && !finalMetadata.day_type) finalMetadata.day_type = pivDayType;
        if (pivData.trade_zone && !finalMetadata.trade_zone) finalMetadata.trade_zone = pivData.trade_zone;
      }
    }

    // ── TIME & DAY DETERMINISTIC BINDING ─────────────────────────────────────
    const signalTsMs = newSignal.signal_ts ? new Date(newSignal.signal_ts).getTime() : Date.now();
    const resolvedTradeId = (finalMetadata && finalMetadata.trade_id) || bodyPayload?.trade_id || `${resolved.symbol}_${signalTsMs}_${(newSignal.type || 'TRADE').toString().toUpperCase().replace(/\s+/g, '_')}`;
    finalMetadata.trade_id = resolvedTradeId;

    const tz = getMarketTz(resolved.symbol, resolved.exchange);
    const formattedDayStr = getTzDateStr(signalTsMs, tz);
    const formattedDateTimeStr = new Date(signalTsMs).toISOString().replace('T', ' ').substring(0, 19);

    if (!finalMetadata.entry_date) finalMetadata.entry_date = formattedDayStr;
    if (!finalMetadata.entryDate) finalMetadata.entryDate = formattedDateTimeStr;
    if (!finalMetadata.entry_time) finalMetadata.entry_time = newSignal.signal_ts;

    newSignal.metadata = Object.keys(finalMetadata).length > 0 ? finalMetadata : null;

    // ── MARKET HOURS GUARD (RCA Fix — After-Hours Signal Prevention) ─────────
    // Resolve signal_ts to milliseconds for IST market hours check
    const sigType = newSignal.type || '';
    const isNewTrade = ['LONG','SHORT','BUY','SELL'].some(t => sigType.includes(t));
    if (isNewTrade && !is24x7Symbol(newSignal.symbol, newSignal.exchange)) {
      const signalTsMs = newSignal.signal_ts ? new Date(newSignal.signal_ts).getTime() : Date.now();
      const IST_OFFSET_MS = (5 * 60 + 30) * 60 * 1000;
      const istTime = new Date(signalTsMs + IST_OFFSET_MS).toISOString().replace('T',' ').substring(0,16) + ' IST';

      if (isMCXSymbol(newSignal.symbol, newSignal.exchange)) {
        if (!isWithinMCXMarketHours(signalTsMs)) {
          console.warn(`[SIEM][MARKET_HOURS_GUARD] Rejected after-hours MCX signal: ${newSignal.symbol} at ${istTime}. MCX is closed (9:00 AM–11:30 PM Mon–Fri only).`);
          return NextResponse.json(
            { success: false, error: 'Signal rejected: MCX market is closed', symbol: newSignal.symbol, signal_time_ist: istTime, market_hours: '9:00 AM – 11:30 PM IST, Monday–Friday' },
            { status: 400, headers: CORS }
          );
        }
      } else if (isNSESymbol(newSignal.symbol, newSignal.exchange)) {
        if (!isWithinNSEMarketHours(signalTsMs)) {
          console.warn(`[SIEM][MARKET_HOURS_GUARD] Rejected after-hours NSE signal: ${newSignal.symbol} at ${istTime}. NSE is closed (9:15 AM–3:45 PM Mon–Fri only).`);
          return NextResponse.json(
            { success: false, error: 'Signal rejected: NSE market is closed', symbol: newSignal.symbol, signal_time_ist: istTime, market_hours: '9:15 AM – 3:45 PM IST, Monday–Friday' },
            { status: 400, headers: CORS }
          );
        }
      }
    }


    // ── DUPLICATE TRADE & ACTIVE POSITION CONCURRENCY GUARD ─────────────────
    // Prevents duplicate entries from: TradingView webhook retries, bar replay re-fire,
    // or opening concurrent positions for the same symbol before the prior trade exits.
    {
      const tradeId = resolvedTradeId || (finalMetadata && finalMetadata.trade_id) || bodyPayload?.trade_id;
      if (tradeId) {
        const { data: existingTrade } = await supabase
          .from('signals')
          .select('id, status')
          .eq('symbol', newSignal.symbol)
          .eq('metadata->>trade_id', tradeId)
          .limit(1)
          .maybeSingle();

        if (existingTrade) {
          console.warn(`[Webhook Route] DEDUP: Trade with trade_id ${tradeId} already exists (id: ${existingTrade.id}, status: ${existingTrade.status}). Skipping.`);
          if (Object.keys(finalMetadata).length > 0 && ['Active', 'OPEN', 'Open', 'ACTIVE LIMIT'].includes(existingTrade.status)) {
            await supabase
              .from('signals')
              .update({ metadata: finalMetadata })
              .eq('id', existingTrade.id);
          }
          return NextResponse.json({ 
            success: true, 
            message: 'Skipped: Duplicate trade_id', 
            existing_id: existingTrade.id 
          }, { headers: CORS });
        }
      }

      const { data: existingActiveSig } = await supabase
        .from('signals')
        .select('id, symbol, created_at, status')
        .eq('symbol', newSignal.symbol)
        .in('status', ['Active', 'OPEN', 'Open', 'ACTIVE LIMIT'])
        .order('created_at', { ascending: false })
        .limit(1)
        .maybeSingle();

      if (existingActiveSig) {
        console.log(`[Webhook Route] CONCURRENCY: Active trade already open for ${newSignal.symbol} (id: ${existingActiveSig.id}, status: ${existingActiveSig.status}). Skipping concurrent open signal.`);
        if (Object.keys(finalMetadata).length > 0) {
          await supabase
            .from('signals')
            .update({ metadata: finalMetadata })
            .eq('id', existingActiveSig.id);
        }
        return NextResponse.json({ 
          success: true, 
          message: 'Skipped: Active trade already open for symbol', 
          existing_id: existingActiveSig.id 
        }, { headers: CORS });
      }
    }

    const { data: insertedData, error: signalError } = await supabase
      .from('signals')
      .insert([newSignal])
      .select()
      .single();

    if (signalError) {
      console.error('[SIEM][DATABASE_ERROR]', signalError);
      return NextResponse.json({ success: false, error: 'Database transaction failed' }, { status: 500, headers: CORS });
    }

    // SECURITY: Log successful insertion without exposing data
    console.log(`[SIEM][SIGNAL_STORED] ID: ${insertedData.id} | Symbol: ${newSignal.symbol} | Type: ${newSignal.type}`);

    // ── Dispatch Telegram Notification for New Entry ──
    const typeStr = newSignal.type ? newSignal.type.toUpperCase() : 'ALERT';
    const entryVal = newSignal.entry || '--';
    const stopVal  = newSignal.stop  || '--';
    const targetVal= newSignal.target|| '--';
    const biasStr  = finalMetadata.opening_bias ? `\n🎯 *Bias*: \`${finalMetadata.opening_bias}\`` : '';
    const dayStr   = finalMetadata.day_type     ? ` | *Day*: \`${finalMetadata.day_type}\`` : '';

    const isLimit = (newSignal.status || '').toUpperCase().includes('LIMIT') || (payload.trigger || '').toUpperCase().includes('LIMIT');

    // ── Dispatch Telegram Notifications (Active Signals Only) ──
    if (!isLimit) {
      const market = getMarketForSymbol(newSignal.symbol);
      const marketName = market ? market.toUpperCase() : 'UNKNOWN';

      const isFireAlert = finalMetadata.fire_alert === true ||
                          finalMetadata.confluence === true ||
                          (payload.trigger || '').toUpperCase() === 'FIREALERT' ||
                          (payload.trigger || '').toUpperCase() === 'CONFLUENCE' ||
                          (payload.trigger || '').toUpperCase() === 'CONFLUENCEALERT' ||
                          (payload.type || '').toUpperCase() === 'FIREALERT' ||
                          (payload.type || '').toUpperCase() === 'FIRE_ALERT' ||
                          (payload.type || '').toUpperCase() === 'CONFLUENCE' ||
                          (payload.type || '').toUpperCase() === 'CONFLUENCE_ALERT';

      if (isFireAlert) {
        const isLong = typeStr.includes('LONG') || typeStr.includes('BUY');
        const directionEmoji = isLong ? '🟢 ▲' : '🔴 ▼';
        const zoneStr = finalMetadata.fire_zone || 'CONFLUENCE ZONE';
        const tgFireMsg = `⚡ *TLCS CONFLUENCE ALERT* — *${marketName}*\n\n`
                        + `📌 *Asset*: *${newSignal.symbol}* (${newSignal.exchange || marketName})\n`
                        + `🎯 *Signal*: ${directionEmoji} *${typeStr}*\n`
                        + `💰 *Entry*: \`${entryVal}\`\n`
                        + `🛑 *Stop Loss*: \`${stopVal}\`\n`
                        + `🎯 *Target 1*: \`${targetVal}\``
                        + (newSignal.tp2 ? ` | *TP2*: \`${newSignal.tp2}\`` : '')
                        + (biasStr ? `${biasStr}` : '')
                        + (dayStr ? `${dayStr}` : '') + `\n`
                        + `⚡ *Confluence Zone*: \`${zoneStr}\` (Neutral / Outside Green & Red)\n\n`
                        + `📝 ${newSignal.message || `High-probability canonical Confluence Alert generated.`}`;

        sendTelegramAlert(tgFireMsg, newSignal.symbol, true).catch(e => console.error('[Telegram Confluence Alert Dispatch Error]', e));
      } else {
        const tgMsgText = `⚡ *${marketName} TRADE ACTIVE* — *${newSignal.symbol}* (*${typeStr}*)\n`
                        + `📍 *Entry*: \`${entryVal}\` | *SL*: \`${stopVal}\` | *TP*: \`${targetVal}\`${biasStr}${dayStr}\n`
                        + `📝 ${newSignal.message || `${marketName} trade signal active.`}`;

        sendTelegramAlert(tgMsgText, newSignal.symbol, false).catch(e => console.error('[Telegram Entry Dispatch Error]', e));
      }
    }



    // ── Dispatch Web Push to all subscribers (fire-and-forget background function) ──
    (async () => {
      try {
        const host = req.headers.get('host') || 'market-store.online';
        const isLocal = host.includes('localhost') || host.includes('127.0.0.1');
        const proto = isLocal ? 'http' : (req.headers.get('x-forwarded-proto') || 'https');
        const baseUrl = `${proto}://${host}`;
        const backgroundUrl = `${baseUrl}/.netlify/functions/push-dispatch-background`;

        console.log(`[SIEM][PUSH_DISPATCH] Triggering background function at: ${backgroundUrl}`);

        await fetch(backgroundUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            symbol: newSignal.symbol,
            type:   newSignal.type,
            entry:  newSignal.entry,
            stop:   newSignal.stop,
            target: newSignal.target,
          }),
        }).catch(err => {
          console.error('[SIEM][PUSH_DISPATCH_ERROR] Failed to trigger background push:', err.message);
        });
      } catch (err: any) {
        console.error('[SIEM][PUSH_DISPATCH_ERROR] Critical error in trigger setup:', err.message);
      }
    })();

    // ── Algo Execution (Private Dhan Account) ──
    (async () => {
      try {
        const trigger = payload.trigger || 'TradeOpen';
        const sigType = (newSignal.type || '').toUpperCase();
        const isExitWebhook = trigger === 'TradeClose' || ['EXIT', 'STOP', 'TP', 'TRAIL', 'CLOSE'].some(t => sigType.includes(t) || (payload.mode && payload.mode.toUpperCase().includes(t)));
        
        let securityId: string | null = null;
        let mappedSymbol = newSignal.symbol;
        let isOption = false;
        let optionDetails: any = null;
        
        const isLong = ['LONG', 'BUY'].some(t => sigType.includes(t));
        const isShort = ['SHORT', 'SELL'].some(t => sigType.includes(t));

        if (nymexToMcxMap[newSignal.symbol]) {
          mappedSymbol = nymexToMcxMap[newSignal.symbol];
          securityId = await getActiveMcxSecurityId(mappedSymbol);
        } else if (['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY'].includes(newSignal.symbol)) {
          // It's an Index -> Resolve to nearest ATM Option
          isOption = true;
          const entryPrice = parseFloat(newSignal.entry || '0');
          if (entryPrice > 0) {
              optionDetails = await getActiveOptionSecurityId(newSignal.symbol, entryPrice, isLong);
              if (optionDetails) {
                 securityId = optionDetails.securityId;
                 mappedSymbol = optionDetails.tradingSymbol;
              }
          }
        }
        
        if (!securityId) {
          console.log(`[ALGO][DHAN] Could not find active contract/option for ${newSignal.symbol}`);
          return;
        }

        let transactionType: 'BUY' | 'SELL' | null = null;
        
        if (isExitWebhook) {
          // For Options, if we bought CE/PE, we must SELL to exit.
          // For Futures, we take opposite direction.
          if (isOption) {
             transactionType = 'SELL';
          } else {
             if (isShort) transactionType = 'BUY';
             else if (isLong) transactionType = 'SELL';
             else {
               const { data: lastTrade } = await supabaseAdmin.from('signals').select('type').eq('symbol', newSignal.symbol).neq('id', insertedData.id).order('created_at', { ascending: false }).limit(1).maybeSingle();
               if (lastTrade && (lastTrade.type.includes('LONG') || lastTrade.type.includes('BUY'))) transactionType = 'SELL';
               if (lastTrade && (lastTrade.type.includes('SHORT') || lastTrade.type.includes('SELL'))) transactionType = 'BUY';
             }
          }
          
          if (transactionType) {
             console.log(`[ALGO][DHAN] Triggering EXIT Market order for ${mappedSymbol}`);
             const res = await placeMarketOrder(securityId, transactionType, 1, isOption ? optionDetails.exchangeSegment : 'MCX_COMM');
             if (res && res.orderId) {
               await supabaseAdmin.from('signals').update({ dhan_exit_order_id: res.orderId, dhan_traded_symbol: mappedSymbol }).eq('id', insertedData.id);
             }
          }
        } else {
          // ENTRY
          // For Options, we always BUY to enter (Option Buying)
          if (isOption) {
             transactionType = 'BUY';
          } else {
             transactionType = isLong ? 'BUY' : 'SELL';
          }
          
          if (transactionType) {
             console.log(`[ALGO][DHAN] Triggering ENTRY Limit order for ${mappedSymbol}`);
             const ltp = await getLivePrice(securityId, isOption ? optionDetails.exchangeSegment : 'MCX_COMM');
             if (ltp) {
               const res = await placeLimitOrder(securityId, transactionType, ltp, 1, isOption ? optionDetails.exchangeSegment : 'MCX_COMM');
               if (res && res.orderId) {
                 await supabaseAdmin.from('signals').update({ dhan_entry_order_id: res.orderId, dhan_traded_symbol: mappedSymbol }).eq('id', insertedData.id);
               }
             } else {
               console.log(`[ALGO][DHAN] Failed to fetch live price for ${mappedSymbol}`);
             }
          }
        }
      } catch (e: any) {
        console.error('[ALGO][DHAN][EXEC_ERROR]', e.message);
      }
    })();


    return NextResponse.json({ success: true, signalId: insertedData.id }, { headers: CORS });
    
  } catch (error: any) {
    console.error('[SIEM][WEBHOOK_CRITICAL]', error.message);
    return NextResponse.json({ success: false, error: 'Internal server error' }, { status: 500, headers: CORS });
  }
}

export async function GET(req: Request) {
  const CORS = getCorsHeaders(req);
  const clientIP = req.headers.get('x-forwarded-for')?.split(',')[0]?.trim() || 'unknown';
  
  // VAPT: Rate limit GET requests too
  if (isRateLimited(clientIP)) {
    return NextResponse.json({ success: false, error: 'Rate limit exceeded' }, { status: 429, headers: CORS });
  }

  // VAPT: Secure the GET endpoint
  const url = new URL(req.url);

  // ── REMOVED: destructive `?purge=true` branch ───────────────────────────────
  // A GET to `/api/webhook?purge=true&secret=<webhook_secret>` used to delete
  // EVERY row in `signals`. It was gated only by the webhook secret, which is
  // embedded in the Pine script as an input default and travels in every alert
  // payload - i.e. not a secret, and certainly not a safe key for an
  // irreversible mass delete reachable by a plain GET.
  //
  // Bulk deletion now lives ONLY behind authenticated admin routes:
  //   - POST /api/admin-purge          (Supabase session + profiles.role check)
  //   - POST /.netlify/functions/admin-clear-signals  (+ confirm: "DELETE_ALL")
  //
  // Anything still calling the old URL gets 410 so it fails loudly, not silently.
  if (url.searchParams.get('purge') === 'true') {
    console.warn(`[SIEM][SECURITY] Rejected legacy purge attempt from ${clientIP.substring(0, 8)}...`);
    return NextResponse.json(
      { success: false, error: 'Endpoint removed. Use POST /api/admin-purge with an admin session.' },
      { status: 410, headers: CORS }
    );
  }

  const { data: signals } = await supabaseAdmin
    .from('signals')
    .select('*')
    .order('created_at', { ascending: false })
    .limit(2000);

  return NextResponse.json({ signals: signals || [] }, { headers: CORS });
}
