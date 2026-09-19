/**
 * TLCS Black Box Signal Engine Daemon - PM2 Process Configuration
 * ===============================================================
 * Run with PM2 on any Linux, Mac, or Windows server:
 *   pm2 start ecosystem.config.js
 *   pm2 logs tlcs-daemon
 *   pm2 restart tlcs-daemon
 *   pm2 save && pm2 startup
 */

module.exports = {
  apps: [
    {
      name: "tlcs-daemon",
      script: "run_daemon.py",
      interpreter: "python3",
      cwd: __dirname,
      args: ["--markets", "ALL"],
      autorestart: true,
      watch: false,
      max_memory_restart: "1G",
      restart_delay: 5000,
      env: {
        PYTHONUNBUFFERED: "1",
        TZ: "Asia/Kolkata"
      }
    }
  ]
};
