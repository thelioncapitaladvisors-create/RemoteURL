import os

file_path = '/Users/vishant/Documents/Project/.agents/AGENTS.md'
with open(file_path, 'a') as f:
    f.write('\n## Vercel Deployment Protocol (Mobile App)\n')
    f.write('- Changes pushed to the `thelioncapital-alerts` repository (for `market-store.online`) may not always automatically trigger a Vercel deployment.\n')
    f.write('- If a recent commit is not reflecting on the live mobile app, manually verify the last deployment timestamp on the Vercel Dashboard and trigger a redeploy if necessary.\n')
    f.write('\n## Standard Strategy Filters\n')
    f.write('- The 6 standard strategy filters (`LONG MISSILE`, `SHORT MISSILE`, `LONG SCALP`, `SHORT SCALP`, `LONG LIGHTNING`, `SHORT LIGHTNING`) are permanently hardcoded in the INSIGHTS tab of the mobile app to ensure they remain visible even on days with 0 active trades.\n')
