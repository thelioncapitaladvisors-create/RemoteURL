const body = { exit_time: "1721033100000" };
let exit_at = new Date().toISOString();
if (body.exit_time || body.exit_ts) {
    const rawTs = body.exit_time || body.exit_ts;
    const ts = Number(rawTs);
    if (!isNaN(ts) && ts > 1e12) exit_at = new Date(ts).toISOString();
    else if (!isNaN(ts) && ts > 1e9) exit_at = new Date(ts * 1000).toISOString();
}
console.log(exit_at);
