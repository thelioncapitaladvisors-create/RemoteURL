require('dotenv').config({ path: '/Users/vishant/Documents/Project/algo_engine/.env' });
const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_KEY || process.env.SUPABASE_SERVICE_ROLE_KEY);

async function check() {
    const { data, error } = await supabase
        .from('signals')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(10);
    console.log("Recent Signals:", data ? data.map(d => ({
        id: d.id,
        symbol: d.symbol,
        created_at: d.created_at,
        signal_ts: d.signal_ts,
        status: d.status
    })) : error);
}

check();
