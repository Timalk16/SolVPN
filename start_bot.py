#!/usr/bin/env python3
"""
VPN Bot Startup Script
This script properly handles event loop conflicts and provides better error handling.
"""

import asyncio
import sys
import os
import signal
import logging

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print(f"\nReceived signal {signum}, shutting down gracefully...")
    sys.exit(0)

def run_bot():
    """Run the bot with proper event loop handling."""
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Check if we're already in an event loop
        try:
            loop = asyncio.get_running_loop()
            print(f"Warning: Event loop is already running: {loop}")
            print("This might cause issues. Try running this script in a fresh terminal.")
            return
        except RuntimeError:
            # No event loop running, we're good
            pass
        
        # Import and run the main function
        from main import main
        
        print("Starting VPN bot...")
        print("Press Ctrl+C to stop the bot gracefully.")
        
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\nBot stopped by user (Ctrl+C).")
    except Exception as e:
        print(f"Error running bot: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = run_bot()
    sys.exit(exit_code) 