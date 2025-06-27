# VPN Bot Deployment Guide

## 🚀 Quick Deploy to Railway (Recommended)

### Step 1: Prepare Your Repository

1. Make sure your code is in a GitHub repository
2. Ensure all files are committed and pushed

### Step 2: Deploy to Railway

1. Go to [Railway.app](https://railway.app) and sign up/login
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Railway will automatically detect it's a Python project

### Step 3: Configure Environment Variables

In Railway dashboard, go to your project → Variables tab and add:

```
TELEGRAM_BOT_TOKEN=your_bot_token_here
ADMIN_USER_ID=your_telegram_user_id
CRYPTOBOT_TESTNET_API_TOKEN=your_cryptobot_token
CRYPTOBOT_MAINNET_API_TOKEN=your_mainnet_token
OUTLINE_API_URL_GERMANY=your_germany_server_url
OUTLINE_CERT_SHA256_GERMANY=your_germany_cert_sha256
OUTLINE_API_URL_FRANCE=your_france_server_url
OUTLINE_CERT_SHA256_FRANCE=your_france_cert_sha256
YOOKASSA_SHOP_ID=your_yookassa_shop_id
YOOKASSA_SECRET_KEY=your_yookassa_secret_key
```

### Step 4: Deploy

1. Railway will automatically build and deploy your bot
2. Check the logs to ensure it starts successfully
3. Your bot will be running 24/7!

## 🔧 Alternative Deployment Options

### Render.com

1. Sign up at [Render.com](https://render.com)
2. Create new Web Service
3. Connect your GitHub repo
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `python main.py`
6. Add environment variables as above

### Heroku

1. Install Heroku CLI
2. Run: `heroku create your-bot-name`
3. Run: `git push heroku main`
4. Set environment variables: `heroku config:set TELEGRAM_BOT_TOKEN=your_token`

### DigitalOcean App Platform

1. Go to [DigitalOcean App Platform](https://cloud.digitalocean.com/apps)
2. Create new app from GitHub
3. Configure as Python app
4. Set environment variables
5. Deploy

## 📋 Pre-deployment Checklist

- [ ] All environment variables are ready
- [ ] Bot token is valid and bot is created via @BotFather
- [ ] Outline VPN servers are configured and accessible
- [ ] Payment gateway credentials are set up
- [ ] Database will be created automatically (SQLite)
- [ ] All dependencies are in requirements.txt

## 🔍 Troubleshooting

### Common Issues:

1. **Bot not responding**: Check TELEGRAM_BOT_TOKEN
2. **Payment errors**: Verify CryptoBot API tokens
3. **VPN connection issues**: Check Outline server URLs
4. **Database errors**: Ensure write permissions

### Check Logs:

- Railway: Project → Deployments → View logs
- Render: Service → Logs
- Heroku: `heroku logs --tail`

## 🛡️ Security Notes

1. Never commit `.env` files to Git
2. Use environment variables for all secrets
3. Keep your bot token secure
4. Regularly update dependencies
5. Monitor bot usage and logs

## 📊 Monitoring

Your bot will automatically:

- Log all activities
- Handle errors gracefully
- Restart on failures
- Process payments securely

## 🎉 Success!

Once deployed, your bot will be available 24/7 and handle VPN subscriptions automatically!
