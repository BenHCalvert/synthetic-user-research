#!/usr/bin/env bash
# Land Parcel Monitor — VPS setup script
# Run as root: bash setup.sh
# Tested on Ubuntu 24.04 ARM (Hetzner CAX series)
set -euo pipefail

INSTALL_DIR="/opt/land-monitor"
SERVICE_USER="landmonitor"
PYTHON="python3"

echo "==> Creating system user..."
id -u "$SERVICE_USER" &>/dev/null || useradd -r -s /usr/sbin/nologin "$SERVICE_USER"

echo "==> Installing system packages..."
apt-get update -qq
apt-get install -y python3 python3-venv python3-pip nodejs npm git curl

echo "==> Creating install directory..."
mkdir -p "$INSTALL_DIR"
cp -r backend frontend data requirements.txt .env.example "$INSTALL_DIR/"

echo "==> Creating Python virtual environment..."
$PYTHON -m venv "$INSTALL_DIR/venv"
"$INSTALL_DIR/venv/bin/pip" install --quiet --upgrade pip
"$INSTALL_DIR/venv/bin/pip" install --quiet -r "$INSTALL_DIR/requirements.txt"

echo "==> Installing Playwright browsers (Chromium)..."
"$INSTALL_DIR/venv/bin/playwright" install chromium
"$INSTALL_DIR/venv/bin/playwright" install-deps chromium

echo "==> Building React frontend..."
cd "$INSTALL_DIR/frontend"
npm install --silent
npm run build
echo "   Frontend built to $INSTALL_DIR/frontend/dist"

echo "==> Configuring environment..."
if [ ! -f "$INSTALL_DIR/.env" ]; then
    cp "$INSTALL_DIR/.env.example" "$INSTALL_DIR/.env"
    echo ""
    echo "   ⚠️  Edit $INSTALL_DIR/.env and set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID"
fi

echo "==> Setting permissions..."
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
chmod 750 "$INSTALL_DIR/data"
chmod 640 "$INSTALL_DIR/.env"

echo "==> Installing systemd service..."
cp land-monitor.service /etc/systemd/system/land-monitor.service
systemctl daemon-reload
systemctl enable land-monitor

echo ""
echo "======================================"
echo "  Setup complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "  1. Edit /opt/land-monitor/.env — set Telegram credentials"
echo "  2. systemctl start land-monitor"
echo "  3. systemctl status land-monitor"
echo "  4. Dashboard available at http://YOUR_VPS_IP:8000"
echo ""
echo "Logs: journalctl -u land-monitor -f"
