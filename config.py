import os
import logging
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()

# Initialize logger
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables or .env file")

# Outline Server API URLs for different countries
OUTLINE_SERVERS = {
    "germany": {
        "api_url": os.getenv("OUTLINE_API_URL_GERMANY"),
        "cert_sha256": os.getenv("OUTLINE_CERT_SHA256_GERMANY", ""),
        "name": "Germany",
        "flag": "🇩🇪"
    },
    "france": {
        "api_url": os.getenv("OUTLINE_API_URL_FRANCE"),
        "cert_sha256": os.getenv("OUTLINE_CERT_SHA256_FRANCE", ""),
        "name": "France",
        "flag": "🇫🇷"
    }
}

# Validate that at least one server is configured
if not any(server["api_url"] for server in OUTLINE_SERVERS.values()):
    raise ValueError("No Outline server API URLs found in environment variables")

# Legacy support - if old single server config exists, use it for Germany
if os.getenv("OUTLINE_API_URL") and not OUTLINE_SERVERS["germany"]["api_url"]:
    OUTLINE_SERVERS["germany"]["api_url"] = os.getenv("OUTLINE_API_URL")
    OUTLINE_SERVERS["germany"]["cert_sha256"] = os.getenv("OUTLINE_CERT_SHA256", "")

# Database file
DB_PATH = "vpn_subscriptions.db"

# Duration Plans (separate from country selection)
DURATION_PLANS = {
    "test_5min": {
        "name": "Test (5 min)", 
        "duration_days": 0.00347, 
        "price_usdt": 0.1
    },
    "1_month": {
        "name": "1 Month", 
        "duration_days": 30, 
        "price_usdt": 2.0
    },
    "3_months": {
        "name": "3 Months", 
        "duration_days": 90, 
        "price_usdt": 5.0
    },
    "1_year": {
        "name": "1 Year", 
        "duration_days": 365, 
        "price_usdt": 15.0
    }
}

# Country Packages (selected after payment)
COUNTRY_PACKAGES = {
    "5_countries": {
        "name": "5 Countries Package",
        "countries": ["germany", "france"],  # Will be extended as more countries are added
        "description": "Access to 5 different countries"
    },
    "10_countries": {
        "name": "10 Countries Package", 
        "countries": ["germany", "france"],  # Will be extended to 10 countries
        "description": "Access to 10 different countries"
    }
}

# Payment Gateway Details
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID", "YOUR_YOOKASSA_SHOP_ID")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY", "YOUR_YOOKASSA_SECRET_KEY")

# CryptoBot API Configuration
CRYPTOBOT_TESTNET_API_TOKEN = os.getenv("CRYPTOBOT_TESTNET_API_TOKEN")
CRYPTOBOT_MAINNET_API_TOKEN = os.getenv("CRYPTOBOT_MAINNET_API_TOKEN")
if not CRYPTOBOT_TESTNET_API_TOKEN:
    raise ValueError("CRYPTOBOT_TESTNET_API_TOKEN not found in environment variables or .env file")

# Debug log the token (first few characters for security)
masked_token = CRYPTOBOT_TESTNET_API_TOKEN[:8] + "..." + CRYPTOBOT_TESTNET_API_TOKEN[-4:]
logger.info(f"Loaded CryptoBot testnet token: {masked_token}")

# Use testnet for development
USE_TESTNET = True
CRYPTOBOT_API_TOKEN = CRYPTOBOT_TESTNET_API_TOKEN if USE_TESTNET else CRYPTOBOT_MAINNET_API_TOKEN

# Admin User ID
admin_user_id_str = os.getenv("ADMIN_USER_ID")
if admin_user_id_str and admin_user_id_str.isdigit():
    ADMIN_USER_ID = int(admin_user_id_str)
else:
    # Fallback or raise error if ADMIN_USER_ID is critical and not found
    # For now, let's set a placeholder if not found, but in production, you might want to raise an error.
    print("Warning: ADMIN_USER_ID not found or invalid in .env file. Admin features might not work correctly.")
    ADMIN_USER_ID = None # Or some default, or raise ValueError

# Rate Limiting (seconds)
# How many seconds a user must wait between triggering sensitive commands/actions
RATE_LIMIT_SECONDS = 5  # e.g., user can't use /subscribe more than once every 5 seconds
COMMAND_RATE_LIMIT = {"default": 3, "subscribe": 10} # seconds per command, default and specific
CALLBACK_RATE_LIMIT = 2 # seconds between callback queries from the same user
MESSAGE_RATE_LIMIT = 1 # seconds between general messages (less critical but can be useful)