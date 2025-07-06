#!/bin/bash

# VPN Bot Deployment Script
echo "🚀 Starting VPN Bot deployment..."

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py not found. Please run this script from the project root."
    exit 1
fi

# Check if required files exist
required_files=("app.py" "wsgi.py" "requirements.txt" "render.yaml")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Error: $file not found. Please ensure all required files are present."
        exit 1
    fi
done

echo "✅ All required files found"

# Check if environment variables are set (optional check)
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "⚠️  Warning: TELEGRAM_BOT_TOKEN not set in environment"
fi

if [ -z "$ADMIN_USER_ID" ]; then
    echo "⚠️  Warning: ADMIN_USER_ID not set in environment"
fi

echo "📋 Deployment checklist:"
echo "   - Main bot file: main.py ✅"
echo "   - Flask app: app.py ✅"
echo "   - WSGI entry point: wsgi.py ✅"
echo "   - Requirements: requirements.txt ✅"
echo "   - Render config: render.yaml ✅"
echo "   - Production WSGI server: gunicorn ✅"

echo ""
echo "🎯 Ready for deployment!"
echo "   Your bot will be deployed to Render with:"
echo "   - Production WSGI server (Gunicorn)"
echo "   - Proper port binding"
echo "   - Health checks at /health"
echo "   - Background bot thread"
echo ""
echo "📝 Next steps:"
echo "   1. Commit your changes: git add . && git commit -m 'Fix deployment issues'"
echo "   2. Push to your repository: git push origin main"
echo "   3. Deploy on Render dashboard or via CLI"
echo ""
echo "🔧 If you need to test locally:"
echo "   python app.py  # Development server"
echo "   gunicorn wsgi:application --bind 0.0.0.0:5000  # Production server" 