
const { createClient } = require('@supabase/supabase-js');
require('dotenv').config({ path: '.env.local' });

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseKey) {
    console.error('Supabase URL or Key is missing.');
    process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseKey);

const marketSymbols = {
  "nifty": [
    "ADANIENT",
    "ADANIPORTS",
    "APOLLOHOSP",
    "ASIANPAINT",
    "AXISBANK",
    "BAJAJ-AUTO",
    "BAJAJFINSV",
    "BAJFINANCE",
    "BHARTIARTL",
    "BPCL",
    "BRITANNIA",
    "CIPLA",
    "COALINDIA",
    "DIVISLAB",
    "DRREDDY",
    "EICHERMOT",
    "GRASIM",
    "HCLTECH",
    "HDFCBANK",
    "HDFCLIFE",
    "HEROMOTOCO",
    "HINDALCO",
    "HINDUNILVR",
    "ICICIBANK",
    "INDUSINDBK",
    "INFY",
    "ITC",
    "JSWSTEEL",
    "KOTAKBANK",
    "LT",
    "LTIMindtree",
    "M&M",
    "MARUTI",
    "NESTLEIND",
    "NTPC",
    "ONGC",
    "POWERGRID",
    "RELIANCE",
    "SBILIFE",
    "SBIN",
    "SHRIRAMFIN",
    "SUNPHARMA",
    "TATACONSUM",
    "TATAMOTORS",
    "TATASTEEL",
    "TCS",
    "TECHM",
    "TITAN",
    "ULTRACEMCO",
    "WIPRO"
  ],
  "mcx": [
    "ALUMINIUM",
    "ALUMINIUMM",
    "COPPER",
    "COTTON",
    "CRUDEOIL",
    "CRUDEOILM",
    "GOLD",
    "GOLDM",
    "GOLDPETAL",
    "LEAD",
    "LEADMINI",
    "MENTHAOIL",
    "NATURALGAS",
    "NATURALGASM",
    "NICKEL",
    "NICKELMINI",
    "SILVER",
    "SILVERM",
    "SILVERMIC",
    "ZINC",
    "ZINCMINI"
  ],
  "nymex": [
    "CL",
    "GC",
    "HG",
    "HO",
    "NG",
    "PA",
    "PL",
    "RB",
    "SI"
  ],
  "crypto": [
    "ADAUSDT",
    "APTUSDT",
    "ARBUSDT",
    "ATOMUSDT",
    "AVAXUSDT",
    "BCHUSDT",
    "BNBUSDT",
    "BTCUSDT",
    "DOGEUSDT",
    "DOTUSDT",
    "ETHUSDT",
    "FILUSDT",
    "ICPUSDT",
    "LINKUSDT",
    "LTCUSDT",
    "NEARUSDT",
    "POLUSDT",
    "SHIBUSDT",
    "SOLUSDT",
    "STXUSDT",
    "TONUSDT",
    "TRXUSDT",
    "UNIUSDT",
    "XLMUSDT",
    "XRPUSDT"
  ],
  "forex": [
    "AUDCAD",
    "AUDINR",
    "AUDJPY",
    "AUDNZD",
    "AUDUSD",
    "CADJPY",
    "EURAUD",
    "EURCAD",
    "EURCHF",
    "EURGBP",
    "EURINR",
    "EURJPY",
    "EURUSD",
    "GBPAUD",
    "GBPCAD",
    "GBPCHF",
    "GBPINR",
    "GBPJPY",
    "GBPUSD",
    "JPYINR",
    "NZDUSD",
    "USDCAD",
    "USDCHF",
    "USDINR",
    "USDJPY"
  ],
  "world": [
    "AU200",
    "DE40",
    "EU50",
    "FR40",
    "HK50",
    "JP225",
    "NAS100",
    "SPX500",
    "UK100",
    "US2000",
    "US30"
  ]
};

async function syncToSupabase() {
    console.log('Syncing market symbols to Supabase...');
    
    for (const [market_id, symbols] of Object.entries(marketSymbols)) {
        const { error } = await supabase
            .from('market_config')
            .upsert({ market_id: market_id, symbols: symbols }, { onConflict: 'market_id' });
            
        if (error) {
            console.error(`Error updating ${market_id}:`, error);
        } else {
            console.log(`Successfully synced ${market_id} with ${symbols.length} symbols.`);
        }
    }
}

syncToSupabase();
