#!/bin/bash

# Enhanced VLESS Bot Setup Script
# This script sets up the enhanced VLESS bot on your VPS server

echo "🚀 Setting up Enhanced VLESS Bot..."

# Update system packages
echo "📦 Updating system packages..."
apt update -y

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
apt install -y python3 python3-pip python3-venv

# Create virtual environment
echo "🔧 Creating Python virtual environment..."
python3 -m venv vless_bot_env
source vless_bot_env/bin/activate

# Install required Python packages
echo "📚 Installing Python packages..."
pip install python-telegram-bot python-dotenv grpcio grpcio-tools

# Make scripts executable
echo "🔐 Setting executable permissions..."
chmod +x vless_only_bot_enhanced.py
chmod +x test_enhanced_vless_bot_simple.py

# Create .env template
echo "📝 Creating .env template..."
cat > .env.template << 'EOF'
# Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
ADMIN_USER_ID=your_telegram_user_id

# Management Mode (optional, defaults to 'grpc')
MANAGEMENT_MODE=grpc  # or 'config_file'

# VLESS Configuration (for gRPC mode)
VLESS_HOST=127.0.0.1
VLESS_API_PORT=62789
VLESS_PUBLIC_HOST=77.110.110.205
VLESS_PORT=443
VLESS_SNI=www.microsoft.com
VLESS_PUBLIC_KEY=your_public_key_here
VLESS_SHORT_ID=your_short_id_here
EOF

# Create systemd service file
echo "🔧 Creating systemd service..."
cat > /etc/systemd/system/vless-bot.service << 'EOF'
[Unit]
Description=Enhanced VLESS Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root
Environment=PATH=/root/vless_bot_env/bin
ExecStart=/root/vless_bot_env/bin/python3 /root/vless_only_bot_enhanced.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
systemctl daemon-reload

echo ""
echo "✅ Setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Copy .env.template to .env and configure your settings:"
echo "   cp .env.template .env"
echo "   nano .env"
echo ""
echo "2. Test the bot:"
echo "   source vless_bot_env/bin/activate"
echo "   python3 test_enhanced_vless_bot_simple.py"
echo ""
echo "3. Start the bot:"
echo "   systemctl start vless-bot"
echo "   systemctl enable vless-bot"
echo ""
echo "4. Check status:"
echo "   systemctl status vless-bot"
echo ""
echo "5. View logs:"
echo "   journalctl -u vless-bot -f"
echo ""
echo "📖 For detailed instructions, see: ENHANCED_VLESS_BOT_README.md" 