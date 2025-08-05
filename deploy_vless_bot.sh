#!/bin/bash

# VLESS Bot Deployment Script for VPS
# This script uploads and sets up the VLESS bot on your VPS

set -e

# Configuration
VPS_IP="77.110.110.205"
VPS_USER="root"
BOT_DIR="/opt/vless_bot"
SERVICE_NAME="vless-bot"

echo "🚀 Starting VLESS Bot Deployment to VPS..."

# Step 1: Create deployment package
echo "📦 Creating deployment package..."
tar -czf vless_bot_deploy.tar.gz \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='test_*.py' \
    --exclude='start_test_bot.py' \
    --exclude='test_xray_*.py' \
    --exclude='*.log' \
    --exclude='*.txt' \
    --exclude='*.json' \
    --exclude='*.md' \
    --exclude='backup' \
    --exclude='source' \
    --exclude='assets' \
    --exclude='locales' \
    vless_only_bot.py config.py database.py vless_utils.py \
    requirements.txt \
    xray_proto_files/ \
    app/ common/ core/

# Step 2: Upload to VPS
echo "📤 Uploading to VPS..."
scp vless_bot_deploy.tar.gz $VPS_USER@$VPS_IP:/tmp/

# Step 3: Setup on VPS
echo "🔧 Setting up on VPS..."
ssh $VPS_USER@$VPS_IP << 'EOF'
set -e

# Create bot directory
sudo mkdir -p /opt/vless_bot
cd /opt/vless_bot

# Extract bot files
sudo tar -xzf /tmp/vless_bot_deploy.tar.gz
sudo rm /tmp/vless_bot_deploy.tar.gz

# Install Python dependencies
sudo apt update
sudo apt install -y python3 python3-pip python3-venv

# Create virtual environment
sudo python3 -m venv venv
sudo chown -R $USER:$USER venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Create systemd service
sudo tee /etc/systemd/system/vless-bot.service > /dev/null << 'SERVICE_EOF'
[Unit]
Description=VLESS Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/vless_bot
Environment=PATH=/opt/vless_bot/venv/bin
ExecStart=/opt/vless_bot/venv/bin/python vless_only_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE_EOF

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable vless-bot

echo "✅ VLESS Bot setup complete!"
echo "📝 Next steps:"
echo "1. Set environment variables in /opt/vless_bot/.env"
echo "2. Start the service: sudo systemctl start vless-bot"
echo "3. Check status: sudo systemctl status vless-bot"
echo "4. View logs: sudo journalctl -u vless-bot -f"
EOF

# Step 4: Create environment file template
echo "📝 Creating environment file template..."
cat > vless_bot.env.template << 'ENV_EOF'
# VLESS Bot Environment Variables
# Copy this to /opt/vless_bot/.env on your VPS

# Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
ADMIN_USER_ID=your_user_id_here

# VLESS Configuration (for localhost connection)
VLESS_HOST=127.0.0.1
VLESS_API_PORT=62789
VLESS_PUBLIC_HOST=77.110.110.205
VLESS_PORT=443
VLESS_SNI=www.github.com
VLESS_PUBLIC_KEY=-UjZAt_uWgBbne-xawPtZnWgMQD2-xtxRMaztwvTkUc
VLESS_SHORT_ID=0123abcd

# Payment Configuration (optional - set dummy values if not using)
CRYPTOBOT_TESTNET_API_TOKEN=dummy_testnet_token
CRYPTOBOT_MAINNET_API_TOKEN=dummy_mainnet_token
ENV_EOF

echo "✅ Deployment package created!"
echo ""
echo "📋 Manual steps to complete deployment:"
echo "1. Copy vless_bot.env.template to your VPS:"
echo "   scp vless_bot.env.template root@77.110.110.205:/opt/vless_bot/.env"
echo ""
echo "2. SSH to your VPS and edit the environment file:"
echo "   ssh root@77.110.110.205"
echo "   nano /opt/vless_bot/.env"
echo ""
echo "3. Start the bot service:"
echo "   sudo systemctl start vless-bot"
echo "   sudo systemctl status vless-bot"
echo ""
echo "4. View logs:"
echo "   sudo journalctl -u vless-bot -f"
echo ""
echo "🎉 Your VLESS bot will be running on the VPS!" 