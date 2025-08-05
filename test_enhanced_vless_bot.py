#!/usr/bin/env python3
"""
Test script for Enhanced VLESS Bot functionality
"""

import os
import sys
import asyncio
from datetime import datetime, timedelta

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from vless_database import init_vless_db, add_vless_subscription, get_user_subscription, remove_vless_subscription

def test_database_functions():
    """Test database functions."""
    print("Testing database functions...")
    
    # Initialize database
    init_vless_db()
    
    # Test user subscription
    test_user_id = 12345
    test_uuid = "test-uuid-12345"
    test_uri = "vless://test-uuid-12345@77.110.110.205:443?encryption=none&security=reality&sni=www.microsoft.com&fp=chrome&pbk=test-key&sid=test-sid&type=tcp&flow=xtls-rprx-vision#test-user"
    test_expiry = datetime.now() + timedelta(days=7)
    
    # Add subscription
    add_vless_subscription(test_user_id, test_uuid, test_uri, test_expiry)
    print("✅ Added subscription")
    
    # Get subscription
    subscription = get_user_subscription(test_user_id)
    if subscription:
        print(f"✅ Retrieved subscription: {subscription['vless_uuid']}")
    else:
        print("❌ Failed to retrieve subscription")
    
    # Remove subscription
    remove_vless_subscription(test_user_id)
    print("✅ Removed subscription")
    
    # Verify removal
    subscription_after = get_user_subscription(test_user_id)
    if not subscription_after:
        print("✅ Subscription successfully removed")
    else:
        print("❌ Subscription still exists after removal")

def test_config_management():
    """Test config file management functions."""
    print("\nTesting config management functions...")
    
    # Import the functions from the enhanced bot
    try:
        from vless_only_bot_enhanced import read_json_file, write_json_file, generate_vless_link_from_config
        
        # Test reading config (if it exists)
        config_path = "/usr/local/etc/xray/config.json"
        if os.path.exists(config_path):
            config = read_json_file(config_path)
            if config:
                print("✅ Successfully read Xray config")
            else:
                print("❌ Failed to read Xray config")
        else:
            print("⚠️ Xray config file not found (expected for testing)")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")

def test_management_modes():
    """Test different management modes."""
    print("\nTesting management modes...")
    
    # Test environment variable setting
    os.environ['MANAGEMENT_MODE'] = 'grpc'
    print("✅ Set MANAGEMENT_MODE to 'grpc'")
    
    os.environ['MANAGEMENT_MODE'] = 'config_file'
    print("✅ Set MANAGEMENT_MODE to 'config_file'")

if __name__ == "__main__":
    print("🧪 Testing Enhanced VLESS Bot Components")
    print("=" * 50)
    
    test_database_functions()
    test_config_management()
    test_management_modes()
    
    print("\n" + "=" * 50)
    print("✅ All tests completed!")
    print("\nTo test the full bot:")
    print("1. Set your TELEGRAM_BOT_TOKEN and ADMIN_USER_ID environment variables")
    print("2. Run: python3 vless_only_bot_enhanced.py")
    print("3. Or set MANAGEMENT_MODE=config_file to use direct config.json modification") 