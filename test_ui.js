function run() {
  const s = {'id': 'a7f11afe-d97e-4b3d-b591-ae14d6657e5e', 'symbol': 'AU200', 'type': 'SHORT SCALP', 'status': 'Completed TP1', 'outcome': 'LOSS', 'r_multiple': -1, 'entry': 8762, 'stop': 8735.9, 'exit_price': 8735.9};

  const resolveOutcome = (s) => {
      if (!s) return 'OPEN';
      
      const st = (s.status || '').toUpperCase();
      const o = (s.outcome || '').toUpperCase().trim();
      
      if (st.includes('TP') || st.includes('TARGET') || o === 'WIN') return 'WIN';
      if (st.includes('STOP') && !st.includes('TRAIL') && !st.includes('BREAK') && !st.includes('B/E')) return 'LOSS';
      if (o === 'LOSS') return 'LOSS';
      if (o === 'BREAKEVEN' || o === 'BREAK EVEN' || o === 'B/E' || st.includes('BREAK EVEN') || st.includes('BREAKEVEN') || st.includes('B/E')) return 'BREAKEVEN';

      let r = null;
      if (s.r_multiple != null) {
        const rm = parseFloat(String(s.r_multiple).replace(/[^\d.-]/g, ''));
        if (!isNaN(rm) && rm !== 0) r = rm;
      }
      
      if (r !== null) {
        if (r > 0) return 'WIN';
        if (r < 0) return 'LOSS';
      }
      
      if (st.includes('STOP') || st.includes('SL')) return 'LOSS';
      
      return 'OPEN';
  };

  const finalOutcome = resolveOutcome(s);
  return finalOutcome;
}
run();
