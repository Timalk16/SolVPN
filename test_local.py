#!/usr/bin/env python3
"""
Simple test script to verify bot functionality locally
"""
import os
import sys
import asyncio
import warnings

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning, module="telegram")
warnings.filterwarnings("ignore", category=RuntimeWarning)

def test_imports():
    """Test if all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        from main import main
        print("✅ main.py imports successfully")
    except Exception as e:
        print(f"❌ Failed to import main.py: {e}")
        return False
    
    try:
        from app import app
        print("✅ app.py imports successfully")
    except Exception as e:
        print(f"❌ Failed to import app.py: {e}")
        return False
    
    try:
        from wsgi import application
        print("✅ wsgi.py imports successfully")
    except Exception as e:
        print(f"❌ Failed to import wsgi.py: {e}")
        return False
    
    return True

def test_config():
    """Test if required environment variables are set"""
    print("\n🔍 Testing configuration...")
    
    required_vars = [
        "TELEGRAM_BOT_TOKEN",
        "ADMIN_USER_ID"
    ]
    
    optional_vars = [
        "CRYPTOBOT_TESTNET_API_TOKEN",
        "CRYPTOBOT_MAINNET_API_TOKEN",
        "OUTLINE_API_URL_GERMANY",
        "OUTLINE_CERT_SHA256_GERMANY",
        "OUTLINE_API_URL_FRANCE",
        "OUTLINE_CERT_SHA256_FRANCE"
    ]
    
    missing_required = []
    missing_optional = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_required.append(var)
        else:
            print(f"✅ {var} is set")
    
    for var in optional_vars:
        if not os.getenv(var):
            missing_optional.append(var)
        else:
            print(f"✅ {var} is set")
    
    if missing_required:
        print(f"❌ Missing required environment variables: {', '.join(missing_required)}")
        return False
    
    if missing_optional:
        print(f"⚠️  Missing optional environment variables: {', '.join(missing_optional)}")
    
    return True

def test_flask_app():
    """Test if Flask app can start"""
    print("\n🔍 Testing Flask app...")
    
    try:
        from app import app
        with app.test_client() as client:
            response = client.get('/')
            if response.status_code == 200:
                print("✅ Flask app responds to requests")
                return True
            else:
                print(f"❌ Flask app returned status {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Flask app test failed: {e}")
        return False

async def test_bot_connection():
    """Test if bot can connect to Telegram"""
    print("\n🔍 Testing bot connection...")
    
    try:
        from telegram import Bot
        from config import TELEGRAM_BOT_TOKEN
        
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        me = await bot.get_me()
        print(f"✅ Bot connected successfully: @{me.username}")
        return True
    except Exception as e:
        print(f"❌ Bot connection failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 VPN Bot Local Test Suite")
    print("=" * 40)
    
    # Test imports
    if not test_imports():
        print("\n❌ Import tests failed. Please fix the issues above.")
        return False
    
    # Test configuration
    if not test_config():
        print("\n❌ Configuration tests failed. Please set the required environment variables.")
        return False
    
    # Test Flask app
    if not test_flask_app():
        print("\n❌ Flask app tests failed.")
        return False
    
    # Test bot connection
    try:
        result = asyncio.run(test_bot_connection())
        if not result:
            print("\n❌ Bot connection tests failed.")
            return False
    except Exception as e:
        print(f"\n❌ Bot connection test error: {e}")
        return False
    
    print("\n✅ All tests passed!")
    print("\n🎯 Your bot is ready for deployment!")
    print("   Run: ./deploy.sh for deployment instructions")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 