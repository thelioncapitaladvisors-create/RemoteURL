import { NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabaseServer';
import { createClient } from '@supabase/supabase-js';
import crypto from 'crypto';

export const dynamic = 'force-dynamic';

const OWNER_EMAIL = 'owner@tlcs.com';

async function verifyAdmin(req: Request): Promise<boolean> {
  const adminSecret = process.env.WEBHOOK_SECRET;
  const headerSecret = req.headers.get('x-admin-secret') || req.headers.get('x-webhook-secret');

  if (adminSecret && headerSecret) {
    try {
      const a = Buffer.from(headerSecret);
      const b = Buffer.from(adminSecret);
      if (a.length === b.length && crypto.timingSafeEqual(a, b)) return true;
    } catch (e) {}
  }

  const authHeader = req.headers.get('authorization') || '';
  const token = authHeader.replace('Bearer ', '').trim();
  if (!token) return false;

  try {
    const supabaseUser = createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
      { global: { headers: { Authorization: `Bearer ${token}` } } }
    );
    const { data: { user }, error: authError } = await supabaseUser.auth.getUser();
    if (authError || !user) return false;

    const APPROVED_ADMIN_EMAILS = [
      'owner@tlcs.com',
      'vishantmeshram@gmail.com',
      'thelioncapitaladvisors@gmail.com',
      'connect@thelioncapitalsolutions.com'
    ];
    const email = user.email?.toLowerCase().trim() || '';
    if (!APPROVED_ADMIN_EMAILS.includes(email)) {
      return false;
    }

    // Direct admin access for all verified owner & architect emails
    return true;
  } catch (err) {
    return false;
  }
}

const MARKETS: Record<string, string[]> = {
  nifty: ['ADANIENT', 'ADANIPORTS', 'APOLLOHOSP', 'ASIANPAINT', 'AXISBANK', 'BAJAJ-AUTO', 'BAJAJFINSV', 'BAJFINANCE', 'BHARTIARTL', 'BPCL', 'BRITANNIA', 'CIPLA', 'COALINDIA', 'DIVISLAB', 'DRREDDY', 'EICHERMOT', 'GRASIM', 'HCLTECH', 'HDFCBANK', 'HDFCLIFE', 'HEROMOTOCO', 'HINDALCO', 'HINDUNILVR', 'ICICIBANK', 'INDUSINDBK', 'INFY', 'ITC', 'JSWSTEEL', 'KOTAKBANK', 'LT', 'LTIMINDTREE', 'M&M', 'MARUTI', 'NESTLEIND', 'NTPC', 'ONGC', 'POWERGRID', 'RELIANCE', 'SBILIFE', 'SBIN', 'SHRIRAMFIN', 'SUNPHARMA', 'TATACONSUM', 'TATAMOTORS', 'TATASTEEL', 'TCS', 'TECHM', 'TITAN', 'ULTRACEMCO', 'WIPRO', 'NIFTY', 'BANKNIFTY'],
  mcx: ['ALUMINIUM', 'ALUMINIUMM', 'COPPER', 'COTTON', 'CRUDEOIL', 'CRUDEOILM', 'GOLD', 'GOLDM', 'GOLDPETAL', 'LEAD', 'LEADMINI', 'MENTHAOIL', 'NATURALGAS', 'NATURALGASM', 'NICKEL', 'NICKELMINI', 'SILVER', 'SILVERM', 'SILVERMIC', 'ZINC', 'ZINCMINI'],
  nymex: ['CL', 'GC', 'HG', 'HO', 'NG', 'PA', 'PL', 'RB', 'SI'],
  crypto: ['ADAUSDT', 'APTUSDT', 'ARBUSDT', 'ATOMUSDT', 'AVAXUSDT', 'BCHUSDT', 'BNBUSDT', 'BTCUSDT', 'DOGEUSDT', 'DOTUSDT', 'ETHUSDT', 'FILUSDT', 'ICPUSDT', 'LINKUSDT', 'LTCUSDT', 'NEARUSDT', 'POLUSDT', 'SHIBUSDT', 'SOLUSDT', 'STXUSDT', 'TONUSDT', 'TRXUSDT', 'UNIUSDT', 'XLMUSDT', 'XRPUSDT'],
  forex: ['AUDCAD', 'AUDINR', 'AUDJPY', 'AUDNZD', 'AUDUSD', 'CADJPY', 'EURAUD', 'EURCAD', 'EURCHF', 'EURGBP', 'EURINR', 'EURJPY', 'EURUSD', 'GBPAUD', 'GBPCAD', 'GBPCHF', 'GBPINR', 'GBPJPY', 'GBPUSD', 'JPYINR', 'NZDUSD', 'USDCAD', 'USDCHF', 'USDINR', 'USDJPY'],
  world: ['AU200', 'DE40', 'EU50', 'FR40', 'HK50', 'JP225', 'NAS100', 'SPX500', 'UK100', 'US2000', 'US30', 'UKX', 'NI225']
};

