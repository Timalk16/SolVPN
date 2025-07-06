#!/usr/bin/env python3
"""
WSGI entry point for production deployment
"""
import os
import sys
import time
import threading
import warnings

# Suppress warnings that might appear during bot startup
warnings.filterwarnings("ignore", category=UserWarning, module="telegram")
warnings.filterwarnings("ignore", category=RuntimeWarning)

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import Flask app
from app import app

# Global bot status
bot_status = {
    "running": False,
    "error": None,
    "startup_time": None,
    "last_check": None
}

def start_bot():
    """Start the bot in a separate thread"""
    global bot_status
    try:
        print("Starting VPN Bot in background thread...")
        bot_status["startup_time"] = time.time()
        bot_status["last_check"] = time.time()
        
        # Import the bot
        from main import main as run_bot
        
        print("Bot imports successful, starting main function...")
        
        # Create a new event loop for this thread
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Run the bot
            loop.run_until_complete(run_bot())
        except Exception as e:
            print(f"Bot runtime error: {e}")
            bot_status["error"] = str(e)
        finally:
            # Clean up the loop
            try:
                loop.close()
            except:
                pass
        
    except Exception as e:
        print(f"Bot startup error: {e}")
        import traceback
        traceback.print_exc()
        bot_status["error"] = str(e)
        bot_status["last_check"] = time.time()

# Start bot in background thread when module is imported
bot_thread = threading.Thread(target=start_bot, daemon=True)
bot_thread.start()

# Export the Flask app for WSGI servers
application = app 