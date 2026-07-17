const { createClient } = require('@supabase/supabase-js');
require('dotenv').config({ path: 'Tv-Alert-Mobile/.env.local' });
const supabase = createClient(process.env.NEXT_PUBLIC_SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY);

const body = {
  "trigger":"TradeClose",
  "secret":"675d6a25933d3fc1b78b45ba2d6b400c0d1598e6780e9b8ae4ea1b1f824d89eb",
  "symbol":"ETHUSDT",
  "type":"SHORT SCALP",
  "status":"Hit Initial SL",
  "entryPrice":"1863.09",
  "closePrice":"1868.93",
  "slLevel":"1868.93",
  "tpLevel":"1857.24",
  "pnlAmount":"-15.14",
  "profit_pct":"0.31",
  "r_multiple":"-1",
  "zone":"SHORT ZONE",
  "dayType":"IN RANGE IN VALUE",
  "marketType":"TYPICAL DAY, TRADING RANGE, SIDEWAYS",
  "tradeMessage":"NO SWING",
  "entryTime":"1784249100000",
  "closeTime":"1784250000000",
  "rawText":"Hit Initial SL | -15.14"
};

async function run() {
  try {
      let activeQuery = supabase
        .from('signals')
        .select('*')
        .eq('symbol', body.symbol);

      if (body.type) {
        const t = body.type.toUpperCase();
        if (t.includes('LONG') || t.includes('BUY')) {
          activeQuery = activeQuery.in('type', ['LONG', 'BUY']);
        } else if (t.includes('SHORT') || t.includes('SELL')) {
          activeQuery = activeQuery.in('type', ['SHORT', 'SELL']);
        }
      }

      const { data, error: fetchErr } = await activeQuery
        .order('created_at', { ascending: false })
        .limit(1)
        .single();
        
      console.log("activeQuery data:", data ? data.id : null, "err:", fetchErr);

      let activeSignal = null;
      if (!fetchErr && data) {
        activeSignal = data;
      } else {
        const { data: fallbackData } = await supabase
          .from('signals')
          .select('*')
          .eq('symbol', body.symbol)
          .in('status', ['Active', 'OPEN', 'Open'])
          .order('created_at', { ascending: false })
          .limit(1)
          .single();
        if (fallbackData) activeSignal = fallbackData;
        console.log("fallback data:", fallbackData ? fallbackData.id : null);
      }
      
      console.log("Active Signal Final:", activeSignal ? activeSignal.id : null);
  } catch (e) {
      console.log("Error:", e);
  }
}
run();
