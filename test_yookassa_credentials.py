#!/usr/bin/env python3
"""
Test script to verify Youkassa credentials are working correctly
"""

import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_yookassa_configuration():
    """Test if Youkassa credentials are properly configured"""
    print("🔍 Testing Youkassa Configuration...")
    
    # Check environment variables
    shop_id = os.getenv("YOOKASSA_SHOP_ID")
    secret_key = os.getenv("YOOKASSA_SECRET_KEY")
    
    print(f"YOOKASSA_SHOP_ID: {'✅ Set' if shop_id and shop_id != 'YOUR_YOOKASSA_SHOP_ID' else '❌ Not set or default'}")
    print(f"YOOKASSA_SECRET_KEY: {'✅ Set' if secret_key and secret_key != 'YOUR_YOOKASSA_SECRET_KEY' else '❌ Not set or default'}")
    
    if not shop_id or shop_id == "YOUR_YOOKASSA_SHOP_ID":
        print("\n❌ YOOKASSA_SHOP_ID is not properly configured!")
        return False
    
    if not secret_key or secret_key == "YOUR_YOOKASSA_SECRET_KEY":
        print("\n❌ YOOKASSA_SECRET_KEY is not properly configured!")
        return False
    
    print("\n✅ Youkassa credentials appear to be configured correctly!")
    return True

async def test_yookassa_connection():
    """Test Youkassa API connection"""
    print("\n🔍 Testing Youkassa API Connection...")
    
    try:
        from payment_utils import get_yookassa_payment_details
        
        # Try to create a test payment
        instructions, payment_id = await get_yookassa_payment_details(10.0, "Test Payment")
        
        print(f"✅ Successfully created test payment!")
        print(f"Payment ID: {payment_id}")
        print(f"Instructions preview: {instructions[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Youkassa connection: {e}")
        return False

async def main():
    """Main test function"""
    print("🧪 Youkassa Credentials Test\n")
    
    # Test configuration
    config_ok = test_yookassa_configuration()
    
    if not config_ok:
        print("\n❌ Configuration test failed. Please check your .env file.")
        return
    
    # Test connection
    connection_ok = await test_yookassa_connection()
    
    if connection_ok:
        print("\n🎉 All tests passed! Youkassa is properly configured.")
    else:
        print("\n❌ Connection test failed. Please check your credentials.")

if __name__ == "__main__":
    asyncio.run(main()) 