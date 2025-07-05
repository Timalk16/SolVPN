#!/usr/bin/env python3
"""
Flask web service wrapper for the VPN Bot
This allows the bot to run on Render as a web service with health checks
"""
import os
import threading
import logging
from flask import Flask, jsonify
import asyncio

# Import the main bot function
from main import main as run_bot

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global variable to track bot status
bot_status = {"running": False, "error": None}

def run_bot_in_thread():
    """Run the bot in a separate thread"""
    global bot_status
    try:
        bot_status["running"] = True
        bot_status["error"] = None
        logger.info("Starting VPN Bot...")
        
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
        "status": "VPN Bot is running",
        "bot_status": bot_status,
        "message": "This is a Telegram VPN Bot service"
    })

@app.route('/health')
def health():
    """Health check endpoint for Render"""
    if bot_status["running"]:
        return jsonify({"status": "healthy", "bot": "running"}), 200
    else:
        return jsonify({
            "status": "unhealthy", 
            "bot": "not running",
            "error": bot_status["error"]
        }), 503

@app.route('/status')
def status():
    """Detailed status endpoint"""
    return jsonify({
        "service": "VPN Bot",
        "bot_status": bot_status,
        "environment": {
            "has_telegram_token": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
            "has_cryptobot_token": bool(os.getenv("CRYPTOBOT_TESTNET_API_TOKEN")),
            "has_outline_servers": bool(os.getenv("OUTLINE_API_URL_GERMANY") or os.getenv("OUTLINE_API_URL_FRANCE"))
        }
    })

if __name__ == '__main__':
    # Start the bot in a separate thread
    bot_thread = threading.Thread(target=run_bot_in_thread, daemon=True)
    bot_thread.start()
    
    # Get port from environment (Render sets PORT)
    port = int(os.environ.get('PORT', 5000))
    
    logger.info(f"Starting Flask web service on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False) 