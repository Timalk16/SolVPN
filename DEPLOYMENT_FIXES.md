# VPN Bot Deployment Fixes

## Issues Fixed

### 1. Syntax Warning: Invalid Escape Sequence

**Problem**: `SyntaxWarning: invalid escape sequence '\d'` in regex patterns
**Solution**: Added raw string prefix `r` to regex patterns

```python
# Before
pattern="^admin_del_\d+$"

# After
pattern=r"^admin_del_\d+$"
```

### 2. PTB Warnings: Conversation Handler Configuration

**Problem**: Warnings about `per_message=True` setting in conversation handlers
**Solution**: Removed `per_message=True` from both conversation handlers

```python
# Before
per_user=True,
per_chat=True,
per_message=True

# After
per_user=True,
per_chat=True
```

### 3. Development Server Warning

**Problem**: Using Flask's development server in production
**Solution**: Added Gunicorn WSGI server for production deployment

## Files Modified

### 1. `main.py`

- Fixed regex escape sequence on line 1078
- Removed `per_message=True` from conversation handlers

### 2. `requirements.txt`

- Added `gunicorn>=21.0.0` for production WSGI server

### 3. `render.yaml`

- Changed start command from `python app.py` to `gunicorn wsgi:application --bind 0.0.0.0:$PORT --workers 1 --timeout 120`

### 4. `wsgi.py` (New File)

- Created production WSGI entry point
- Handles bot startup in background thread
- Exports Flask app for Gunicorn

### 5. `deploy.sh` (Updated)

- Simplified deployment script
- Added deployment checklist
- Provides clear next steps

### 6. `test_local.py` (New File)

- Local testing suite
- Validates imports, configuration, and connections
- Helps verify bot before deployment

## Deployment Process

### 1. Test Locally

```bash
python test_local.py
```

### 2. Deploy to Render

```bash
# Commit changes
git add .
git commit -m "Fix deployment issues"
git push origin main

# Deploy on Render dashboard
# Or use Render CLI if configured
```

### 3. Verify Deployment

- Check Render logs for successful startup
- Visit your service URL (e.g., https://solvpn.onrender.com)
- Test health endpoint: `/health`
- Test bot functionality on Telegram

## Production Configuration

### WSGI Server

- **Server**: Gunicorn
- **Workers**: 1 (single worker for bot)
- **Timeout**: 120 seconds
- **Binding**: 0.0.0.0:$PORT

### Health Checks

- **Endpoint**: `/health`
- **Expected Response**: 200 OK with bot status

### Environment Variables

Required:

- `TELEGRAM_BOT_TOKEN`
- `ADMIN_USER_ID`

Optional:

- `CRYPTOBOT_TESTNET_API_TOKEN`
- `CRYPTOBOT_MAINNET_API_TOKEN`
- `OUTLINE_API_URL_GERMANY`
- `OUTLINE_CERT_SHA256_GERMANY`
- `OUTLINE_API_URL_FRANCE`
- `OUTLINE_CERT_SHA256_FRANCE`

## Monitoring

### Logs

- Bot logs are captured in Render dashboard
- Flask app logs are also available
- Background thread errors are logged

### Health Monitoring

- `/health` - Basic health check
- `/status` - Detailed status information
- `/ping` - Simple connectivity test
- `/test-bot` - Bot connection test

## Troubleshooting

### Common Issues

1. **Bot not responding**

   - Check if bot is running in background thread
   - Verify TELEGRAM_BOT_TOKEN is correct
   - Check bot permissions

2. **Deployment fails**

   - Ensure all required files are present
   - Check environment variables are set
   - Verify requirements.txt is up to date

3. **Health check fails**
   - Check if Flask app is running
   - Verify port binding
   - Check Render service logs

### Debug Commands

```bash
# Test locally
python test_local.py

# Run development server
python app.py

# Run production server locally
gunicorn wsgi:application --bind 0.0.0.0:5000

# Check deployment status
./deploy.sh
```

## Performance Notes

- Single worker configuration for bot stability
- Background thread for bot execution
- Flask app handles HTTP requests
- Proper timeout settings for long-running operations

## Security Considerations

- Environment variables for sensitive data
- No hardcoded tokens or keys
- Proper error handling without exposing internals
- Health checks without sensitive information
