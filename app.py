#!/usr/bin/env python3
"""
Flask web service wrapper for the VPN Bot
This allows the bot to run on Render as a web service with health checks
"""
import os
import threading
import logging
import time
from flask import Flask, jsonify
import asyncio

# Configure logging first
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global variable to track bot status
bot_status = {"running": False, "error": None, "startup_time": None}

def run_bot_in_thread():
    """Run the bot in a separate thread"""
    global bot_status
    try:
        logger.info("Starting VPN Bot in background thread...")
        bot_status["startup_time"] = time.time()
        
        # Import here to avoid import errors during startup
        from main import main as run_bot
        
        bot_status["running"] = True
        bot_status["error"] = None
        logger.info("VPN Bot thread started successfully")
        
        # Run the bot
        asyncio.run(run_bot())
    except Exception as e:
        logger.error(f"Bot error: {e}")
        bot_status["running"] = False
        bot_status["error"] = str(e)

@app.route('/')
def home():
    """Home endpoint"""
    return jsonify({
        "status": "VPN Bot Web Service",
        "bot_status": bot_status,
        "message": "This is a Telegram VPN Bot service",
        "endpoints": {
            "health": "/health",
            "status": "/status"
        }
    })

@app.route('/health')
def health():
    """Health check endpoint for Render"""
    # Always return 200 for the web service itself
    # The bot status is tracked separately
    return jsonify({
        "status": "healthy",
        "service": "web",
        "bot_status": bot_status["running"],
        "bot_error": bot_status["error"]
    }), 200

@app.route('/status')
def status():
    """Detailed status endpoint"""
    return jsonify({
        "service": "VPN Bot Web Service",
        "bot_status": bot_status,
        "environment": {
            "has_telegram_token": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
            "has_cryptobot_token": bool(os.getenv("CRYPTOBOT_TESTNET_API_TOKEN")),
            "has_outline_servers": bool(os.getenv("OUTLINE_API_URL_GERMANY") or os.getenv("OUTLINE_API_URL_FRANCE")),
            "port": os.environ.get('PORT', '5000')
        }
    })

@app.route('/ping')
def ping():
    """Simple ping endpoint"""
    return jsonify({"pong": True, "timestamp": time.time()})

if __name__ == '__main__':
    # Get port from environment (Render sets PORT)
    port = int(os.environ.get('PORT', 5000))
    
    logger.info(f"Starting Flask web service on port {port}")
    
    # Start the bot in a separate thread (non-blocking)
    try:
        bot_thread = threading.Thread(target=run_bot_in_thread, daemon=True)
        bot_thread.start()
        logger.info("Bot thread started successfully")
    except Exception as e:
        logger.error(f"Failed to start bot thread: {e}")
        bot_status["error"] = f"Failed to start bot thread: {e}"
    
    # Always start the Flask app regardless of bot status
    logger.info(f"Starting Flask app on 0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True) 