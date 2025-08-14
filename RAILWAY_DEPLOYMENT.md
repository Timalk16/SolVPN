# Railway Deployment Guide for VPN Bot

Railway is an excellent alternative to Render with similar ease of use and features.

## 🚀 Quick Setup

### 1. Create Railway Account

- Go to [railway.app](https://railway.app)
- Sign up with GitHub
- Create a new project

### 2. Connect Your Repository

- Click "Deploy from GitHub repo"
- Select your VPN bot repository
- Railway will automatically detect it's a Python app

### 3. Configure Environment Variables

Add these environment variables in Railway dashboard:

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
DATABASE_URL=your_postgresql_url
```

### 4. Add PostgreSQL Database

- In Railway dashboard, click "New"
- Select "Database" → "PostgreSQL"
- Railway will automatically set the `DATABASE_URL` environment variable

### 5. Deploy

- Railway will automatically deploy when you push to your main branch
- Or click "Deploy" in the dashboard

## 📁 Required Files

Railway will use these files automatically:

- `requirements.txt` - Python dependencies
- `wsgi.py` - WSGI entry point
- `app.py` - Flask application

## 🔧 Railway-Specific Configuration

### Create `railway.json` (Optional)

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "gunicorn wsgi:application --bind 0.0.0.0:$PORT --workers 1 --timeout 120",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 300,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Update `requirements.txt` (if needed)

Your current requirements.txt should work fine, but ensure these are included:

```
gunicorn>=21.0.0
Flask>=2.3.0
psycopg2-binary>=2.9.0
```

## 🌐 Custom Domain (Optional)

1. In Railway dashboard, go to your service
2. Click "Settings" → "Domains"
3. Add your custom domain
4. Configure DNS records as instructed

## 📊 Monitoring

Railway provides:

- Real-time logs
- Performance metrics
- Automatic restarts
- Health checks

## 💰 Pricing

- **Free tier**: $5 credit monthly
- **Pro**: Pay-as-you-use
- **Team**: $20/month per user

## 🔍 Troubleshooting

### Check Logs

- Go to Railway dashboard
- Click on your service
- View "Deployments" tab for logs

### Common Issues

1. **Port binding**: Railway sets `$PORT` environment variable
2. **Database connection**: Ensure `DATABASE_URL` is set correctly
3. **Environment variables**: Double-check all required variables are set

### Health Check

Your bot already has a health endpoint at `/health` which Railway will use.

## 🚀 Deployment Commands

```bash
# If using Railway CLI
railway login
railway link
railway up
```

## 📈 Scaling

Railway automatically scales based on traffic. You can also:

- Set minimum/maximum instances
- Configure auto-scaling rules
- Monitor resource usage

---

**Railway is ready to deploy your VPN bot!** 🚀
