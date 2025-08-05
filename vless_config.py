#!/usr/bin/env python3
"""
Configuration for VLESS-only Telegram Bot
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# VLESS Server Configuration
VLESS_SERVERS = {
    "server1": {
        "name": "VLESS Server 1",
        "flag": "🚀",
        "host": os.getenv("VLESS_HOST", "127.0.0.1"),          # The IP where the Xray API is listening
        "api_port": int(os.getenv("VLESS_API_PORT", "62789")), # The port for the Xray API
        "public_host": os.getenv("VLESS_PUBLIC_HOST", "77.110.110.205"), # Your server's public domain or IP
        "port": int(os.getenv("VLESS_PORT", "443")),           # The public port for VLESS
        # --- REALITY PARAMS ---
        "sni": os.getenv("VLESS_SNI", "www.github.com"),    # SNI (Server Name Indication)
        "publicKey": os.getenv("VLESS_PUBLIC_KEY", "-UjZAt_uWgBbne-xawPtZnWgMQD2-xtxRMaztwvTkUc"),        # Public key from your Xray config
        "shortId": os.getenv("VLESS_SHORT_ID", "0123abcd"),    # Short ID from your Xray config
    }
    # Add more servers here when you have them:
    # "server2": {
    #     "name": "VLESS Server 2",
    #     "flag": "⚡",
    #     "host": "127.0.0.1",
    #     "api_port": 62789,
    #     "public_host": "88.220.220.220",
    #     "port": 443,
    #     "sni": "www.microsoft.com",
    #     "publicKey": "your-public-key-2",
    #     "shortId": "4567efgh",
    # }
}

# Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_USER_ID = os.getenv('ADMIN_USER_ID')

# Database Configuration
DB_PATH = "vless_subscriptions.db"

# Payment Configuration (optional)
CRYPTOBOT_TESTNET_API_TOKEN = os.getenv('CRYPTOBOT_TESTNET_API_TOKEN', 'dummy_testnet_token')
CRYPTOBOT_MAINNET_API_TOKEN = os.getenv('CRYPTOBOT_MAINNET_API_TOKEN', 'dummy_mainnet_token') 