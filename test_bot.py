#!/usr/bin/env python3
"""
Simple bot test script
"""
import os
import asyncio
from telegram import Bot
from config import TELEGRAM_BOT_TOKEN

async def test_bot():
    """Test basic bot functionality"""
    try:
        print(f"Testing bot token: {TELEGRAM_BOT_TOKEN[:10]}...")
        
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        
        # Get bot info
        me = await bot.get_me()
        print(f"Bot info: {me.first_name} (@{me.username})")
        
        # Test webhook info
        webhook_info = await bot.get_webhook_info()
        print(f"Webhook info: {webhook_info}")
        
        print("✅ Bot token is valid and working!")
        return True
        
    except Exception as e:
        print(f"❌ Bot test failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_bot()) 