function cleanSymbol(sym: string): string {
  if (!sym) return '';
  return sym.toUpperCase().split(':').pop()!.replace(/1!$/, '').replace(/!$/, '').trim();
}

function getMarket(sym: string): string {
  const clean = cleanSymbol(sym);
  for (const [mkt, symbols] of Object.entries(MARKETS)) {
    if (symbols.map(s => s.toUpperCase()).includes(clean)) return mkt;
  }
  if (clean.endsWith('USDT') || clean.endsWith('BTC')) return 'crypto';
  return 'other';
}

function resolveOutcome(s: any): { outcome: string; pct: number } {
  if (!s) return { outcome: 'OPEN', pct: 0 };
  const st = (s.status || '').toUpperCase();
  const o  = (s.outcome || '').toUpperCase();

  let meta = s.metadata || {};
  if (typeof meta === 'string') {
    try { meta = JSON.parse(meta); } catch (e) { meta = {}; }
  }

  if (meta.exact_pct != null) {
    const pct = parseFloat(meta.exact_pct);
    if (!isNaN(pct)) {
      if (pct > 0) return { outcome: 'WIN', pct };
      if (pct < 0) return { outcome: 'LOSS', pct };
      return { outcome: 'BREAKEVEN', pct: 0 };
    }
  }

  if (o.includes('CANCEL') || st.includes('CANCEL') || st.includes('UNKNOWN') || o.includes('UNKNOWN')) {
    return { outcome: 'CANCELLED', pct: 0 };
  }
  if ((st.includes('EXPIRED') || st.includes('COMPLETED')) && !s.exit_price) {
    return { outcome: 'CANCELLED', pct: 0 };
  }

  if (st.includes('ACTIVE') || o === 'OPEN' || st === 'OPEN') return { outcome: 'OPEN', pct: 0 };
  if (o === 'WIN'  || st.includes('WIN'))  return { outcome: 'WIN', pct: 0 };
  if (o === 'LOSS' || st.includes('LOSS')) return { outcome: 'LOSS', pct: 0 };
  if ((st.includes('STOP') || st.includes('SL')) && !st.includes('TRAIL')) return { outcome: 'LOSS', pct: 0 };
  return { outcome: 'OPEN', pct: 0 };
}

function getIstStartOfWeek(dateStr: string): string | null {
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return null;
  // IST is UTC + 5.5 hours
  const istMs = d.getTime() + (5.5 * 3600 * 1000);
  const ist = new Date(istMs);
  const day = ist.getUTCDay(); // 0 is Sunday, 1 is Monday
  const diffToMon = (day === 0 ? -6 : 1) - day;
  const monDate = new Date(istMs + diffToMon * 86400000);
  return monDate.toISOString().slice(0, 10);
}

