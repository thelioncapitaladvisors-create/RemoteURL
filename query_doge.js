const { createClient } = require('@supabase/supabase-js');
const supabase = createClient('https://dwepduvhzuhzeehbeaaz.supabase.co', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR3ZXBkdXZoenVoemVlaGJlYWF6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NzMwMDY3NSwiZXhwIjoyMDkyODc2Njc1fQ.4gnT-NbFvQp_8PwkCHqzMvt1KGXwyZXH6kpSqwC70qg');

async function run() {
  const startOfTodayISO = new Date(new Date().setHours(0,0,0,0)).toISOString();
  const { data, error } = await supabase.from('crypto_signals').select('*').eq('symbol', 'DOGEUSDT').gte('signal_ts', startOfTodayISO).order('signal_ts', { ascending: false });
  console.log("Error:", error);
  data.forEach(d => {
    console.log(`ID: ${d.id}, outcome: ${d.outcome}, status: ${d.status}`);
    console.log(`opening_bias: '${d.opening_bias}', day_type: '${d.day_type}'`);
    console.log(`metadata: ${typeof d.metadata === 'string' ? d.metadata : JSON.stringify(d.metadata)}`);
    console.log("-------------------");
  });
}
run();
