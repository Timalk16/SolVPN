# Heroku Deployment Guide for VPN Bot

Heroku is a reliable classic choice with good free tier and easy deployment.

## 🚀 Quick Setup

### 1. Create Heroku Account

- Go to [heroku.com](https://heroku.com)
- Sign up for a free account
- Install Heroku CLI

### 2. Install Heroku CLI

```bash
# macOS
brew tap heroku/brew && brew install heroku

# Ubuntu/Debian
sudo snap install heroku --classic

# Windows
# Download from https://devcenter.heroku.com/articles/heroku-cli
```

### 3. Login to Heroku

```bash
heroku login
```

### 4. Create Heroku App

```bash
# In your project directory
heroku create vpn-bot-yourname
```

### 5. Add PostgreSQL Database

```bash
heroku addons:create heroku-postgresql:mini
```

### 6. Set Environment Variables

```bash
heroku config:set TELEGRAM_BOT_TOKEN=your_bot_token_here
heroku config:set ADMIN_USER_ID=your_telegram_user_id
heroku config:set CRYPTOBOT_TESTNET_API_TOKEN=your_cryptobot_testnet_token
heroku config:set CRYPTOBOT_MAINNET_API_TOKEN=your_cryptobot_mainnet_token
heroku config:set OUTLINE_API_URL_GERMANY=your_germany_outline_url
heroku config:set OUTLINE_CERT_SHA256_GERMANY=your_germany_cert_sha256
heroku config:set OUTLINE_API_URL_FRANCE=your_france_outline_url
heroku config:set OUTLINE_CERT_SHA256_FRANCE=your_france_cert_sha256
heroku config:set YOOKASSA_SHOP_ID=your_yookassa_shop_id
heroku config:set YOOKASSA_SECRET_KEY=your_yookassa_secret_key
heroku config:set USE_POSTGRESQL=true
```

### 7. Deploy

```bash
git add .
git commit -m "Deploy to Heroku"
git push heroku main
```

## 📁 Required Files

### Create `Procfile`

```
web: gunicorn wsgi:application --bind 0.0.0.0:$PORT --workers 1 --timeout 120
```

### Create `runtime.txt`

```
python-3.11.7
```

### Update `requirements.txt`

Your current requirements.txt should work, but ensure these are included:

```
gunicorn>=21.0.0
Flask>=2.3.0
psycopg2-binary>=2.9.0
```

## 🔧 Heroku-Specific Configuration

### Update `app.py` for Heroku

Your current `app.py` should work, but ensure it binds to the correct port:

```python
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
```

### Health Check Endpoint

Your existing `/health` endpoint will work perfectly with Heroku's health checks.

## 🌐 Custom Domain

```bash
# Add custom domain
heroku domains:add yourdomain.com

# Check domain status
heroku domains
```

## 📊 Monitoring

```bash
# View logs
heroku logs --tail

# Monitor app status
heroku ps

# Check app info
heroku info
```

## 💰 Pricing

- **Free tier**: Discontinued (use Eco dyno)
- **Eco dyno**: $5/month (512MB RAM)
- **Basic dyno**: $7/month (512MB RAM)
- **Standard dyno**: $25/month (512MB RAM)

## 🔍 Troubleshooting

### Check App Status

```bash
heroku ps
heroku logs --tail
```

### Common Issues

1. **Port binding**: Heroku sets `$PORT` environment variable
2. **Database connection**: Check `DATABASE_URL` is set correctly
3. **Memory limits**: Free tier has 512MB memory limit
4. **Sleep mode**: Free dynos sleep after 30 minutes of inactivity

### Debug Commands

```bash
# Run app locally with Heroku config
heroku local web

# Check environment variables
heroku config

# Restart app
heroku restart

# Run one-off dyno
heroku run python
```

## 🚀 Advanced Configuration

### Auto-scaling

```bash
# Enable auto-scaling
heroku ps:scale web=1-3
```

### Worker Dynos

If you want to separate web and bot processes:

```bash
# Add worker dyno
heroku ps:scale worker=1

# Update Procfile
echo "worker: python main.py" >> Procfile
```

## 📈 Performance

Heroku provides:

- Automatic SSL certificates
- Built-in load balancing
- Easy scaling
- Add-on ecosystem

## 🔧 Database Migration

If you need to migrate your existing database:

```bash
# Create database backup
heroku pg:backups:capture

# Download backup
heroku pg:backups:download

# Restore to local database
pg_restore --verbose --clean --no-acl --no-owner -h localhost -U your_username -d your_database latest.dump
```

## 🚨 Important Notes

1. **Free tier limitations**: 512MB RAM, 30-minute sleep
2. **Database limits**: 10,000 rows for free tier
3. **Request timeout**: 30 seconds for web requests
4. **File system**: Ephemeral (files are lost on restart)

## 📊 Monitoring Add-ons

```bash
# Add monitoring
heroku addons:create papertrail:choklad
heroku addons:create newrelic:wayne

# View logs
heroku logs --tail --addon papertrail
```

---

**Heroku is ready to deploy your VPN bot!** 🚀
