# Render Deployment Troubleshooting Guide

## 🚨 "No open ports detected" Warning

This warning appears when Render can't detect a web service running on the expected port. Here's how to fix it:

### Common Causes & Solutions

#### 1. **Flask App Not Starting**

**Symptoms**: App crashes during startup, no logs showing Flask running

**Solutions**:

- Check that `app.py` exists and is properly configured
- Verify Flask is in `requirements.txt`
- Check logs for Python import errors
- Ensure all environment variables are set

#### 2. **Port Binding Issues**

**Symptoms**: Flask starts but Render can't connect

**Solutions**:

- Ensure Flask app binds to `0.0.0.0` (not `localhost`)
- Use `os.environ.get('PORT', 5000)` for port
- Add `threaded=True` to `app.run()`

#### 3. **Bot Import Errors**

**Symptoms**: Flask app fails to start due to bot import issues

**Solutions**:

- Check all bot dependencies are in `requirements.txt`
- Verify environment variables are set
- Test bot imports locally first

### ✅ Fixed Configuration

The updated `app.py` now includes:

- ✅ Proper error handling
- ✅ Non-blocking bot startup
- ✅ Always starts Flask regardless of bot status
- ✅ Health check endpoint always returns 200
- ✅ Better logging

### 🔍 Debugging Steps

#### 1. Check Render Logs

Go to your service → Logs tab and look for:

```
Starting Flask web service on port XXXX
Starting Flask app on 0.0.0.0:XXXX
```

#### 2. Test Health Endpoints

After deployment, test:

- `https://your-app.onrender.com/health`
- `https://your-app.onrender.com/ping`
- `https://your-app.onrender.com/`

#### 3. Verify Environment Variables

Check that all required variables are set in Render dashboard:

- `TELEGRAM_BOT_TOKEN`
- `CRYPTOBOT_TESTNET_API_TOKEN`
- `ADMIN_USER_ID`
- Outline server URLs

### 🛠️ Quick Fixes

#### If Flask Won't Start:

1. Check `requirements.txt` includes Flask
2. Verify Python version in `runtime.txt`
3. Check for syntax errors in `app.py`

#### If Bot Won't Start:

1. Check environment variables
2. Verify bot token is valid
3. Check Outline server URLs

#### If Port Issues Persist:

1. Ensure `render.yaml` has `healthCheckPath: /health`
2. Verify Flask binds to `0.0.0.0`
3. Check port is set from environment

### 📋 Deployment Checklist

Before deploying:

- [ ] `app.py` exists and imports successfully
- [ ] `requirements.txt` includes Flask
- [ ] `render.yaml` has health check path
- [ ] All environment variables are ready
- [ ] Bot token is valid
- [ ] No syntax errors in code

### 🔄 Redeploy Steps

1. **Fix the issue** (see above)
2. **Commit and push**:
   ```bash
   git add .
   git commit -m "Fix port binding issues"
   git push
   ```
3. **Redeploy on Render**:
   - Go to Manual Deploy tab
   - Click "Deploy latest commit"
4. **Check logs** for successful startup
5. **Test endpoints** to verify working

### 📞 Still Having Issues?

If the problem persists:

1. Check Render logs for specific error messages
2. Test the Flask app locally first
3. Verify all dependencies are installed
4. Check environment variables are correct

### 🎯 Expected Behavior

After successful deployment, you should see:

- ✅ Flask app starts on port (from environment)
- ✅ Bot starts in background thread
- ✅ Health endpoint returns 200
- ✅ Service accessible via HTTPS
- ✅ No "No open ports detected" warnings
