const fs = require('fs');
const path = require('path');

const files = [
    '/Users/vishant/Documents/Project/TLCS_Website_Deploy/trade-metrics.js',
    '/Users/vishant/Documents/Project/TLCS_Website_Deploy/scanner.js',
    '/Users/vishant/Documents/Project/TLCS_Website_Deploy/commodity-scanner.js',
    '/Users/vishant/Documents/Project/TLCS_Website_Deploy/dashboard.html',
    '/Users/vishant/Documents/Project/Tv-Alert-Mobile/src/app/page.tsx',
    '/Users/vishant/Documents/Project/.agents/AGENTS.md',
    '/Users/vishant/Documents/Project/TLCS_Website_Deploy/backfill-weekly-logs.js',
    '/Users/vishant/Documents/Project/TLCS_Website_Deploy/netlify/functions/cron-instagram-stats.js',
    '/Users/vishant/Documents/Project/TLCS_Website_Deploy/netlify/functions/cron-weekly-logs.js'
];

for (const file of files) {
    if (!fs.existsSync(file)) {
        console.log(`Skipping missing file: ${file}`);
        continue;
    }
    let content = fs.readFileSync(file, 'utf8');

    const regex = /([ \t]*)(?:\/\/[^\n]*\n)*([ \t]*)(if\s*\([^)]*includes\('CANCEL'\)[^]*?return\s*'CANCELLED';\n)[ \t]*(if\s*\([^)]*includes\('EXPIRED'\)[^]*?return\s*'CANCELLED';\n)\s*(?:\/\/[^\n]*\n)*\s*(let\s*meta\s*=\s*s\.metadata[^]*?return\s*'BREAKEVEN';\s*(?:\/\/[^\n]*\n)?\s*\}\n\s*\})/g;

    const newContent = content.replace(regex, (match, p1, p2, cancel1, cancel2, exactBlock) => {
        return `\n${p1}${exactBlock}\n\n${p1}${cancel1}${p1}${cancel2}`;
    });

    if (newContent !== content) {
        fs.writeFileSync(file, newContent, 'utf8');
        console.log(`Updated ${file}`);
    } else {
        console.log(`No match found in ${file}`);
    }
}
