#!/usr/bin/env python3
"""
Simple Flask web service for VPN Bot
Follows Render's port binding requirements exactly
"""
import os
import sys
import time
import threading
import warnings
from flask import Flask, jsonify

# Suppress warnings that might appear during bot startup
warnings.filterwarnings("ignore", category=UserWarning, module="telegram")
warnings.filterwarnings("ignore", category=RuntimeWarning)

# Create Flask app
app = Flask(__name__)

# Global bot status
bot_status = {
    "running": False,
    "error": None,
    "startup_time": None,
    "last_check": None
}

def start_flask():
    """Start Flask in a background thread"""
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Flask app on 0.0.0.0:{port}")
    app.run(
        host='0.0.0.0',  # Bind to all interfaces
        port=port,       # Use PORT from environment
        debug=False,     # Disable debug mode
        threaded=True,   # Enable threading
        use_reloader=False  # Disable reloader to avoid duplicate processes
    )

@app.route('/')
def home():
    """Home page"""
    # Check bot status
    check_bot_status()
    
    return jsonify({
        "service": "VPN Bot",
        "status": "running",
        "bot_status": bot_status,
        "endpoints": ["/health", "/status", "/ping"],
        "uptime": time.time() - bot_status.get("startup_time", time.time()) if bot_status.get("startup_time") else 0
    })

@app.route('/health')
def health():
    """Health check for Render"""
    # Check bot status
    check_bot_status()
    
    return jsonify({
        "status": "healthy",
        "bot_running": bot_status["running"],
        "bot_error": bot_status["error"]
    }), 200

@app.route('/status')
def status():
    """Detailed status"""
    # Check bot status
    check_bot_status()
    
    return jsonify({
        "service": "VPN Bot",
        "bot_status": bot_status,
        "port": os.environ.get('PORT', '5000'),
        "uptime": time.time() - bot_status.get("startup_time", time.time()) if bot_status.get("startup_time") else 0,
        "environment": {
            "has_telegram_token": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
            "has_cryptobot_token": bool(os.getenv("CRYPTOBOT_TESTNET_API_TOKEN")),
            "has_outline_servers": bool(os.getenv("OUTLINE_API_URL_GERMANY") or os.getenv("OUTLINE_API_URL_FRANCE"))
        }
    })

@app.route('/ping')
def ping():
    """Simple ping"""
    return jsonify({"pong": True, "time": time.time()})

@app.route('/test-bot')
def test_bot():
    """Test bot connection"""
    try:
        import asyncio
        from telegram import Bot
        from config import TELEGRAM_BOT_TOKEN
        
        async def check_bot():
            bot = Bot(token=TELEGRAM_BOT_TOKEN)
            me = await bot.get_me()
            webhook_info = await bot.get_webhook_info()
            return {
                "bot_name": me.first_name,
                "bot_username": me.username,
                "webhook_info": str(webhook_info),
                "pending_updates": webhook_info.pending_update_count
            }
        
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(check_bot())
        loop.close()
        
        return jsonify({
            "status": "success",
            "bot_info": result,
            "bot_status": bot_status
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "bot_status": bot_status
        }), 500

def check_bot_status():
    """Check if bot is still running"""
    global bot_status
    if bot_status["startup_time"] and time.time() - bot_status["startup_time"] > 10:
        # Bot has been running for more than 10 seconds, consider it successful
        if not bot_status["running"] and not bot_status["error"]:
            bot_status["running"] = True
            print("Bot appears to be running successfully")

def main():
    """Main function to start the service"""
    # Get port from environment (Render requirement)
    port = int(os.environ.get('PORT', 5000))
    
    print(f"Starting VPN Bot service on port {port}")
    print(f"Environment PORT: {os.environ.get('PORT', 'not set')}")
    
    # Start Flask in a background thread
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()
    print("Flask thread started successfully")
    
    # Give Flask a moment to start
    time.sleep(2)
    
    # Start the bot in the main thread (this avoids signal handler issues)
    try:
        print("Starting VPN Bot in main thread...")
        bot_status["startup_time"] = time.time()
        bot_status["last_check"] = time.time()
        
        # Import and run the bot
        from main import main as run_bot
        import asyncio
        
        print("Bot imports successful, starting main function...")
        
        # Run the bot in the main thread
        asyncio.run(run_bot())
        
    except Exception as e:
        print(f"Bot error: {e}")
        import traceback
        traceback.print_exc()
        bot_status["running"] = False
        bot_status["error"] = str(e)
        bot_status["last_check"] = time.time()

if __name__ == '__main__':
    main() 