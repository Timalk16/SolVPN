#!/bin/bash

# Simple VPN Bot VPS Deployment Script
# This script deploys your bot directly to a VPS

set -e

echo "🚀 Simple VPN Bot VPS Deployment"

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
    print_error "Usage: $0 <vps_ip>"
    echo ""
    echo "Example:"
    echo "  $0 62.60.238.31"
    exit 1
fi

VPS_IP="$1"
VPS_USER="root"

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
mv vpn-bot /root/vpn-bot
cd /root/vpn-bot

# Update system
echo "Updating system packages..."
apt update && apt upgrade -y

# Install required packages
echo "Installing required packages..."
apt install -y curl wget git nano ufw docker.io docker-compose

# Start Docker service
systemctl start docker
systemctl enable docker

# Create Dockerfile
echo "Creating Dockerfile..."
cat > Dockerfile << 'DOCKEREOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Start the application
CMD ["gunicorn", "wsgi:application", "--bind", "0.0.0.0:8080", "--workers", "1", "--timeout", "120"]
DOCKEREOF

# Create docker-compose.yml
echo "Creating docker-compose.yml..."
cat > docker-compose.yml << 'COMPOSEEOF'
version: '3.8'

services:
  vpn-bot:
    build: .
    ports:
      - '8080:8080'
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - ADMIN_USER_ID=${ADMIN_USER_ID}
      - CRYPTOBOT_TESTNET_API_TOKEN=${CRYPTOBOT_TESTNET_API_TOKEN}
      - CRYPTOBOT_MAINNET_API_TOKEN=${CRYPTOBOT_MAINNET_API_TOKEN}
      - OUTLINE_API_URL_GERMANY=${OUTLINE_API_URL_GERMANY}
      - OUTLINE_CERT_SHA256_GERMANY=${OUTLINE_CERT_SHA256_GERMANY}
      - OUTLINE_API_URL_FRANCE=${OUTLINE_API_URL_FRANCE}
      - OUTLINE_CERT_SHA256_FRANCE=${OUTLINE_CERT_SHA256_FRANCE}
      - YOOKASSA_SHOP_ID=${YOOKASSA_SHOP_ID}
      - YOOKASSA_SECRET_KEY=${YOOKASSA_SECRET_KEY}
      - USE_POSTGRESQL=true
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/vpn_bot
    depends_on:
      - postgres
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs
    networks:
      - vpn-bot-network

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=vpn_bot
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    networks:
      - vpn-bot-network

volumes:
  postgres_data:

networks:
  vpn-bot-network:
    driver: bridge
COMPOSEEOF

# Create .env template
echo "Creating .env template..."
cat > .env.template << 'ENVEOF'
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
ADMIN_USER_ID=your_telegram_user_id

# Cryptobot Configuration
CRYPTOBOT_TESTNET_API_TOKEN=your_cryptobot_testnet_token
CRYPTOBOT_MAINNET_API_TOKEN=your_cryptobot_mainnet_token

# Outline VPN Configuration
OUTLINE_API_URL_GERMANY=your_germany_outline_url
OUTLINE_CERT_SHA256_GERMANY=your_germany_cert_sha256
OUTLINE_API_URL_FRANCE=your_france_outline_url
OUTLINE_CERT_SHA256_FRANCE=your_france_cert_sha256

# YooKassa Payment Configuration
YOOKASSA_SHOP_ID=your_yookassa_shop_id
YOOKASSA_SECRET_KEY=your_yookassa_secret_key

# Database Configuration
POSTGRES_PASSWORD=your_secure_password_here
ENVEOF

# Create management script
echo "Creating management script..."
cat > manage.sh << 'MANAGEEOF'
#!/bin/bash

# VPN Bot Management Script

case "$1" in
    start)
        echo "Starting VPN Bot..."
        docker-compose up -d
        ;;
    stop)
        echo "Stopping VPN Bot..."
        docker-compose down
        ;;
    restart)
        echo "Restarting VPN Bot..."
        docker-compose restart
        ;;
    logs)
        echo "Showing logs..."
        docker-compose logs -f
        ;;
    status)
        echo "Checking status..."
        docker-compose ps
        ;;
    update)
        echo "Updating VPN Bot..."
        git pull
        docker-compose down
        docker-compose up -d --build
        ;;
    backup)
        echo "Creating backup..."
        DATE=$(date +%Y%m%d_%H%M%S)
        docker-compose exec -T postgres pg_dump -U postgres vpn_bot > backup_$DATE.sql
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|logs|status|update|backup}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the VPN Bot"
        echo "  stop    - Stop the VPN Bot"
        echo "  restart - Restart the VPN Bot"
        echo "  logs    - Show logs"
        echo "  status  - Show status"
        echo "  update  - Update and rebuild"
        echo "  backup  - Create backup"
        exit 1
        ;;
esac
MANAGEEOF

chmod +x manage.sh

# Create logs directory
mkdir -p logs

# Setup firewall
echo "Configuring firewall..."
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8080/tcp
ufw --force enable

# Clean up
rm -f /tmp/vpn-bot-deploy.tar.gz

echo "✅ VPN Bot setup completed on VPS!"
echo ""
echo "Next steps:"
echo "1. Configure environment: cp .env.template .env && nano .env"
echo "2. Start the bot: ./manage.sh start"
echo "3. Check status: ./manage.sh status"
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
echo "   cd /root/vpn-bot"
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