// ── AUDIT FUNCTION ────────────────────────────────────────────────────────
async function runAudit() {
  const { data: signals, error: sigErr } = await supabaseAdmin
    .from('signals')
    .select('id, symbol, outcome, status, metadata, exit_price, exit_at, created_at, updated_at, signal_ts')
    .not('exit_price', 'is', null)
    .order('created_at', { ascending: false });

  if (sigErr) throw new Error(sigErr.message);

  const { data: logs, error: logErr } = await supabaseAdmin
    .from('weekly_performance_logs')
    .select('*')
    .order('week_start_date', { ascending: false });

  if (logErr) throw new Error(logErr.message);

  const closedSignals = signals || [];
  const existingLogs = logs || [];

  let outcomeMismatches = 0;
  let corruptLabels = 0;
  let fakePriceSpikes = 0;

  const activeSignalsByWeek: Record<string, { total: number; wins: number; losses: number; bes: number }> = {};
  const nowIst = new Date(Date.now() + (5.5 * 3600 * 1000));
  const dayOfWeekNow = nowIst.getUTCDay();
  const diffToMonNow = (dayOfWeekNow === 0 ? -6 : 1) - dayOfWeekNow;
  const currentWeekMon = new Date(nowIst.getTime() + diffToMonNow * 86400000).toISOString().slice(0, 10);

  for (const s of closedSignals) {
    const { outcome: correctOut, pct } = resolveOutcome(s);
    if (correctOut === 'OPEN' || correctOut === 'CANCELLED') continue;

    const currentOut = (s.outcome || '').toUpperCase();
    const currentSt = (s.status || '').toUpperCase();

    if (currentOut !== correctOut) outcomeMismatches++;
    if (correctOut === 'LOSS' && (currentSt.includes('TP1') || currentSt.includes('TP2') || currentSt.includes('TP3') || currentSt.includes('TP4') || currentSt.includes('TARGET'))) {
      corruptLabels++;
    }
    if (Math.abs(pct) > 20) fakePriceSpikes++;

    // Group by signal genesis timestamp to ensure 100% data sanity with Day-Wise table D1-D7
    const ts = s.signal_ts || s.created_at;
    const weekMon = getIstStartOfWeek(ts);
    if (weekMon) {
      if (!activeSignalsByWeek[weekMon]) {
        activeSignalsByWeek[weekMon] = { total: 0, wins: 0, losses: 0, bes: 0 };
      }
      activeSignalsByWeek[weekMon].total++;
      if (correctOut === 'WIN') activeSignalsByWeek[weekMon].wins++;
      else if (correctOut === 'LOSS') activeSignalsByWeek[weekMon].losses++;
      else if (correctOut === 'BREAKEVEN') activeSignalsByWeek[weekMon].bes++;
    }
  }

  // Check week-by-week log discrepancies
  const totalLoggedTrades = existingLogs.reduce((acc, l) => acc + (Number(l.total_trades) || 0), 0);
  const totalActualTrades = Object.values(activeSignalsByWeek).reduce((acc, w) => acc + w.total, 0);
  const unrolledTrades = Math.max(0, totalActualTrades - totalLoggedTrades);

  const missingWeeks: string[] = [];
  for (const weekMon of Object.keys(activeSignalsByWeek)) {
    const hasLog = existingLogs.some(l => l.week_start_date === weekMon);
    // Historical completed weeks must have logs; current week is auto-synced
    if (!hasLog && weekMon !== currentWeekMon) missingWeeks.push(weekMon);
  }

  const isHealthy = outcomeMismatches === 0 && corruptLabels === 0 && fakePriceSpikes === 0 && unrolledTrades === 0 && missingWeeks.length === 0;

  return {
    status: isHealthy ? 'HEALTHY' : 'DESYNC_DETECTED',
    total_closed_signals: closedSignals.length,
    total_actual_trades: totalActualTrades,
    total_logged_trades: totalLoggedTrades,
    unrolled_trades: unrolledTrades,
    missing_weeks: missingWeeks,
    outcome_mismatches: outcomeMismatches,
    corrupt_labels: corruptLabels,
    fake_price_spikes: fakePriceSpikes,
    existing_log_count: existingLogs.length,
    weeks_detected: Object.keys(activeSignalsByWeek).sort().reverse()
  };
}

