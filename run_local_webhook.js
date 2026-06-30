import { NextResponse } from 'next/server';

function isNSESymbol(symbol, exchange) {
  const sym  = (symbol   || '').toUpperCase();
  const exch = (exchange || '').toUpperCase();
  if (['NSE', 'BSE', 'NFO', 'MCX', 'INDEX'].includes(exch)) return true;
  if (/^(NIFTY|BANKNIFTY|FINNIFTY|MIDCPNIFTY|SENSEX)/.test(sym)) return true;
  if (!exch && /^[A-Z&]{2,20}$/.test(sym) && !sym.endsWith('USDT') && sym.length <= 15) return true;
  return false;
}

function is24x7Symbol(symbol, exchange) {
  const sym  = (symbol   || '').toUpperCase();
  const exch = (exchange || '').toUpperCase();
  if (sym.endsWith('USDT') || sym.endsWith('BTC') || sym.endsWith('ETH')) return true;
  if (['BINANCE', 'COINBASE', 'CRYPTO'].includes(exch)) return true;
  if (['FX_IDC', 'FX', 'OANDA', 'FXCM'].includes(exch)) return true;
  if (sym.length === 6 && /^[A-Z]{6}$/.test(sym)) return true; // forex pairs
  const worldIdx = ['UKX','HSI','NI225','DAX','CAC40','SX5E','DJI','SPX','NDX','RUT','XJO'];
  if (worldIdx.includes(sym)) return true;
  if (/^[A-Z]{2}1!$/.test(sym) && !sym.startsWith('NIFTY') && !sym.startsWith('BANK') && !sym.startsWith('FINN')) return true;
  return false;
}

console.log("HSI:", "NSESymbol:", isNSESymbol("HSI", "HKEX"), "24x7:", is24x7Symbol("HSI", "HKEX"));
console.log("EURJPY:", "NSESymbol:", isNSESymbol("EURJPY", ""), "24x7:", is24x7Symbol("EURJPY", ""));
