const { createClient } = require('@supabase/supabase-js');
const supabase = createClient(
  'https://dwepduvhzuhzeehbeaaz.supabase.co',
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR3ZXBkdXZoenVoemVlaGJlYWF6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NzMwMDY3NSwiZXhwIjoyMDkyODc2Njc1fQ.4gnT-NbFvQp_8PwkCHqzMvt1KGXwyZXH6kpSqwC70qg'
);

async function run() {
  const { data, error } = await supabase
    .from('signals')
    .select('id, symbol, type, status, entry, created_at, signal_ts')
    .eq('symbol', 'GBPUSD')
    .order('created_at', { ascending: false })
    .limit(5);
  console.log(data);
}
run();
