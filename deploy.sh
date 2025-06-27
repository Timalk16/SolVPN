#!/bin/bash

# VPN Bot Deployment Script
echo "🚀 VPN Bot Deployment Helper"
echo "============================"

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "❌ Git repository not found. Please initialize git first:"
    echo "   git init"
    echo "   git add ."
    echo "   git commit -m 'Initial commit'"
    echo "   git remote add origin YOUR_GITHUB_REPO_URL"
    echo "   git push -u origin main"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Please create one with your environment variables:"
    echo ""
    echo "TELEGRAM_BOT_TOKEN=your_bot_token_here"
    echo "ADMIN_USER_ID=your_telegram_user_id"
    echo "CRYPTOBOT_TESTNET_API_TOKEN=your_cryptobot_token"
    echo "CRYPTOBOT_MAINNET_API_TOKEN=your_mainnet_token"
    echo "OUTLINE_API_URL_GERMANY=your_germany_server_url"
    echo "OUTLINE_CERT_SHA256_GERMANY=your_germany_cert_sha256"
    echo "OUTLINE_API_URL_FRANCE=your_france_server_url"
    echo "OUTLINE_CERT_SHA256_FRANCE=your_france_cert_sha256"
    echo "YOOKASSA_SHOP_ID=your_yookassa_shop_id"
    echo "YOOKASSA_SECRET_KEY=your_yookassa_secret_key"
    echo ""
    echo "Then run this script again."
    exit 1
fi

# Run health check
echo "🔍 Running health checks..."
python health_check.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Health checks passed!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Push your code to GitHub:"
    echo "   git add ."
    echo "   git commit -m 'Prepare for deployment'"
    echo "   git push"
    echo ""
    echo "2. Deploy to Railway:"
    echo "   - Go to https://railway.app"
    echo "   - Sign up/login"
    echo "   - Click 'New Project' → 'Deploy from GitHub repo'"
    echo "   - Select your repository"
    echo "   - Add environment variables in Railway dashboard"
    echo "   - Deploy!"
    echo ""
    echo "3. Alternative: Deploy to Render:"
    echo "   - Go to https://render.com"
    echo "   - Create new Web Service"
    echo "   - Connect your GitHub repo"
    echo "   - Set build command: pip install -r requirements.txt"
    echo "   - Set start command: python main.py"
    echo "   - Add environment variables"
    echo ""
    echo "🎉 Your bot will be running 24/7 once deployed!"
else
    echo ""
    echo "❌ Health checks failed. Please fix the issues above before deploying."
    exit 1
fi 