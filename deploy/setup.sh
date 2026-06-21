#!/usr/bin/env bash
# One-shot setup for a fresh Ubuntu VM (Oracle Cloud Always Free, etc.).
# Run from the repo root:  bash deploy/setup.sh
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SERVICE_USER="$(whoami)"
cd "$REPO_DIR"

echo ">> Installing system packages..."
sudo apt-get update -qq
sudo apt-get install -y -qq python3-venv git

echo ">> Creating virtualenv + installing deps..."
python3 -m venv .venv
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
  chmod 600 .env
  echo ""
  echo "!! Created .env from template. Edit it now with your credentials:"
  echo "     nano $REPO_DIR/.env"
  echo "   Then re-run this script to install the service."
  exit 0
fi
chmod 600 .env

echo ">> Installing systemd service (user=$SERVICE_USER)..."
sudo sed -e "s|^User=.*|User=$SERVICE_USER|" \
         -e "s|^WorkingDirectory=.*|WorkingDirectory=$REPO_DIR|" \
         -e "s|^EnvironmentFile=.*|EnvironmentFile=$REPO_DIR/.env|" \
         -e "s|^ExecStart=.*|ExecStart=$REPO_DIR/.venv/bin/python scheduler.py|" \
         deploy/tnp-notifier.service | sudo tee /etc/systemd/system/tnp-notifier.service >/dev/null

sudo systemctl daemon-reload
sudo systemctl enable --now tnp-notifier

echo ""
echo ">> Done. The notifier is running and will auto-start on boot."
echo "   Watch logs:   journalctl -u tnp-notifier -f"
echo "   Restart:      sudo systemctl restart tnp-notifier"
