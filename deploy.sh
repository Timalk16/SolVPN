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

# Check for required files
echo "🔍 Checking required files..."
required_files=("app.py" "main.py" "requirements.txt" "render.yaml" "config.py")
missing_files=()

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -ne 0 ]; then
    echo "❌ Missing required files: ${missing_files[*]}"
    exit 1
fi

echo "✅ All required files found"

# Check if Flask is in requirements.txt
if ! grep -q "Flask" requirements.txt; then
    echo "❌ Flask not found in requirements.txt"
    exit 1
fi

echo "✅ Flask dependency found"

# Run health check
echo "🔍 Running health checks..."
python health_check.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Health checks passed!"
    echo ""
    echo "📋 Render Deployment Steps:"
    echo "1. Push your code to GitHub:"
    echo "   git add ."
    echo "   git commit -m 'Prepare for Render deployment'"
    echo "   git push"
    echo ""
    echo "2. Deploy to Render:"
    echo "   - Go to https://render.com"
    echo "   - Sign up/login"
    echo "   - Click 'New +' → 'Web Service'"
    echo "   - Connect your GitHub repository"
    echo "   - Render will auto-detect render.yaml"
    echo "   - Click 'Create Web Service'"
    echo ""
    echo "3. Configure Environment Variables:"
    echo "   - Go to your service → Environment tab"
    echo "   - Add all variables from your .env file"
    echo "   - Click 'Save Changes'"
    echo ""
    echo "4. Deploy:"
    echo "   - Go to 'Manual Deploy' tab"
    echo "   - Click 'Deploy latest commit'"
    echo "   - Wait for build to complete (2-3 minutes)"
    echo ""
    echo "5. Verify:"
    echo "   - Check logs in Render dashboard"
    echo "   - Visit your service URL"
    echo "   - Test health endpoint: /health"
    echo "   - Test your bot on Telegram"
    echo ""
    echo "📖 For detailed instructions, see RENDER_DEPLOYMENT.md"
    echo ""
    echo "🎉 Your bot will be running 24/7 once deployed!"
else
    echo ""
    echo "❌ Health checks failed. Please fix the issues above before deploying."
    exit 1
fi 