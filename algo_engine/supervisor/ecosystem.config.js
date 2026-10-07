module.exports = {
  apps: [
    {
      name: 'tlcs-nse100-scanner',
      script: 'run_nse100_scanner.py',
      args: '--interval 900',
      cwd: '/Users/vishant/Documents/Project/algo_engine',
      interpreter: '/Applications/anaconda3/bin/python3',
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        PYTHONUNBUFFERED: '1'
      },
      out_file: './logs/scanner_stdout.log',
      error_file: './logs/scanner_stderr.log',
      merge_logs: true,
      time: true
    }
  ]
};
