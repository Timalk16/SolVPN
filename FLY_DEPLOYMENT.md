# Fly.io Deployment Guide for VPN Bot

Fly.io is a great alternative with global edge deployment and generous free tier.

## 🚀 Quick Setup

### 1. Install Fly CLI

```bash
# macOS
brew install flyctl

# Linux
curl -L https://fly.io/install.sh | sh

# Windows
iwr https://fly.io/install.ps1 -useb | iex
```

### 2. Login to Fly

```bash
fly auth login
```

### 3. Create Fly App

```bash
fly launch
```

When prompted:

- Choose your app name (e.g., `vpn-bot`)
- Choose your region
- Don't deploy yet (we'll configure first)

### 4. Configure Environment Variables

```bash
fly secrets set TELEGRAM_BOT_TOKEN=your_bot_token_here
fly secrets set ADMIN_USER_ID=your_telegram_user_id
fly secrets set CRYPTOBOT_TESTNET_API_TOKEN=your_cryptobot_testnet_token
fly secrets set CRYPTOBOT_MAINNET_API_TOKEN=your_cryptobot_mainnet_token
fly secrets set OUTLINE_API_URL_GERMANY=your_germany_outline_url
fly secrets set OUTLINE_CERT_SHA256_GERMANY=your_germany_cert_sha256
fly secrets set OUTLINE_API_URL_FRANCE=your_france_outline_url
fly secrets set OUTLINE_CERT_SHA256_FRANCE=your_france_cert_sha256
fly secrets set YOOKASSA_SHOP_ID=your_yookassa_shop_id
fly secrets set YOOKASSA_SECRET_KEY=your_yookassa_secret_key
fly secrets set USE_POSTGRESQL=true
```

### 5. Create PostgreSQL Database

```bash
fly postgres create vpn-bot-db
fly postgres attach vpn-bot-db --app vpn-bot
```

### 6. Deploy

```bash
fly deploy
```

## 📁 Required Files

### Create `fly.toml`

```toml
app = "vpn-bot"
primary_region = "iad"

[build]

[env]
  PORT = "8080"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0
  processes = ["app"]

  [[http_service.checks]]
    grace_period = "10s"
    interval = "30s"
    method = "GET"
    timeout = "5s"
    path = "/health"

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 512
```

### Create `Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8080

# Start the application
CMD ["gunicorn", "wsgi:application", "--bind", "0.0.0.0:8080", "--workers", "1", "--timeout", "120"]
```

## 🔧 Fly.io Specific Configuration

### Update `app.py` for Fly.io

Your current `app.py` should work, but ensure it binds to the correct port:

```python
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
```

### Health Check Endpoint

Your existing `/health` endpoint will work perfectly with Fly.io's health checks.

## 🌐 Custom Domain

```bash
# Add custom domain
fly certs add yourdomain.com

# Check certificate status
fly certs show yourdomain.com
```

## 📊 Monitoring

```bash
# View logs
fly logs

# Monitor app status
fly status

# Scale your app
fly scale count 1
```

## 💰 Pricing

- **Free tier**: 3 shared-cpu-1x 256mb VMs, 3GB persistent volume storage
- **Paid**: Pay-as-you-use starting at $1.94/month per VM

## 🔍 Troubleshooting

### Check App Status

```bash
fly status
fly logs
```

### Common Issues

1. **Port binding**: Ensure app binds to `0.0.0.0:8080`
2. **Database connection**: Check `DATABASE_URL` is set correctly
3. **Memory limits**: Free tier has 256MB memory limit

### Debug Commands

```bash
# SSH into your app
fly ssh console

# Check environment variables
fly ssh console -C "env | grep DATABASE_URL"

# Restart app
fly apps restart vpn-bot
```

## 🚀 Advanced Configuration

### Auto-scaling

```bash
# Set auto-scaling rules
fly scale memory 512
fly scale count 1-3
```

### Multiple Regions

```bash
# Deploy to multiple regions
fly deploy --strategy immediate
```

## 📈 Performance

Fly.io provides:

- Global edge deployment
- Automatic SSL certificates
- Built-in load balancing
- Fast cold starts

---

**Fly.io is ready to deploy your VPN bot globally!** 🚀
