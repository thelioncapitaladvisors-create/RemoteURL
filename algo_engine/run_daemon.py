#!/usr/bin/env python3
"""
algo_engine.run_daemon — Universal Daemon Launcher
=================================================

Provides a foolproof executable entrypoint for the TLCS Black Box Signal Engine Daemon.
Ensures correct module resolution regardless of whether it is launched from:
  - Inside algo_engine/ (`python3 run_daemon.py`)
  - The project root (`python3 algo_engine/run_daemon.py`)
  - A Docker container (`python3 algo_engine/run_daemon.py`)
  - A systemd service or PM2 process manager
"""

from __future__ import annotations
import os
import sys
from pathlib import Path

# Add project root and algo_engine directory to sys.path
_current_dir = Path(__file__).resolve().parent
_parent_dir = _current_dir.parent

if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))
if str(_current_dir) not in sys.path:
    sys.path.insert(0, str(_current_dir))

# Ensure working directory allows finding .env
if not os.path.exists(".env") and os.path.exists(str(_current_dir / ".env")):
    os.chdir(str(_current_dir))

from algo_engine.engine_daemon import main

if __name__ == "__main__":
    main()
