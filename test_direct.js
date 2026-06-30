const { createClient } = require('@supabase/supabase-js');
require('dotenv').config({ path: 'Tv-Alert-Mobile/.env.local' });

const supabase = createClient(process.env.NEXT_PUBLIC_SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY);

async function run() {
    const payload = {
      symbol: "AUDUSD",
      exchange: "FX_IDC",
      type: "SELL",
      entry: 0.68985,
      stop: 0.68860,
      trail_sl: 0.68860,
      target: 0.68902,
      status: "Active",
      signal_ts: new Date().toISOString()
    };
    
    const { data, error } = await supabase.from('signals').insert(payload).select().single();
    if (error) {
        console.error("Insert failed:", error);
    } else {
        console.log("Insert success:", data);
        await supabase.from('signals').delete().eq('id', data.id);
    }
}
run();
