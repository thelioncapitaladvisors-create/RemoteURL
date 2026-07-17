const fetch = require('node-fetch');

async function test(symbol) {
    const url = `https://query1.finance.yahoo.com/v8/finance/chart/${symbol}?interval=1d&range=1d`;
    try {
        const res = await fetch(url);
        const data = await res.json();
        const price = data.chart?.result?.[0]?.meta?.regularMarketPrice;
        console.log(symbol, '->', price);
    } catch (e) {
        console.log(symbol, '-> ERROR', e.message);
    }
}

(async () => {
    await test('RELIANCE.NS');
    await test('GOLD.MC'); // let's see if this works
    await test('MGC=F'); // Micro Gold
    await test('CL=F');
    await test('^DJI');
})();
