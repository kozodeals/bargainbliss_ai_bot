#!/bin/bash

# BargainBliss AI Bot - Deployment Script
# This script sets up the bot on a fresh Ubuntu server

echo "🚀 BargainBliss AI Bot - Deployment Script"
echo "=========================================="

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages
echo "📦 Installing required packages..."
sudo apt install python3 python3-pip git screen curl -y

# Create bot directory
echo "📁 Setting up bot directory..."
mkdir -p /opt/bargainbliss_bot
cd /opt/bargainbliss_bot

# Copy bot files (assuming they're in current directory)
echo "📋 Copying bot files..."
cp -r . /opt/bargainbliss_bot/

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

# Create systemd service
echo "⚙️ Creating systemd service..."
sudo tee /etc/systemd/system/bargainbliss-bot.service > /dev/null <<EOF
[Unit]
Description=BargainBliss AI Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/bargainbliss_bot
ExecStart=/usr/bin/python3 /opt/bargainbliss_bot/bargainbliss_ai_bot.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
echo "🚀 Enabling and starting bot service..."
sudo systemctl daemon-reload
sudo systemctl enable bargainbliss-bot.service
sudo systemctl start bargainbliss-bot.service

# Check status
echo "📊 Checking bot status..."
sudo systemctl status bargainbliss-bot.service --no-pager

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 Useful commands:"
echo "  Check status: sudo systemctl status bargainbliss-bot"
echo "  View logs: sudo journalctl -u bargainbliss-bot -f"
echo "  Restart bot: sudo systemctl restart bargainbliss-bot"
echo "  Stop bot: sudo systemctl stop bargainbliss-bot"
echo ""
echo "🔗 Share your bot with users via Telegram!"
echo "   Users can only interact via Telegram - no server access needed." 