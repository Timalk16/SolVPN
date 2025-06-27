#!/usr/bin/env python3
"""
Simple health check script for deployment platforms
"""
import os
import sys
import sqlite3
from config import TELEGRAM_BOT_TOKEN, DB_PATH

def check_environment():
    """Check if all required environment variables are set"""
    required_vars = [
        'TELEGRAM_BOT_TOKEN',
        'CRYPTOBOT_TESTNET_API_TOKEN'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ All required environment variables are set")
    return True

def check_database():
    """Check if database can be accessed"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        conn.close()
        print(f"✅ Database accessible, found {len(tables)} tables")
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def check_bot_token():
    """Check if bot token is valid format"""
    if TELEGRAM_BOT_TOKEN and len(TELEGRAM_BOT_TOKEN) > 40:
        print("✅ Bot token format looks valid")
        return True
    else:
        print("❌ Bot token appears invalid")
        return False

def main():
    """Run all health checks"""
    print("🔍 Running VPN Bot Health Checks...")
    print("=" * 40)
    
    checks = [
        check_environment(),
        check_database(),
        check_bot_token()
    ]
    
    print("=" * 40)
    if all(checks):
        print("✅ All health checks passed!")
        sys.exit(0)
    else:
        print("❌ Some health checks failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 