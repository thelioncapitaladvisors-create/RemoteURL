const { createClient } = require('@supabase/supabase-js');
const fs = require('fs');
const env = fs.readFileSync('./TLCS_Website_Deploy/.env', 'utf8').split('\n');
let url, key;
env.forEach(l => {
    if (l.startsWith('SUPABASE_URL=')) url = l.split('=')[1];
    if (l.startsWith('SUPABASE_SERVICE_KEY=')) key = l.split('=')[1];
});
const supabase = createClient(url, key);
(async () => {
    const { data } = await supabase.from('signals').select('symbol, type, opening_bias, day_type, metadata').order('created_at', { ascending: false }).limit(2);
    console.log(JSON.stringify(data, null, 2));
})();
