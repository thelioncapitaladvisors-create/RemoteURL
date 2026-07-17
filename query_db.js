const { createClient } = require('@supabase/supabase-js');
const supabase = createClient('https://dwepduvhzuhzeehbeaaz.supabase.co', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR3ZXBkdXZoenVoemVlaGJlYWF6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NzMwMDY3NSwiZXhwIjoyMDkyODc2Njc1fQ.4gnT-NbFvQp_8PwkCHqzMvt1KGXwyZXH6kpSqwC70qg');

async function run() {
  const { data, error } = await supabase.from('signals').select('*').order('created_at', { ascending: false }).limit(3);
  console.log("Error:", error);
  console.log("Data:", JSON.stringify(data, null, 2));
}
run();
