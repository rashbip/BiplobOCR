#!/bin/bash
set -e

# Configuration
INSTALL_DIR="/opt/BiplobOCR"
BIN_DIR="/usr/local/bin"
DESKTOP_DIR="/usr/share/applications"
ICON_DIR="/usr/share/icons/hicolor/256x256/apps"
APPNAME="BiplobOCR"

# Ensure root
if [ "$EUID" -ne 0 ]; then 
  echo "Please run as root (sudo ./uninstall.sh)"
  exit 1
fi

echo "Uninstalling $APPNAME..."

# 1. Remove binary and opt folder
echo "[1/4] Removing Application Files..."
rm -rf "$INSTALL_DIR"
rm -f "$BIN_DIR/biplobocr"

# 2. Remove Desktop Entry and Icon
echo "[2/4] Removing Menu Entries..."
rm -f "$DESKTOP_DIR/$APPNAME.desktop"
rm -f "$ICON_DIR/$APPNAME.png"

# 3. Cache & User Data (Optional/Prompt?)
# The user asked to remove "every track". 
# We should try to find where we put data.
echo "[3/4] Cleaning up system caches..."
if command -v gtk-update-icon-cache &> /dev/null; then
    gtk-update-icon-cache /usr/share/icons/hicolor || true
fi

# 4. User-specific data (emojis, tessdata etc)
# This usually lives in ~/.local/share/BiplobOCR
# Since we are root, we can't easily find every user's home, 
# but we can try to find the person who called sudo.
REAL_USER=$SUDO_USER
if [ -n "$REAL_USER" ]; then
    USER_HOME=$(getent passwd "$REAL_USER" | cut -d: -f6)
    DATA_PATH="$USER_HOME/.local/share/$APPNAME"
    CONFIG_PATH="$USER_HOME/.config/$APPNAME"
    
    if [ -d "$DATA_PATH" ] || [ -f "$USER_HOME/config.json" ]; then
        echo "[4/4] Found user data for '$REAL_USER' at $DATA_PATH"
        read -p "Do you want to remove user data and configuration? (y/N): " confirm
        if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
            echo "Deleting user data..."
            rm -rf "$DATA_PATH"
            rm -rf "$CONFIG_PATH"
            rm -f "$USER_HOME/config.json"
            rm -f "$USER_HOME/history.json"
        fi
    fi
else
    echo "[4/4] Skipping user data cleanup (could not determine calling user)."
fi

echo "-----------------------------------"
echo "$APPNAME Uninstalled Successfully."
echo "-----------------------------------"
