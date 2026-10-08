#!/bin/bash
export PATH="/Applications/anaconda3/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export PYTHONPATH="/Users/vishant/Documents/Project:/Users/vishant/Documents/Project/algo_engine"
export PYTHONUNBUFFERED="1"
cd /Users/vishant/Documents/Project/algo_engine
exec /Applications/anaconda3/bin/python3 /Users/vishant/Documents/Project/algo_engine/run_nse100_scanner.py --interval 900
