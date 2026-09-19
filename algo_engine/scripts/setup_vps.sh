#!/usr/bin/env bash
# ==============================================================================
# TLCS Black Box Signal Engine Daemon - VPS Auto-Setup & Bootstrap Script
# ==============================================================================
# Supported OS: Ubuntu 20.04 / 22.04 / 24.04 LTS, Debian 11 / 12
# Usage:
#   chmod +x setup_vps.sh
#   sudo ./setup_vps.sh
# ==============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}      TLCS BLACK BOX SIGNAL ENGINE DAEMON - VPS SETUP (v2.0)     ${NC}"
echo -e "${BLUE}================================================================${NC}"

# Check for root/sudo
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}[ERROR] Please run as root or with sudo: sudo ./setup_vps.sh${NC}"
  exit 1
fi

CURRENT_DIR=$(pwd)
APP_DIR="/opt/tlcs/algo_engine"
ACTUAL_USER="${SUDO_USER:-$(whoami)}"

echo -e "\n${YELLOW}Choose your deployment method:${NC}"
echo "  1) Docker & Docker Compose (Recommended - isolated, portable, zero host dependencies)"
echo "  2) Native Systemd Service (Runs in a native Python virtualenv)"
read -rp "Select option [1 or 2, default 1]: " DEPLOY_MODE
DEPLOY_MODE=${DEPLOY_MODE:-1}

# ------------------------------------------------------------------------------
# Common Base Updates
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[1/3] Updating system packages and installing prerequisites...${NC}"
apt-get update -y
apt-get install -y --no-install-recommends \
    curl \
    git \
    ca-certificates \
    tzdata \
    htop

# Configure timezone to IST (Asia/Kolkata)
timedatectl set-timezone Asia/Kolkata || true

# ------------------------------------------------------------------------------
# Option 1: Docker & Docker Compose
# ------------------------------------------------------------------------------
if [ "$DEPLOY_MODE" = "1" ]; then
    echo -e "\n${BLUE}[2/3] Installing Docker & Docker Compose...${NC}"
    if ! command -v docker &> /dev/null; then
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        rm get-docker.sh
        systemctl enable --now docker
        usermod -aG docker "$ACTUAL_USER" || true
        echo -e "${GREEN}[OK] Docker installed successfully.${NC}"
    else
        echo -e "${GREEN}[OK] Docker is already installed.${NC}"
    fi

    # Install Docker Compose Plugin if missing
    apt-get install -y docker-compose-plugin || true

    echo -e "\n${BLUE}[3/3] Preparing container environment...${NC}"
    mkdir -p data logs
    chown -R "$ACTUAL_USER:$ACTUAL_USER" data logs

    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            echo -e "${YELLOW}[!] Created .env from .env.example. Please edit .env with your credentials!${NC}"
        else
            touch .env
        fi
    fi

    echo -e "\n${GREEN}================================================================${NC}"
    echo -e "${GREEN} Docker environment prepared successfully!                     ${NC}"
    echo -e "${GREEN}================================================================${NC}"
    echo -e "To launch your daemon now:"
    echo -e "  ${YELLOW}1. Edit credentials:${NC}      nano .env"
    echo -e "  ${YELLOW}2. Build & run in background:${NC} docker compose up -d --build"
    echo -e "  ${YELLOW}3. View live stream logs:${NC}  docker compose logs -f"
    echo -e "  ${YELLOW}4. Stop daemon:${NC}            docker compose down"

# ------------------------------------------------------------------------------
# Option 2: Native Systemd Service
# ------------------------------------------------------------------------------
else
    echo -e "\n${BLUE}[2/3] Installing Python 3.11/3.12 and Virtualenv...${NC}"
    apt-get install -y python3 python3-pip python3-venv

    echo -e "\n${BLUE}[3/3] Setting up application in ${APP_DIR}...${NC}"
    mkdir -p "/opt/tlcs"
    
    # Copy files if not already in /opt/tlcs/algo_engine
    if [ "$CURRENT_DIR" != "$APP_DIR" ]; then
        echo "Copying files from $CURRENT_DIR to $APP_DIR..."
        mkdir -p "$APP_DIR"
        cp -r "$CURRENT_DIR"/* "$APP_DIR"/
    fi

    # Create virtual environment
    if [ ! -d "$APP_DIR/venv" ]; then
        echo "Creating Python virtualenv..."
        python3 -m venv "$APP_DIR/venv"
    fi

    echo "Installing Python dependencies..."
    "$APP_DIR/venv/bin/pip" install --upgrade pip
    "$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"

    # Ensure directories & permissions
    mkdir -p "$APP_DIR/data" "$APP_DIR/logs"
    chmod +x "$APP_DIR/run_daemon.py"
    chown -R "$ACTUAL_USER:$ACTUAL_USER" "/opt/tlcs"

    if [ ! -f "$APP_DIR/.env" ] && [ -f "$APP_DIR/.env.example" ]; then
        cp "$APP_DIR/.env.example" "$APP_DIR/.env"
        chown "$ACTUAL_USER:$ACTUAL_USER" "$APP_DIR/.env"
    fi

    # Install Systemd Unit
    echo "Installing systemd service..."
    sed -i "s/User=ubuntu/User=$ACTUAL_USER/g" "$APP_DIR/systemd/algo_engine.service"
    sed -i "s/Group=ubuntu/Group=$ACTUAL_USER/g" "$APP_DIR/systemd/algo_engine.service"
    cp "$APP_DIR/systemd/algo_engine.service" /etc/systemd/system/algo_engine.service

    systemctl daemon-reload
    systemctl enable algo_engine

    echo -e "\n${GREEN}================================================================${NC}"
    echo -e "${GREEN} Native Systemd service installed successfully!                ${NC}"
    echo -e "${GREEN}================================================================${NC}"
    echo -e "Next steps:"
    echo -e "  ${YELLOW}1. Edit credentials:${NC}      nano ${APP_DIR}/.env"
    echo -e "  ${YELLOW}2. Start daemon service:${NC}   sudo systemctl start algo_engine"
    echo -e "  ${YELLOW}3. View live stream logs:${NC}  sudo journalctl -u algo_engine -f"
    echo -e "  ${YELLOW}4. Check service status:${NC}   sudo systemctl status algo_engine"
    echo -e "  ${YELLOW}5. Restart service:${NC}        sudo systemctl restart algo_engine"
fi
