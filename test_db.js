const { createClient } = require('@supabase/supabase-js');
require('dotenv').config({ path: '/Users/vishant/Documents/Project/TLCS_Website_Deploy/.env' });

const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY);

async function run() {
    const { data: openSignals } = await supabase
        .from('signals')
        .select('id, symbol, status, outcome, metadata')
        .in('status', ['OPEN', 'ACTIVE LIMIT'])
        .order('created_at', { ascending: false })
        .limit(5);
        
    console.log("OPEN SIGNALS:", JSON.stringify(openSignals, null, 2));

    const { data: recentSignals } = await supabase
        .from('signals')
        .select('id, symbol, status, outcome, metadata, created_at')
        .order('created_at', { ascending: false })
        .limit(5);

    console.log("RECENT SIGNALS:", JSON.stringify(recentSignals, null, 2));
}

run();
