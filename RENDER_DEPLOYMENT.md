# VPN Bot Render Deployment Guide

## 🚀 Deploy to Render.com

### Prerequisites

- GitHub repository with your VPN bot code
- All environment variables ready
- Valid Telegram bot token from @BotFather

### Step 1: Prepare Your Repository

1. Make sure all files are committed and pushed to GitHub:

   ```bash
   git add .
   git commit -m "Prepare for Render deployment"
   git push
   ```

2. Verify these files exist in your repository:
   - `app.py` (Flask web service wrapper)
   - `main.py` (Main bot logic)
   - `requirements.txt` (Python dependencies)
   - `render.yaml` (Render configuration)
   - `config.py` (Configuration file)
   - All other bot files

### Step 2: Deploy to Render

1. Go to [Render.com](https://render.com) and sign up/login
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Render will automatically detect the `render.yaml` configuration
5. Click "Create Web Service"

### Step 3: Configure Environment Variables

In the Render dashboard, go to your service → Environment tab and add:

**Required Variables:**

```
TELEGRAM_BOT_TOKEN=your_bot_token_here
ADMIN_USER_ID=your_telegram_user_id
CRYPTOBOT_TESTNET_API_TOKEN=your_cryptobot_token
```

**Optional Variables (if using mainnet):**

```
CRYPTOBOT_MAINNET_API_TOKEN=your_mainnet_token
```

**Outline VPN Server Variables:**

```
OUTLINE_API_URL_GERMANY=your_germany_server_url
OUTLINE_CERT_SHA256_GERMANY=your_germany_cert_sha256
OUTLINE_API_URL_FRANCE=your_france_server_url
OUTLINE_CERT_SHA256_FRANCE=your_france_cert_sha256
```

**Payment Gateway Variables (if using YooKassa):**

```
YOOKASSA_SHOP_ID=your_yookassa_shop_id
YOOKASSA_SECRET_KEY=your_yookassa_secret_key
```

### Step 4: Deploy

1. Click "Save Changes" in the Environment tab
2. Go to the "Manual Deploy" tab
3. Click "Deploy latest commit"
4. Wait for the build to complete (usually 2-3 minutes)

### Step 5: Verify Deployment

1. Check the logs in Render dashboard
2. Visit your service URL (e.g., `https://your-bot-name.onrender.com`)
3. Test the health endpoint: `https://your-bot-name.onrender.com/health`
4. Test your bot on Telegram

## 🔍 Health Check Endpoints

Your deployed service will have these endpoints:

- **Home**: `https://your-bot-name.onrender.com/`
- **Health Check**: `https://your-bot-name.onrender.com/health`
- **Status**: `https://your-bot-name.onrender.com/status`

## 📋 Pre-deployment Checklist

- [ ] All code is committed to GitHub
- [ ] `app.py` exists and contains Flask wrapper
- [ ] `requirements.txt` includes Flask
- [ ] `render.yaml` is configured correctly
- [ ] Environment variables are ready
- [ ] Bot token is valid
- [ ] Outline VPN servers are configured
- [ ] Payment gateway credentials are set up

## 🔧 Troubleshooting

### Common Issues:

1. **Build fails**: Check `requirements.txt` and Python version
2. **Bot not responding**: Verify `TELEGRAM_BOT_TOKEN`
3. **Payment errors**: Check CryptoBot API tokens
4. **VPN connection issues**: Verify Outline server URLs
5. **Service crashes**: Check logs for Python errors

### Check Logs:

- Go to your service in Render dashboard
- Click "Logs" tab
- Look for error messages or startup issues

### Database Issues:

- The bot uses SQLite which is ephemeral on Render
- Data will be lost on service restarts
- Consider migrating to a persistent database for production

## 🛡️ Security Notes

1. Never commit `.env` files to Git
2. Use environment variables for all secrets
3. Keep your bot token secure
4. Regularly update dependencies
5. Monitor bot usage and logs

## 📊 Monitoring

Your bot will automatically:

- Log all activities to Render logs
- Handle errors gracefully
- Restart on failures
- Process payments securely
- Provide health check endpoints

## 🎉 Success!

Once deployed, your bot will be available 24/7 and handle VPN subscriptions automatically!

### Next Steps:

1. Test all bot commands
2. Verify payment processing
3. Check VPN key generation
4. Monitor logs for any issues
5. Set up monitoring alerts if needed

## 🔄 Updates

To update your bot:

1. Make changes to your code
2. Commit and push to GitHub
3. Render will automatically redeploy
4. Check logs to ensure successful deployment