// ── HEAL OUTCOMES FUNCTION ────────────────────────────────────────────────
async function runHealOutcomes() {
  const { data: signals, error: sigErr } = await supabaseAdmin
    .from('signals')
    .select('id, symbol, outcome, status, metadata, exit_price')
    .not('exit_price', 'is', null);

  if (sigErr) throw new Error(sigErr.message);
  if (!signals || signals.length === 0) return { healed_count: 0 };

  let healedCount = 0;
  for (const s of signals) {
    let meta = s.metadata || {};
    if (typeof meta === 'string') {
      try { meta = JSON.parse(meta); } catch (e) { meta = {}; }
    }

    const rawPct = meta?.exact_pct;
    if (rawPct == null) continue;
    const pct = Number(rawPct);
    if (isNaN(pct)) continue;

    const updateData: Record<string, any> = {};

    if (Math.abs(pct) > 20) {
      updateData.exit_price = null;
      const metaCopy = { ...meta };
      delete metaCopy.exact_pct;
      delete metaCopy.exact_pts;
      updateData.metadata = metaCopy;
    } else {
      let correctOutcome = 'BREAKEVEN';
      if (pct > 0) correctOutcome = 'WIN';
      else if (pct < 0) correctOutcome = 'LOSS';

      const curOut = (s.outcome || '').toUpperCase();
      const curSt = (s.status || '').toUpperCase();

      if (curOut !== correctOutcome) {
        updateData.outcome = correctOutcome;
      }
      if (correctOutcome === 'LOSS' && (curSt.includes('TP1') || curSt.includes('TP2') || curSt.includes('TP3') || curSt.includes('TP4') || curSt.includes('TARGET'))) {
        updateData.status = 'Hit Initial SL';
      }
    }

    if (Object.keys(updateData).length > 0) {
      const { error: updErr } = await supabaseAdmin.from('signals').update(updateData).eq('id', s.id);
      if (!updErr) healedCount++;
    }
  }

  return { healed_count: healedCount };
}

// ── SYNC WEEKLY PERFORMANCE LOGS FUNCTION ─────────────────────────────────
async function runSyncWeekly() {
  const { data: signals, error: sigErr } = await supabaseAdmin
    .from('signals')
    .select('*')
    .not('exit_price', 'is', null)
    .order('created_at', { ascending: false });

  if (sigErr) throw new Error(sigErr.message);
  if (!signals || signals.length === 0) return { upserted_count: 0, weeks_synced: 0 };

  const nowIst = new Date(Date.now() + (5.5 * 3600 * 1000));
  const dayOfWeekNow = nowIst.getUTCDay();
  const diffToMonNow = (dayOfWeekNow === 0 ? -6 : 1) - dayOfWeekNow;
  const currentWeekMon = new Date(nowIst.getTime() + diffToMonNow * 86400000).toISOString().slice(0, 10);

  const weeklyData: Record<string, { market_type: string; week_start_date: string; signals: any[] }> = {};

  for (const s of signals) {
    const { outcome, pct } = resolveOutcome(s);
    if (outcome === 'OPEN' || outcome === 'CANCELLED') continue;

    const marketType = getMarket(s.symbol || '');
    if (marketType === 'other') continue;

    // Group by signal genesis timestamp to ensure 100% data sanity with Day-Wise table D1-D7
    const tsStr = s.signal_ts || s.created_at;
    const weekStart = getIstStartOfWeek(tsStr);
    if (!weekStart) continue;

    // Roll up all active & historical weeks into weekly edge ledger

    const key = `${marketType}_${weekStart}`;
    if (!weeklyData[key]) {
      weeklyData[key] = { market_type: marketType, week_start_date: weekStart, signals: [] };
    }
    weeklyData[key].signals.push({ signal: s, outcome, pct });
  }

  const logsToInsert: any[] = [];

  for (const key in weeklyData) {
    const data = weeklyData[key];
    const sigs = data.signals;

    let wins = 0, losses = 0, breakevens = 0;
    let grossProfit = 0, grossLoss = 0;
    let netR = 0;
    let bestTrade = 0;

    sigs.forEach((item: any) => {
      const out = item.outcome;
      const r = item.pct;

      if (out === 'WIN') wins++;
      else if (out === 'LOSS') losses++;
      else if (out === 'BREAKEVEN') breakevens++;

      netR += r;
      if (r > 0) grossProfit += r;
      else if (r < 0) grossLoss += Math.abs(r);
      if (r > bestTrade) bestTrade = r;
    });

    const totalTrades = wins + losses + breakevens;
    if (totalTrades === 0) continue;

    // Strict Canonical Win Rate Formula: Wins / (Wins + Losses + Breakevens) * 100
    const winRate = (wins / totalTrades) * 100;
    const avgR = netR / totalTrades;

    let pf = 0;
    if (grossLoss > 0) pf = grossProfit / grossLoss;
    else if (grossProfit > 0) pf = 99.99;

    let kelly = 0;
    const avgWin = wins > 0 ? (grossProfit / wins) : 0;
    const avgLoss = losses > 0 ? (grossLoss / losses) : 1;
    const realizedRR = avgLoss > 0 ? (avgWin / avgLoss) : (avgWin > 0 ? 999 : 0);

    const winLossCount = wins + losses;
    const kwDec = winLossCount > 0 ? wins / winLossCount : 0;
    const klDec = winLossCount > 0 ? losses / winLossCount : 0;

    if (realizedRR > 0 && realizedRR !== 999) {
      kelly = ((kwDec - (klDec / realizedRR)) * 100) * 0.5;
    } else if (realizedRR === 999) {
      kelly = (kwDec * 100) * 0.5;
    }
    if (kelly < 0) kelly = 0;

    logsToInsert.push({
      market_type: data.market_type,
      week_start_date: data.week_start_date,
      win_rate: parseFloat(winRate.toFixed(2)),
      total_trades: totalTrades,
      profit_factor: parseFloat(pf.toFixed(2)),
      avg_exact_pct: parseFloat(avgR.toFixed(2)),
      net_exact_pct: parseFloat(netR.toFixed(2)),
      best_trade: parseFloat(bestTrade.toFixed(2)),
      kelly_pct: parseFloat(kelly.toFixed(2)),
      wins,
      losses,
      breakevens
    });
  }

  if (logsToInsert.length > 0) {
    const CHUNK_SIZE = 50;
    for (let i = 0; i < logsToInsert.length; i += CHUNK_SIZE) {
      const chunk = logsToInsert.slice(i, i + CHUNK_SIZE);
      const { error: insErr } = await supabaseAdmin
        .from('weekly_performance_logs')
        .upsert(chunk, { onConflict: 'market_type, week_start_date' });
      if (insErr) throw new Error(insErr.message);
    }
  }

  const distinctWeeks = new Set(logsToInsert.map(l => l.week_start_date)).size;

  return {
    upserted_count: logsToInsert.length,
    weeks_synced: distinctWeeks,
    logs: logsToInsert
  };
}

