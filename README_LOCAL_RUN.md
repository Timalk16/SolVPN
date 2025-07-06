# VPN Bot - Local Running Instructions

## Problem Fixed

The bot was having issues with event loop conflicts when running locally. This has been resolved by modifying the polling mechanism in `main.py`.

## How to Run the Bot Locally

### Option 1: Using the startup script (Recommended)

```bash
./start.sh
```

### Option 2: Using Python directly

```bash
python start_bot.py
```

### Option 3: Using the main file directly

```bash
python main.py
```

## What Was Fixed

1. **Event Loop Conflict**: The main issue was that `python-telegram-bot` was trying to manage its own event loop internally, causing conflicts with the existing environment.

2. **Polling Mechanism**: Modified the polling approach in `main.py` to use a more explicit method:

   - `await application.initialize()`
   - `await application.start()`
   - `await application.updater.start_polling()`
   - Added proper shutdown handling

3. **Error Handling**: Added better error handling and graceful shutdown capabilities.

## Files Created/Modified

- `main.py` - Fixed the polling mechanism
- `start_bot.py` - New startup script with better error handling
- `start.sh` - Shell script for easy startup
- `test_simple_bot.py` - Simple test bot (for debugging)

## Environment Variables Required

Make sure you have these environment variables set (either in your shell or in a `.env` file):

- `TELEGRAM_BOT_TOKEN` - Your Telegram bot token
- `CRYPTOBOT_TESTNET_API_TOKEN` - CryptoBot API token
- `ADMIN_USER_ID` - Your Telegram user ID for admin access
- `OUTLINE_API_URL_GERMANY` - Outline server URL for Germany
- `OUTLINE_API_URL_FRANCE` - Outline server URL for France

## Troubleshooting

If you still get event loop errors:

1. Make sure you're not running this in Jupyter notebook or IPython
2. Try running in a fresh terminal session
3. Use the `start_bot.py` script which has better error handling
4. Check that your virtual environment is properly activated

## Deployment to Render

The bot should now work properly on Render as well. The event loop issue was specific to local development environments with certain configurations.

## Stopping the Bot

Press `Ctrl+C` to stop the bot gracefully. The bot will properly shut down and clean up resources.
