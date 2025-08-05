#!/bin/bash

echo "🚀 Installing VLESS Bot Dependencies on VPS"
echo "============================================="

# Navigate to bot directory
cd /opt/vless_bot

# Activate virtual environment
source venv/bin/activate

# Install minimal requirements
echo "📦 Installing Python packages..."
pip install python-telegram-bot[job-queue]>=20.0
pip install python-dotenv>=1.0.0
pip install grpcio>=1.60.0
pip install grpcio-tools>=1.60.0

echo "✅ Dependencies installed successfully!"
echo ""
echo "🧪 Testing the bot..."
python vless_only_bot.py 