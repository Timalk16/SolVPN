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

def start_bot():
    """Start the bot in a background thread"""
    global bot_status
    try:
        print("Starting VPN Bot in background...")
        bot_status["startup_time"] = time.time()
        bot_status["last_check"] = time.time()
        
        # Import and run the bot
        from main import main
        import asyncio
        
        print("Bot imports successful, starting main function...")
        
        # Run the bot
        asyncio.run(main())
        
        # If we get here, the bot has stopped
        bot_status["running"] = False
        bot_status["error"] = "Bot stopped unexpectedly"
        print("Bot stopped unexpectedly")
        
    except Exception as e:
        print(f"Bot error: {e}")
        bot_status["running"] = False
        bot_status["error"] = str(e)
        bot_status["last_check"] = time.time()

def check_bot_status():
    """Check if bot is still running"""
    global bot_status
    if bot_status["startup_time"] and time.time() - bot_status["startup_time"] > 10:
        # Bot has been running for more than 10 seconds, consider it successful
        if not bot_status["running"] and not bot_status["error"]:
            bot_status["running"] = True
            print("Bot appears to be running successfully")

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

def main():
    """Main function to start the service"""
    # Get port from environment (Render requirement)
    port = int(os.environ.get('PORT', 5000))
    
    print(f"Starting Flask service on port {port}")
    print(f"Environment PORT: {os.environ.get('PORT', 'not set')}")
    
    # Start bot in background thread
    try:
        bot_thread = threading.Thread(target=start_bot, daemon=True)
        bot_thread.start()
        print("Bot thread started successfully")
    except Exception as e:
        print(f"Failed to start bot thread: {e}")
        bot_status["error"] = str(e)
    
    # Start Flask app (this is the critical part for Render)
    print(f"Starting Flask app on 0.0.0.0:{port}")
    app.run(
        host='0.0.0.0',  # Bind to all interfaces
        port=port,       # Use PORT from environment
        debug=False,     # Disable debug mode
        threaded=True    # Enable threading
    )

if __name__ == '__main__':
    main() 