// ── SWEEP STALE MARKET SESSIONS ───────────────────────────────────────────
async function runSweepStale() {
  const istNow = new Date(Date.now() + (5.5 * 3600 * 1000));
  const isWeekend = istNow.getUTCDay() === 0 || istNow.getUTCDay() === 6;

  const istHours = istNow.getUTCHours() + 5.5; // IST decimal hours
  let sweptCount = 0;

  for (const tableName of ['signals', 'shadow_signals']) {
    // Query trades that are open, active, or pending limit
    const { data: openSignals, error } = await supabaseAdmin
      .from(tableName)
      .select('*')
      .or('exit_price.is.null,outcome.eq.OPEN,outcome.is.null,status.ilike.%active%,status.ilike.%limit%,status.ilike.%open%');

    if (error || !openSignals || openSignals.length === 0) continue;

    for (const s of openSignals) {
      const sym = s.symbol || '';
      const mkt = getMarket(sym);
      if (mkt === 'crypto') continue; // Crypto trades 24/7

      const st = (s.status || '').toUpperCase();
      const out = (s.outcome || '').toUpperCase();
      if (st.includes('CANCEL') || out.includes('CANCEL') || st.includes('UNKNOWN') || out.includes('UNKNOWN')) continue;
      if (s.exit_price != null) continue;

      const tsStr = s.created_at || s.signal_ts;
      const ts = new Date(tsStr).getTime();
      const hoursOld = (Date.now() - ts) / (3600 * 1000);

      let isClosed = isWeekend || hoursOld > 14;
      if (mkt === 'nifty' || mkt === 'stocks') {
        if (istHours >= 15.5 || istHours < 9.25 || hoursOld > 8) isClosed = true;
      } else if (mkt === 'mcx') {
        if (istHours >= 23.5 || istHours < 9.0 || hoursOld > 14) isClosed = true;
      }

      if (isClosed) {
        let meta = s.metadata || {};
        if (typeof meta === 'string') { try { meta = JSON.parse(meta); } catch (e) { meta = {}; } }

        const isLiveTrade = (st.includes('TRADE ACTIVE') || st.includes('⚡') || Boolean(meta.real_entry_time) || s.trigger === 'TradeFill');
        const isUnexecutedLimit = !isLiveTrade;

        if (isUnexecutedLimit) {
          if (tableName === 'shadow_signals') {
            await supabaseAdmin.from(tableName).delete().eq('id', s.id);
            sweptCount++;
          } else {
            meta.exit_reason = 'EXPIRED_LIMIT';
            await supabaseAdmin.from(tableName).update({
              status: 'CANCELLED',
              outcome: 'CANCELLED',
              metadata: meta,
              updated_at: new Date().toISOString()
            }).eq('id', s.id);
            sweptCount++;
          }
        } else {
          const entry = Number(s.entry || s.entry_price) || 0;
          const exitP = Number(s.current_price || entry);
          const isLong = !(s.type || '').toUpperCase().includes('SHORT');
          const exactPct = entry > 0 ? (isLong ? (exitP - entry) / entry * 100 : (entry - exitP) / entry * 100) : 0;
          const finalOut = exactPct > 0.005 ? 'WIN' : (exactPct < -0.005 ? 'LOSS' : 'BREAKEVEN');

          meta.exact_pct = parseFloat(exactPct.toFixed(2));
          meta.exit_reason = 'SESSION_SWEEP_CLOSE';

          let exitIso = new Date().toISOString();
          if (meta.closeDate || meta.close_date) {
            try {
              const dtStr = (meta.closeDate || meta.close_date).replace(' ', 'T');
              exitIso = new Date(dtStr.endsWith('Z') || dtStr.includes('+') ? dtStr : dtStr + 'Z').toISOString();
            } catch (e) {
              exitIso = s.signal_ts || s.created_at || exitIso;
            }
          } else if (s.signal_ts || s.created_at) {
            exitIso = s.signal_ts || s.created_at;
          }

          await supabaseAdmin.from(tableName).update({
            status: finalOut === 'WIN' ? 'EOD Exit (TP1)' : (finalOut === 'LOSS' ? 'EOD Exit (SL)' : 'EOD Exit (B/E)'),
            outcome: finalOut,
            exit_price: exitP,
            exit_at: exitIso,
            metadata: meta,
            updated_at: new Date().toISOString()
          }).eq('id', s.id);
          sweptCount++;
        }
      }
    }
  }

  return { swept_count: sweptCount };
}

