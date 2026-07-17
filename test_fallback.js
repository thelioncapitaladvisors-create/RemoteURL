const { createClient } = require('@supabase/supabase-js');
require('dotenv').config({ path: 'Tv-Alert-Mobile/.env.local' });
const supabase = createClient(process.env.NEXT_PUBLIC_SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY);

async function run() {
  const { data: fallbackData, error } = await supabase
    .from('signals')
    .select('*')
    .eq('symbol', 'ETHUSDT')
    .in('status', ['Active', 'OPEN', 'Open'])
    .order('created_at', { ascending: false })
    .limit(1)
    .single();
  console.log("Fallback Error:", error);
  console.log("Fallback Data:", fallbackData);
}
run();
