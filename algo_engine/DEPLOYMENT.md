# TLCS Black Box Signal Engine Daemon — Production VPS Cloud Deployment Guide

This guide provides end-to-end instructions for deploying the **TLCS Black Box Signal Engine Daemon v2.0** on a 24/7 cloud Virtual Private Server (VPS). 

---

## 1. Cloud VPS Hardware Requirements

The daemon is engineered in Python with an asynchronous event-driven loop and in-memory candle aggregation. It is extremely lightweight:

| Component | Minimum Spec | Recommended Spec |
| :--- | :--- | :--- |
| **vCPU** | 1 Core | 1 – 2 Cores |
| **RAM** | 1 GB | 2 GB |
| **Storage** | 10 GB SSD | 20 GB SSD |
| **OS** | Ubuntu 22.04 / 24.04 LTS | Ubuntu 22.04 LTS / Debian 12 |
| **Estimated Cost** | ~$4 – $6 / month | ~$5 – $10 / month |

### Recommended Cloud Providers
- **DigitalOcean**: Basic Droplet (1 vCPU, 1GB RAM) – \$6/mo
- **Hetzner Cloud**: CX22 (2 vCPU, 4GB RAM) – €3.79/mo
- **AWS EC2**: `t3.micro` (free tier) or `t3.small` (\$15/mo)
- **Linode / Akamai**: Shared 1GB Plan – \$5/mo

---

## 2. Quickstart: 1-Click Automated Setup

On your fresh VPS instance, clone or transfer the `algo_engine` directory, and run the automated setup script:

```bash
cd /opt
# Clone or upload your repository
git clone <YOUR_GIT_REPO_URL> tlcs
cd tlcs/algo_engine

# Make setup script executable and run
chmod +x scripts/setup_vps.sh
sudo ./scripts/setup_vps.sh
```

The script will prompt you to choose between **Docker** (recommended) or **Native Systemd**.

---

## 3. Deployment Method A: Docker Compose (Recommended)

Docker isolates all Python dependencies and guarantees zero dependency conflicts.

### Step 1: Configure Environment Variables
Copy and customize `.env.example`:
```bash
cp .env.example .env
nano .env
```
Ensure your `SUPABASE_URL`, `SUPABASE_KEY`, `DHAN_CLIENT_ID`, and `TELEGRAM_BOT_TOKEN` are populated.

### Step 2: Build & Start Container in Background
```bash
# Build and launch daemon as a persistent detached container
docker compose up -d --build
```

### Step 3: Monitor Live Logs
```bash
# Stream live tick evaluation and heartbeat logs
docker compose logs -f

# Check container status and resource utilization
docker stats tlcs-blackbox-daemon
```

### Step 4: Management Commands
```bash
# Restart container (e.g. after editing .env)
docker compose restart

# Stop daemon
docker compose down

# Re-pull updates and rebuild
git pull origin main
docker compose up -d --build
```

---

## 4. Deployment Method B: Native Systemd Service

If you prefer running directly on the Linux host without Docker:

### Step 1: Install Dependencies
```bash
sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv git
```

### Step 2: Set Up Directory & Virtualenv
```bash
sudo mkdir -p /opt/tlcs
sudo chown -R $USER:$USER /opt/tlcs
cp -r algo_engine /opt/tlcs/
cd /opt/tlcs/algo_engine

python3 -m venv venv
venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt
```

### Step 3: Configure `.env`
```bash
cp .env.example .env
nano .env
```

### Step 4: Install and Enable Systemd Service
```bash
# Copy systemd unit file to system directory
sudo cp systemd/algo_engine.service /etc/systemd/system/

# Adjust user if not 'ubuntu'
sudo sed -i "s/User=ubuntu/User=$USER/g" /etc/systemd/system/algo_engine.service
sudo sed -i "s/Group=ubuntu/Group=$USER/g" /etc/systemd/system/algo_engine.service

# Reload systemd and enable service on system boot
sudo systemctl daemon-reload
sudo systemctl enable algo_engine

# Start the service
sudo systemctl start algo_engine
```

### Step 5: Systemd Operational Commands
```bash
# View live output and heartbeat logs
sudo journalctl -u algo_engine -f

# Check status
sudo systemctl status algo_engine

# Restart service
sudo systemctl restart algo_engine

# Stop service
sudo systemctl stop algo_engine
```

---

## 5. Deployment Method C: PM2 Process Manager

If you have Node.js / PM2 already installed:

```bash
# Start daemon under PM2
pm2 start ecosystem.config.js

# Stream live output
pm2 logs tlcs-daemon

# Save PM2 state across server reboots
pm2 save
pm2 startup
```

---

## 6. Daily Operational Procedures

### 1. Indian Markets (DhanHQ Daily Token Refresh)
- DhanHQ requires a fresh JWT access token every 24 hours.
- Generate your token from the Dhan Developer Portal each morning before 9:00 AM IST.
- Update `DHAN_ACCESS_TOKEN` in `.env` and run:
  ```bash
  # For Docker:
  docker compose restart
  
  # For Systemd:
  sudo systemctl restart algo_engine
  ```

### 2. Crypto, Forex & NYMEX Markets
- **Binance WebSocket** (Crypto top 25) requires zero API keys and streams 24/7/365.
- Global and Forex feeds run continuously with automated reconnection and bar aggregation.

### 3. Verification & Live Telemetry
- Open the **TLCS Mobile Terminal** (`page.tsx`) or **Web Dashboard** (`dashboard.html`).
- Switch the engine selector to `SHADOW DB`.
- Check the **Parity Audit Screen** to verify the top 4 KPIs:
  - **Parity Score** (Target: ≥99%)
  - **Level Fidelity** (±0.1% bound on Entry, SL, TP1–4)
  - **Execution Lead** (Positive sub-second lead over TradingView)
  - **Outcome Consistency** (100% mathematical match on realized returns)
