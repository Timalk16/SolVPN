# VPS with Docker Deployment Guide for VPN Bot

Deploy your VPN bot on a VPS with Docker for full control and maximum flexibility.

## 🚀 Quick Start (5-Minute Setup)

### 1. Get a VPS

- **DigitalOcean**: $5/month (1GB RAM, 1 vCPU) - [Sign up here](https://m.do.co/c/your-referral)
- **Linode**: $5/month (1GB RAM, 1 vCPU) - [Sign up here](https://www.linode.com/)
- **Vultr**: $5/month (1GB RAM, 1 vCPU) - [Sign up here](https://www.vultr.com/)

### 2. One-Command Setup

```bash
# SSH into your VPS and run this command
curl -fsSL https://raw.githubusercontent.com/your-username/vpn-bot/main/setup_vps.sh | bash
```

### 3. Configure Environment

```bash
# Edit environment variables
nano .env
```

### 4. Deploy

```bash
# Start everything
docker-compose up -d
```

**That's it!** Your bot will be running in 5 minutes.

---

## 📋 Detailed Setup (If you prefer manual setup)

### 1. Choose a VPS Provider

Recommended providers:

- **DigitalOcean**: $5/month (1GB RAM, 1 vCPU)
- **Linode**: $5/month (1GB RAM, 1 vCPU)
- **Vultr**: $5/month (1GB RAM, 1 vCPU)
- **AWS EC2**: t3.micro (free tier eligible)

### 2. Set Up VPS

```bash
# SSH into your VPS
ssh root@your-vps-ip

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Add user to docker group
usermod -aG docker $USER
```

### 3. Clone Your Repository

```bash
# Install git
apt install git -y

# Clone your repository
git clone https://github.com/your-username/vpn-bot.git
cd vpn-bot
```

### 4. Create Docker Configuration

#### Create `Dockerfile`

```dockerfile
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
```

#### Create `docker-compose.yml`

```yaml
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
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
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
```

#### Create `.env` file

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
ADMIN_USER_ID=your_telegram_user_id
CRYPTOBOT_TESTNET_API_TOKEN=your_cryptobot_testnet_token
CRYPTOBOT_MAINNET_API_TOKEN=your_cryptobot_mainnet_token
OUTLINE_API_URL_GERMANY=your_germany_outline_url
OUTLINE_CERT_SHA256_GERMANY=your_germany_cert_sha256
OUTLINE_API_URL_FRANCE=your_france_outline_url
OUTLINE_CERT_SHA256_FRANCE=your_france_cert_sha256
YOOKASSA_SHOP_ID=your_yookassa_shop_id
YOOKASSA_SECRET_KEY=your_yookassa_secret_key
POSTGRES_PASSWORD=your_secure_password_here
```

#### Create `nginx.conf`

```nginx
events {
    worker_connections 1024;
}

http {
    upstream vpn_bot {
        server vpn-bot:8080;
    }

    server {
        listen 80;
        server_name your-domain.com;

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
```

### 5. Deploy

```bash
# Build and start services
docker-compose up -d

# Check logs
docker-compose logs -f

# Check status
docker-compose ps
```

## 🔧 SSL Certificate Setup

### Using Let's Encrypt with Certbot

```bash
# Install certbot
apt install certbot -y

# Get SSL certificate
certbot certonly --standalone -d your-domain.com

# Update nginx.conf for SSL
```

### Updated `nginx.conf` with SSL

```nginx
events {
    worker_connections 1024;
}

http {
    upstream vpn_bot {
        server vpn-bot:8080;
    }

    server {
        listen 80;
        server_name your-domain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl;
        server_name your-domain.com;

        ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

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
```

## 📊 Monitoring and Maintenance

### Create `monitor.sh`

```bash
#!/bin/bash

# Check if containers are running
if ! docker-compose ps | grep -q "Up"; then
    echo "VPN Bot is down! Restarting..."
    docker-compose restart
    # Send notification (optional)
    # curl -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
    #     -d "chat_id=$ADMIN_USER_ID" \
    #     -d "text=VPN Bot was down and has been restarted"
fi

# Check disk space
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "Disk usage is high: ${DISK_USAGE}%"
fi

# Clean up old logs
find ./logs -name "*.log" -mtime +7 -delete
```

### Set up cron job

```bash
# Add to crontab
crontab -e

# Add this line to run monitoring every 5 minutes
*/5 * * * * /path/to/your/vpn-bot/monitor.sh
```

## 🔍 Troubleshooting

### Check Container Status

```bash
# View all containers
docker ps -a

# View logs
docker-compose logs vpn-bot

# Restart service
docker-compose restart vpn-bot
```

### Database Management

```bash
# Access PostgreSQL
docker-compose exec postgres psql -U postgres -d vpn_bot

# Backup database
docker-compose exec postgres pg_dump -U postgres vpn_bot > backup.sql

# Restore database
docker-compose exec -T postgres psql -U postgres -d vpn_bot < backup.sql
```

### Update Application

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

## 🚀 Advanced Configuration

### Auto-scaling with Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml vpn-bot
```

### Backup Strategy

```bash
#!/bin/bash
# Create backup script
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# Backup database
docker-compose exec -T postgres pg_dump -U postgres vpn_bot > $BACKUP_DIR/db_$DATE.sql

# Backup logs
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz logs/

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

## 💰 Cost Breakdown

- **VPS**: $5-10/month
- **Domain**: $10-15/year
- **SSL**: Free (Let's Encrypt)
- **Total**: ~$5-10/month

## 🚨 Security Considerations

1. **Firewall**: Configure UFW

```bash
ufw allow 22
ufw allow 80
ufw allow 443
ufw enable
```

2. **Regular updates**: Keep system and containers updated
3. **Backups**: Set up automated backups
4. **Monitoring**: Monitor logs and system resources

## 🎯 Quick Commands Reference

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Restart bot only
docker-compose restart vpn-bot

# Update and rebuild
git pull && docker-compose up -d --build

# Check status
docker-compose ps

# Backup database
docker-compose exec postgres pg_dump -U postgres vpn_bot > backup.sql
```

---

**VPS with Docker deployment gives you full control!** 🚀

No more account suspensions, complete control over your infrastructure, and the lowest cost option available.
