const { createClient } = require('@supabase/supabase-js');
require('dotenv').config({ path: 'Tv-Alert-Mobile/.env.local' });
const supabase = createClient(process.env.NEXT_PUBLIC_SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY);

async function run() {
  const { data, error } = await supabase.from('signals').select('*').eq('symbol', 'ETHUSDT').order('created_at', {ascending: false}).limit(1);
  console.log("Error:", error);
  console.log("Data:", JSON.stringify(data, null, 2));
}
run();
