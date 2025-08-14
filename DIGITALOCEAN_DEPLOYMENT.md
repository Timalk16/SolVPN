# DigitalOcean App Platform Deployment Guide for VPN Bot

DigitalOcean App Platform is a reliable, scalable alternative with good performance.

## 🚀 Quick Setup

### 1. Create DigitalOcean Account

- Go to [digitalocean.com](https://digitalocean.com)
- Sign up for an account
- Add payment method (required)

### 2. Create App in DigitalOcean Dashboard

- Go to "Apps" in your DigitalOcean dashboard
- Click "Create App"
- Connect your GitHub repository
- Select your VPN bot repository

### 3. Configure App Settings

#### Basic Settings:

- **Name**: `vpn-bot`
- **Region**: Choose closest to your users
- **Branch**: `main`

#### Build Settings:

- **Build Command**: Leave empty (auto-detected)
- **Run Command**: `gunicorn wsgi:application --bind 0.0.0.0:$PORT --workers 1 --timeout 120`

### 4. Add Environment Variables

Add these environment variables in the DigitalOcean dashboard:

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
USE_POSTGRESQL=true
```

### 5. Add PostgreSQL Database

- Click "Add Resource" → "Database"
- Choose "PostgreSQL"
- Select plan (Basic $7/month minimum)
- DigitalOcean will automatically set `DATABASE_URL`

### 6. Deploy

- Click "Create Resources"
- DigitalOcean will build and deploy your app

## 📁 Required Files

### Create `.do/app.yaml` (Optional)

```yaml
name: vpn-bot
services:
  - name: web
    source_dir: /
    github:
      repo: your-username/vpn-bot
      branch: main
    run_command: gunicorn wsgi:application --bind 0.0.0.0:$PORT --workers 1 --timeout 120
    environment_slug: python
    instance_count: 1
    instance_size_slug: basic-xxs
    health_check:
      http_path: /health
databases:
  - name: vpn-bot-db
    engine: PG
    version: '12'
    size: db-s-1vcpu-1gb
```

### Update `requirements.txt`

Your current requirements.txt should work fine.

## 🔧 DigitalOcean-Specific Configuration

### Health Check Endpoint

Your existing `/health` endpoint will work perfectly with DigitalOcean's health checks.

### Port Configuration

DigitalOcean automatically sets the `$PORT` environment variable.

## 🌐 Custom Domain

1. In DigitalOcean dashboard, go to your app
2. Click "Settings" → "Domains"
3. Add your custom domain
4. Configure DNS records as instructed

## 📊 Monitoring

DigitalOcean provides:

- Real-time logs
- Performance metrics
- Automatic restarts
- Health checks
- Resource usage monitoring

## 💰 Pricing

- **Basic plan**: $5/month (512MB RAM, 0.25 vCPU)
- **Professional plan**: $12/month (1GB RAM, 0.5 vCPU)
- **Database**: $7/month minimum for PostgreSQL

## 🔍 Troubleshooting

### Check App Status

- Go to DigitalOcean dashboard
- Click on your app
- View "Runtime Logs" tab

### Common Issues

1. **Build failures**: Check build logs for dependency issues
2. **Database connection**: Ensure `DATABASE_URL` is set correctly
3. **Memory limits**: Monitor resource usage in dashboard
4. **Port binding**: Ensure app binds to `$PORT`

### Debug Commands

```bash
# If using doctl CLI
doctl apps list
doctl apps logs your-app-id
doctl apps get your-app-id
```

## 🚀 Advanced Configuration

### Auto-scaling

- In DigitalOcean dashboard, go to your app
- Click "Settings" → "Autoscaling"
- Configure min/max instances

### Multiple Regions

- Create apps in different regions
- Use load balancer for global distribution

## 📈 Performance

DigitalOcean App Platform provides:

- Automatic SSL certificates
- Built-in load balancing
- Global CDN
- Fast deployments
- Reliable infrastructure

## 🔧 Database Management

### Backup and Restore

- DigitalOcean automatically handles backups
- Manual backups available in dashboard
- Point-in-time recovery for PostgreSQL

### Database Scaling

- Upgrade database plan as needed
- Monitor usage in dashboard

## 🚨 Important Notes

1. **No free tier**: Minimum $5/month for app + $7/month for database
2. **Resource limits**: Monitor usage in dashboard
3. **Build timeouts**: 20 minutes maximum build time
4. **File system**: Ephemeral (files are lost on restart)

## 📊 Monitoring and Alerts

```bash
# Set up monitoring alerts
# Go to DigitalOcean dashboard → Monitoring → Alerts
# Configure alerts for:
# - High CPU usage
# - High memory usage
# - Database connections
# - Response time
```

## 🔧 CLI Deployment (Alternative)

If you prefer CLI deployment:

```bash
# Install doctl
brew install doctl  # macOS
# or download from https://github.com/digitalocean/doctl/releases

# Authenticate
doctl auth init

# Deploy app
doctl apps create --spec .do/app.yaml
```

---

**DigitalOcean App Platform is ready to deploy your VPN bot!** 🚀
