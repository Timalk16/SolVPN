#!/usr/bin/env python3
"""
Test bot startup script for VLESS testing.
This script sets environment variables and starts the bot locally.
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Set test environment variables for VLESS testing
os.environ.update({
    # Bot configuration
    'TELEGRAM_BOT_TOKEN': '7736608927:AAG_aM5vyOuiJvC4dk7dY5ZdprFaowzqwds',  # Replace with your test bot token
    'ADMIN_USER_ID': '336181581',  # Replace with your user ID
    
    # Payment tokens (dummy values for testing)
    'CRYPTOBOT_TESTNET_API_TOKEN': 'dummy_testnet_token',
    'CRYPTOBOT_MAINNET_API_TOKEN': 'dummy_mainnet_token',
    
    # VLESS Configuration
    'VLESS_HOST': '127.0.0.1',  # Changed from 127.0.0.1 to actual server IP
    'VLESS_API_PORT': '62789',
    'VLESS_PUBLIC_HOST': '77.110.110.205',
    'VLESS_PORT': '443',
    'VLESS_SNI': 'www.github.com',
    'VLESS_PUBLIC_KEY': '-UjZAt_uWgBbne-xawPtZnWgMQD2-xtxRMaztwvTkUc',
    'VLESS_SHORT_ID': '0123abcd',
    
    # Optional: Add testnet token if you want to test payments
    # 'CRYPTOBOT_TESTNET_API_TOKEN': 'your_testnet_token',
})

# Load any existing .env file (will be overridden by the above variables)
load_dotenv()

print("🚀 Starting VLESS Test Bot...")
print("Environment variables set:")
for key, value in os.environ.items():
    if key.startswith(('TELEGRAM_BOT_TOKEN', 'ADMIN_USER_ID', 'VLESS_', 'CRYPTOBOT_')):
        # Mask sensitive values
        if 'TOKEN' in key or 'KEY' in key:
            print(f"  {key}: {value[:10]}...")
        else:
            print(f"  {key}: {value}")

print("\nStarting bot...")
print("Use /vless_subscribe to test VLESS functionality")
print("Press Ctrl+C to stop")

# Import and run the main bot
if __name__ == "__main__":
    try:
        from main import main
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        sys.exit(1) 