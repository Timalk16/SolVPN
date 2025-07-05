#!/usr/bin/env python3
"""
Simple Flask web service for VPN Bot
Follows Render's port binding requirements exactly
"""
import os
import sys
import time
import threading
from flask import Flask, jsonify

# Create Flask app
app = Flask(__name__)

# Global bot status
bot_status = {
    "running": False,
    "error": None,
    "startup_time": None
}

def start_bot():
    """Start the bot in a background thread"""
    global bot_status
    try:
        print("Starting VPN Bot in background...")
        bot_status["startup_time"] = time.time()
        
        # Import and run the bot
        from main import main
        import asyncio
        
        bot_status["running"] = True
        bot_status["error"] = None
        print("Bot started successfully")
        
        # Run the bot
        asyncio.run(main())
    except Exception as e:
        print(f"Bot error: {e}")
        bot_status["running"] = False
        bot_status["error"] = str(e)

@app.route('/')
def home():
    """Home page"""
    return jsonify({
        "service": "VPN Bot",
        "status": "running",
        "bot_status": bot_status,
        "endpoints": ["/health", "/status", "/ping"]
    })

@app.route('/health')
def health():
    """Health check for Render"""
    return jsonify({"status": "healthy"}), 200

@app.route('/status')
def status():
    """Detailed status"""
    return jsonify({
        "service": "VPN Bot",
        "bot_status": bot_status,
        "port": os.environ.get('PORT', '5000'),
        "environment": {
            "has_telegram_token": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
            "has_cryptobot_token": bool(os.getenv("CRYPTOBOT_TESTNET_API_TOKEN"))
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
        print("Bot thread started")
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