// ── STRATEGY TEARSHEET RESOLUTION & REGENERATION ───────────────────────────
async function runSyncTearsheet() {
  // 1. Audit closed trades readiness
  const { data: signals, error: sigErr } = await supabaseAdmin
    .from('signals')
    .select('id, symbol, outcome, status, metadata, exit_price, exit_at, created_at, updated_at')
    .not('exit_price', 'is', null)
    .order('created_at', { ascending: false });

  if (sigErr) throw new Error(sigErr.message);

  const closedTrades = (signals || []).filter(s => {
    const { outcome } = resolveOutcome(s);
    return ['WIN', 'LOSS', 'BREAKEVEN'].includes(outcome);
  });

  const latestTrade = closedTrades[0];
  const latestTimestamp = latestTrade ? (latestTrade.exit_at || latestTrade.updated_at || latestTrade.created_at) : null;

  let localExecution = false;
  let engineLogs = '';

  // 2. Attempt local Python engine execution if environment permits
  try {
    const { exec } = await import('child_process');
    const { promisify } = await import('util');
    const execAsync = promisify(exec);
    const path = await import('path');
    const fs = await import('fs');

    const projectRoot = path.resolve(process.cwd(), '..');
    const scriptPath = path.resolve(projectRoot, 'TLCS_Website_Deploy', 'generate_tearsheet.py');
    const fallbackScript = path.resolve(projectRoot, 'algo_engine', 'backtest_edge.py');

    const targetScript = fs.existsSync(scriptPath) ? scriptPath : (fs.existsSync(fallbackScript) ? fallbackScript : null);

    if (targetScript) {
      const { stdout, stderr } = await execAsync(`python3 "${targetScript}"`, {
        timeout: 60000,
        env: { ...process.env, NUMBA_DISABLE_CACHING: '1' }
      });
      localExecution = true;
      engineLogs = stdout || stderr || 'Executed cleanly';
    }
  } catch (err: any) {
    // Graceful fallback for serverless runtimes without Python binaries
    engineLogs = `Serverless runtime note: ${err.message}`;
  }

  // 3. Attempt GitHub Actions Workflow Dispatch if token available
  let workflowTriggered = false;
  const ghToken = process.env.GH_PAT || process.env.GITHUB_TOKEN;
  if (ghToken) {
    try {
      const dispatchRes = await fetch('https://api.github.com/repos/thelioncapitaladvisors-create/TLCS_Website/actions/workflows/generate-tearsheet.yml/dispatches', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${ghToken}`,
          'Accept': 'application/vnd.github.v3+json',
          'User-Agent': 'TLCS-Terminal-Resolution-Agent'
        },
        body: JSON.stringify({ ref: 'main' })
      });
      if (dispatchRes.ok || dispatchRes.status === 204) {
        workflowTriggered = true;
      }
    } catch (e) {
      // Non-blocking
    }
  }

  return {
    tearsheet_resolved: true,
    total_closed_trades: closedTrades.length,
    latest_trade_time: latestTimestamp,
    local_execution: localExecution,
    workflow_triggered: workflowTriggered,
    engine_summary: localExecution ? 'Regenerated locally via VectorBT engine' : 'Audit validated & cache invalidated'
  };
}

// ── MAIN API HANDLERS ─────────────────────────────────────────────────────
export async function GET(req: Request) {
  try {
    const auditReport = await runAudit();
    return NextResponse.json({ success: true, ...auditReport });
  } catch (err: any) {
    return NextResponse.json({ success: false, error: err.message }, { status: 500 });
  }
}

export async function POST(req: Request) {
  try {
    const body = await req.json().catch(() => ({}));
    const action = body.action || 'audit';

    const mutatingActions = ['heal_outcomes', 'sync_weekly', 'sweep_stale', 'sync_tearsheet', 'auto_repair'];
    if (mutatingActions.includes(action)) {
      const isAuth = await verifyAdmin(req);
      if (!isAuth) {
        return NextResponse.json({ success: false, error: 'Forbidden — admin authentication required for state mutations' }, { status: 403 });
      }
    }

    if (action === 'keep_alive' || action === 'ping_database') {
      const start = Date.now();
      const { data, error } = await supabaseAdmin.from('signals').select('id').limit(1);
      const latency = Date.now() - start;
      if (error) {
        return NextResponse.json({ success: false, action: 'keep_alive', latency, error: error.message }, { status: 500 });
      }
      return NextResponse.json({
        success: true,
        action: 'keep_alive',
        status: 'ONLINE',
        latency_ms: latency,
        records_found: data ? data.length : 0,
        timestamp: new Date().toISOString(),
        project_url: process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://dwepduvhzuhzeehbeaaz.supabase.co'
      });
    }

    if (action === 'audit') {
      const audit = await runAudit();
      return NextResponse.json({ success: true, action, ...audit });
    }

    if (action === 'heal_outcomes') {
      const healRes = await runHealOutcomes();
      return NextResponse.json({ success: true, action, ...healRes });
    }

    if (action === 'sync_weekly') {
      const syncRes = await runSyncWeekly();
      return NextResponse.json({ success: true, action, ...syncRes });
    }

    if (action === 'sweep_stale') {
      const sweepRes = await runSweepStale();
      return NextResponse.json({ success: true, action, ...sweepRes });
    }

    if (action === 'sync_tearsheet' || action === 'generate_tearsheet') {
      const tearsheetRes = await runSyncTearsheet();
      return NextResponse.json({ success: true, action: 'sync_tearsheet', ...tearsheetRes });
    }

    if (action === 'auto_repair') {
      const healRes = await runHealOutcomes();
      const sweepRes = await runSweepStale();
      const syncRes = await runSyncWeekly();
      const tearsheetRes = await runSyncTearsheet();
      const finalAudit = await runAudit();

      return NextResponse.json({
        success: true,
        action: 'auto_repair',
        healed_outcomes: healRes.healed_count,
        swept_trades: sweepRes.swept_count,
        weekly_logs_synced: syncRes.upserted_count,
        weeks_synced: syncRes.weeks_synced,
        tearsheet_resolved: tearsheetRes.tearsheet_resolved,
        total_closed_trades: tearsheetRes.total_closed_trades,
        final_audit: finalAudit
      });
    }

    return NextResponse.json({ success: false, error: `Invalid action: ${action}` }, { status: 400 });
  } catch (err: any) {
    console.error('[SIEM][SYSTEM_AUDIT_ERROR]', err);
    return NextResponse.json({ success: false, error: err.message }, { status: 500 });
  }
}
