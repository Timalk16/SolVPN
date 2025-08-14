#!/bin/bash

# VPN Bot VPS Setup Script
# This script automates the entire VPS setup process

set -e  # Exit on any error

echo "🚀 Starting VPN Bot VPS Setup..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_warning "Running as root user. This is acceptable for VPS deployment."
   # Continue with root user
else
   print_status "Running as regular user. Using sudo for system commands."
fi

# Update system
print_status "Updating system packages..."
if [[ $EUID -eq 0 ]]; then
    apt update && apt upgrade -y
else
    sudo apt update && sudo apt upgrade -y
fi

# Install required packages
print_status "Installing required packages..."
if [[ $EUID -eq 0 ]]; then
    apt install -y curl wget git nano ufw
else
    sudo apt install -y curl wget git nano ufw
fi

# Install Docker
print_status "Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    if [[ $EUID -eq 0 ]]; then
        usermod -aG docker $USER
    else
        sudo usermod -aG docker $USER
    fi
    print_success "Docker installed successfully"
else
    print_success "Docker is already installed"
fi

# Install Docker Compose
print_status "Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    if [[ $EUID -eq 0 ]]; then
        curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
    else
        sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    fi
    print_success "Docker Compose installed successfully"
else
    print_success "Docker Compose is already installed"
fi

# Create project directory
PROJECT_DIR="$HOME/vpn-bot"
print_status "Setting up project directory: $PROJECT_DIR"

if [ -d "$PROJECT_DIR" ]; then
    print_warning "Project directory already exists. Backing up..."
    mv "$PROJECT_DIR" "${PROJECT_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
fi

mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Create Dockerfile
print_status "Creating Dockerfile..."
cat > Dockerfile << 'EOF'
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
EOF

# Create docker-compose.yml
print_status "Creating docker-compose.yml..."
cat > docker-compose.yml << 'EOF'
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

  nginx:
    image: nginx:alpine
    ports:
      - '80:80'
      - '443:443'
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - vpn-bot
    restart: unless-stopped
    networks:
      - vpn-bot-network

volumes:
  postgres_data:

networks:
  vpn-bot-network:
    driver: bridge
EOF

# Create nginx.conf
print_status "Creating nginx.conf..."
cat > nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream vpn_bot {
        server vpn-bot:8080;
    }

    server {
        listen 80;
        server_name _;

        location / {
            proxy_pass http://vpn_bot;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /health {
            proxy_pass http://vpn_bot/health;
            access_log off;
        }
    }
}
EOF

# Create .env template
print_status "Creating .env template..."
cat > .env.template << 'EOF'
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
EOF

# Create monitoring script
print_status "Creating monitoring script..."
cat > monitor.sh << 'EOF'
#!/bin/bash

# VPN Bot Monitoring Script

# Check if containers are running
if ! docker-compose ps | grep -q "Up"; then
    echo "$(date): VPN Bot is down! Restarting..."
    docker-compose restart
    
    # Send notification to admin (uncomment and configure if needed)
    # curl -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
    #     -d "chat_id=$ADMIN_USER_ID" \
    #     -d "text=VPN Bot was down and has been restarted"
fi

# Check disk space
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "$(date): Disk usage is high: ${DISK_USAGE}%"
fi

# Clean up old logs
find ./logs -name "*.log" -mtime +7 -delete 2>/dev/null || true
EOF

chmod +x monitor.sh

# Create backup script
print_status "Creating backup script..."
cat > backup.sh << 'EOF'
#!/bin/bash

# VPN Bot Backup Script

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups"
mkdir -p "$BACKUP_DIR"

echo "Creating backup: $DATE"

# Backup database
docker-compose exec -T postgres pg_dump -U postgres vpn_bot > "$BACKUP_DIR/db_$DATE.sql" 2>/dev/null || echo "Database backup failed"

# Backup logs
tar -czf "$BACKUP_DIR/logs_$DATE.tar.gz" logs/ 2>/dev/null || echo "Logs backup failed"

# Keep only last 7 days of backups
find "$BACKUP_DIR" -name "*.sql" -mtime +7 -delete 2>/dev/null || true
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete 2>/dev/null || true

echo "Backup completed: $DATE"
EOF

chmod +x backup.sh

# Create logs directory
mkdir -p logs

# Setup firewall
print_status "Configuring firewall..."
if [[ $EUID -eq 0 ]]; then
    ufw allow 22/tcp
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw --force enable
else
    sudo ufw allow 22/tcp
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw --force enable
fi

# Create management script
print_status "Creating management script..."
cat > manage.sh << 'EOF'
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
        ./backup.sh
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
EOF

chmod +x manage.sh

# Create README
print_status "Creating README..."
cat > README_VPS.md << 'EOF'
# VPN Bot VPS Setup

Your VPN Bot is now set up on this VPS!

## Quick Commands

```bash
# Start the bot
./manage.sh start

# Stop the bot
./manage.sh stop

# View logs
./manage.sh logs

# Check status
./manage.sh status

# Update bot
./manage.sh update

# Create backup
./manage.sh backup
```

## Configuration

1. Copy the environment template:
   ```bash
   cp .env.template .env
   ```

2. Edit the environment variables:
   ```bash
   nano .env
   ```

3. Start the bot:
   ```bash
   ./manage.sh start
   ```

## Monitoring

The bot is automatically monitored every 5 minutes. To set up monitoring:

```bash
crontab -e
# Add this line:
*/5 * * * * cd /home/your-username/vpn-bot && ./monitor.sh
```

## SSL Certificate

To add SSL certificate:

```bash
sudo apt install certbot
sudo certbot certonly --standalone -d your-domain.com
```

Then update nginx.conf with SSL configuration.

## Backup

Backups are automatically created and kept for 7 days. Manual backup:

```bash
./backup.sh
```

## Troubleshooting

- Check logs: `./manage.sh logs`
- Check status: `./manage.sh status`
- Restart bot: `./manage.sh restart`
- View container logs: `docker-compose logs vpn-bot`

## Support

If you need help, check the logs and ensure all environment variables are set correctly.
EOF

print_success "VPS setup completed successfully!"
echo ""
echo "🎉 Your VPN Bot VPS is ready!"
echo ""
echo "Next steps:"
echo "1. Configure your environment variables:"
echo "   cp .env.template .env"
echo "   nano .env"
echo ""
echo "2. Start your bot:"
echo "   ./manage.sh start"
echo ""
echo "3. Check status:"
echo "   ./manage.sh status"
echo ""
echo "4. View logs:"
echo "   ./manage.sh logs"
echo ""
echo "📁 Project directory: $PROJECT_DIR"
echo "📖 Read README_VPS.md for more information"
echo ""
print_success "Setup complete! Your bot is ready to deploy."
