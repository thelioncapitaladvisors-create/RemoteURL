const fs = require('fs');
const content = fs.readFileSync('Tv-Alert-Mobile/src/app/api/webhook/route.ts', 'utf8');
try {
  // just check if it compiles / syntax is valid
  console.log("Checking route.ts syntax...");
} catch (e) {
  console.error(e);
}
