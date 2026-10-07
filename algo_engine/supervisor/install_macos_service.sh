#!/bin/bash
# Install & start TLCS NSE100 Scanner as persistent macOS background service
PLIST_NAME="com.tlcs.nse100scanner.plist"
SOURCE_PLIST="/Users/vishant/Documents/Project/algo_engine/supervisor/${PLIST_NAME}"
TARGET_DIR="${HOME}/Library/LaunchAgents"
TARGET_PLIST="${TARGET_DIR}/${PLIST_NAME}"

mkdir -p "${TARGET_DIR}"
mkdir -p "/Users/vishant/Documents/Project/algo_engine/logs"

# Unload previous instance if active
launchctl unload "${TARGET_PLIST}" 2>/dev/null

# Copy plist and load
cp "${SOURCE_PLIST}" "${TARGET_PLIST}"
launchctl load "${TARGET_PLIST}"

echo "TLCS NSE100 Scanner successfully installed and loaded into launchd!"
echo "Status check: launchctl list | grep tlcs"
echo "Log stdout: tail -f /Users/vishant/Documents/Project/algo_engine/logs/scanner_stdout.log"
echo "Log stderr: tail -f /Users/vishant/Documents/Project/algo_engine/logs/scanner_stderr.log"
