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
    "amsterdam": {
        "api_url": os.getenv("OUTLINE_API_URL_AMSTERDAM"),
        "cert_sha256": os.getenv("OUTLINE_CERT_SHA256_AMSTERDAM", ""),
        "name": "Amsterdam",
        "flag": "🇳🇱"
    }
}

# Validate that at least one server is configured
if not any(server["api_url"] for server in OUTLINE_SERVERS.values()):
    raise ValueError("No Outline server API URLs found in environment variables")

# Legacy support - if old single server config exists, use it for Germany
if os.getenv("OUTLINE_API_URL") and not OUTLINE_SERVERS["germany"]["api_url"]:
    OUTLINE_SERVERS["germany"]["api_url"] = os.getenv("OUTLINE_API_URL")
    OUTLINE_SERVERS["germany"]["cert_sha256"] = os.getenv("OUTLINE_CERT_SHA256", "")

# Database configuration
USE_POSTGRESQL = os.getenv("USE_POSTGRESQL", "true").lower() == "true"

# SQLite configuration (always defined for fallback)
DB_PATH = "vpn_subscriptions.db"

if USE_POSTGRESQL:
    # PostgreSQL configuration
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "vpn_bot")
    POSTGRES_USER = os.getenv("POSTGRES_USER", "vpn_bot_user")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
    
    # Construct PostgreSQL connection string
    POSTGRES_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    
    # For Render's internal PostgreSQL service
    if os.getenv("DATABASE_URL"):
        POSTGRES_URL = os.getenv("DATABASE_URL")

# Duration Plans (separate from country selection)
DURATION_PLANS = {
    "1_month": {
        "name": "Подписка на 1 месяц",
        "duration_days": 30,
        "price_usdt": 2.00,
        "price_rub": 159.00
    },
    "3_months": {
        "name": "Подписка на 3 месяца",
        "duration_days": 90,
        "price_usdt": 6.00,
        "price_rub": 450.00
    },
    "12_months": {
        "name": "Подписка на 12 месяцев",
        "duration_days": 365,
        "price_usdt": 23.00,
        "price_rub": 1850.00
    }
}

# Country Packages (selected after payment)
COUNTRY_PACKAGES = {
    "standard": {
        "name": "Стандартный пакет",
        "description": "Доступ к серверам в Германии и Амстердаме",
        "countries": ["germany", "amsterdam"]
    },
    "extended": {
        "name": "Расширенный пакет",
        "description": "Доступ к серверам в Германии и Амстердаме",
        "countries": ["germany", "amsterdam"]
    }
}

# Payment Gateway Details
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID", "YOUR_YOOKASSA_SHOP_ID")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY", "YOUR_YOOKASSA_SECRET_KEY")

# CryptoBot API Configuration
CRYPTOBOT_TESTNET_API_TOKEN = os.getenv("CRYPTOBOT_TESTNET_API_TOKEN")
CRYPTOBOT_MAINNET_API_TOKEN = os.getenv("CRYPTOBOT_MAINNET_API_TOKEN")

# Validate tokens based on network mode
if not CRYPTOBOT_TESTNET_API_TOKEN:
    logger.warning("CRYPTOBOT_TESTNET_API_TOKEN not found in environment variables")

if not CRYPTOBOT_MAINNET_API_TOKEN:
    logger.warning("CRYPTOBOT_MAINNET_API_TOKEN not found in environment variables")

# Debug log the token (first few characters for security)
masked_token = CRYPTOBOT_TESTNET_API_TOKEN[:8] + "..." + CRYPTOBOT_TESTNET_API_TOKEN[-4:]
logger.info(f"Loaded CryptoBot testnet token: {masked_token}")

# Debug log the mainnet token if available
if CRYPTOBOT_MAINNET_API_TOKEN:
    masked_mainnet_token = CRYPTOBOT_MAINNET_API_TOKEN[:8] + "..." + CRYPTOBOT_MAINNET_API_TOKEN[-4:]
    logger.info(f"Loaded CryptoBot mainnet token: {masked_mainnet_token}")
else:
    logger.warning("CRYPTOBOT_MAINNET_API_TOKEN not found in environment variables")

# Use mainnet for production
USE_TESTNET = False
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

VLESS_SERVERS = {
    "test": {
        "name": "Test VLESS Server",
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
}