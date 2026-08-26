const { createClient } = require('@supabase/supabase-js');
const fs = require('fs');

const envFile = fs.readFileSync('/Users/vishant/Documents/Project/Tv-Alert-Mobile/.env.local', 'utf-8');
const lines = envFile.split('\n');
let url = '';
let key = '';
for (const line of lines) {
  if (line.startsWith('NEXT_PUBLIC_SUPABASE_URL=')) url = line.split('=')[1];
  if (line.startsWith('SUPABASE_SERVICE_ROLE_KEY=')) key = line.split('=')[1];
}

const supabase = createClient(url, key, { auth: { persistSession: false } });

async function run() {
  const { data, error } = await supabase.from('signals').insert({
    symbol: 'DEBUG_TEST_SCRIPT',
    exchange: 'SYS',
    status: 'Active',
    type: 'LONG'
  }).select();
  console.log('Error:', error);
  console.log('Data:', data);
  if (data) {
    await supabase.from('signals').delete().eq('id', data[0].id);
  }
}
run();
