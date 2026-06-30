import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';
dotenv.config({ path: './Tv-Alert-Mobile/.env.local' });

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || '';

if (!supabaseUrl || !supabaseKey) {
  console.error("Missing Supabase credentials");
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseKey);

async function fix() {
  const { data, error } = await supabase
    .from('signals')
    .select('*')
    .in('status', ['Closed', 'Closed: TP', 'Closed: SL', 'Force Closed', 'TP1', 'TP2', 'TP3', 'TP4'])
    .not('exit_price', 'is', null);

  if (error || !data) {
    console.error(error);
    return;
  }

  console.log(`Found ${data.length} closed signals to check.`);
  let fixed = 0;

  for (const s of data) {
    if (!s.entry || !s.stop || !s.exit_price || !s.type) continue;
    
    const ep = Number(s.exit_price);
    const en = Number(s.entry);
    const sl = Number(s.stop);
    
    if (Math.abs(en - sl) === 0) continue;

    const t = s.type.toUpperCase();
    const isL = t.includes('LONG') || t.includes('BUY');
    const isS = t.includes('SHORT') || t.includes('SELL');
    
    if (!isL && !isS) continue;

    const rVal = isL ? (ep - en) / (en - sl) : (en - ep) / (sl - en);
    
    if (s.r_multiple != null) {
      const dbR = Number(s.r_multiple);
      if (Math.sign(dbR) !== Math.sign(rVal) && Math.abs(dbR) > 0.01) {
         let newOutcome = s.outcome;
         if (rVal > 0) newOutcome = 'WIN';
         else if (rVal < 0) newOutcome = 'LOSS';
         else newOutcome = 'BREAKEVEN';

         console.log(`Fixing ${s.symbol} ${s.type}: DB=${dbR} True=${rVal.toFixed(2)} Outcome=${newOutcome}`);
         
         await supabase.from('signals').update({
           r_multiple: Number(rVal.toFixed(2)),
           outcome: newOutcome
         }).eq('id', s.id);
         fixed++;
      }
    }
  }
  console.log(`Fixed ${fixed} corrupted signals!`);
}

fix();
