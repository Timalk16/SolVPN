#!/bin/bash

# VPN Bot VPS Deployment Script
# This script copies your existing bot files to a VPS

set -e

echo "🚀 VPN Bot VPS Deployment Script"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if VPS IP is provided
if [ -z "$1" ]; then
    print_error "Usage: $0 <vps_ip> [username]"
    echo ""
    echo "Example:"
    echo "  $0 192.168.1.100"
    echo "  $0 192.168.1.100 ubuntu"
    exit 1
fi

VPS_IP="$1"
VPS_USER="${2:-root}"
PROJECT_DIR="$HOME/vpn-bot"

print_status "Deploying VPN Bot to $VPS_USER@$VPS_IP"

# Check if we're in the bot directory
if [ ! -f "main.py" ] || [ ! -f "requirements.txt" ]; then
    print_error "Please run this script from your VPN bot directory"
    exit 1
fi

# Create a temporary deployment package
print_status "Creating deployment package..."
TEMP_DIR=$(mktemp -d)
DEPLOY_DIR="$TEMP_DIR/vpn-bot"

mkdir -p "$DEPLOY_DIR"

# Copy essential files
print_status "Copying bot files..."
cp -r main.py app.py wsgi.py requirements.txt "$DEPLOY_DIR/"
cp -r app/ common/ core/ "$DEPLOY_DIR/" 2>/dev/null || true
cp -r assets/ "$DEPLOY_DIR/" 2>/dev/null || true
cp -r locales/ "$DEPLOY_DIR/" 2>/dev/null || true
cp -r xray_proto_files/ "$DEPLOY_DIR/" 2>/dev/null || true

# Copy configuration files
cp config.py database.py database_postgresql.py "$DEPLOY_DIR/" 2>/dev/null || true
cp payment_utils.py outline_utils.py vless_utils.py "$DEPLOY_DIR/" 2>/dev/null || true

# Copy deployment files
cp setup_vps.sh "$DEPLOY_DIR/"
cp VPS_DOCKER_DEPLOYMENT.md "$DEPLOY_DIR/"

# Create a simple .gitignore
cat > "$DEPLOY_DIR/.gitignore" << 'EOF'
.env
*.log
logs/
backups/
__pycache__/
*.pyc
.DS_Store
EOF

# Create deployment archive
print_status "Creating deployment archive..."
cd "$TEMP_DIR"
tar -czf vpn-bot-deploy.tar.gz vpn-bot/

# Upload to VPS
print_status "Uploading to VPS..."
scp vpn-bot-deploy.tar.gz "$VPS_USER@$VPS_IP:/tmp/"

# Execute setup on VPS
print_status "Setting up on VPS..."
ssh "$VPS_USER@$VPS_IP" << 'EOF'
set -e

echo "🚀 Setting up VPN Bot on VPS..."

# Extract deployment package
cd /tmp
tar -xzf vpn-bot-deploy.tar.gz

# Move to home directory
mv vpn-bot ~/vpn-bot
cd ~/vpn-bot

# Run setup script
chmod +x setup_vps.sh
./setup_vps.sh

# Clean up
rm -f /tmp/vpn-bot-deploy.tar.gz

echo "✅ VPN Bot setup completed on VPS!"
echo ""
echo "Next steps:"
echo "1. SSH into your VPS: ssh $VPS_USER@$VPS_IP"
echo "2. Configure environment: cd ~/vpn-bot && cp .env.template .env && nano .env"
echo "3. Start the bot: ./manage.sh start"
echo "4. Check status: ./manage.sh status"
EOF

# Clean up local temp files
rm -rf "$TEMP_DIR"

print_success "Deployment completed successfully!"
echo ""
echo "🎉 Your VPN Bot has been deployed to $VPS_USER@$VPS_IP"
echo ""
echo "Next steps:"
echo "1. SSH into your VPS:"
echo "   ssh $VPS_USER@$VPS_IP"
echo ""
echo "2. Configure your environment variables:"
echo "   cd ~/vpn-bot"
echo "   cp .env.template .env"
echo "   nano .env"
echo ""
echo "3. Start your bot:"
echo "   ./manage.sh start"
echo ""
echo "4. Check if everything is working:"
echo "   ./manage.sh status"
echo "   ./manage.sh logs"
echo ""
print_success "Your VPN Bot is ready to run on VPS!"
