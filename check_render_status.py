#!/usr/bin/env python3
"""
Script to check Render deployment status and help identify bot instances
"""
import os
import sys
import asyncio
import aiohttp
from config import TELEGRAM_BOT_TOKEN

async def check_bot_status():
    """Check the current bot status via Telegram API"""
    try:
        from telegram import Bot
        
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        
        # Get bot info
        me = await bot.get_me()
        print(f"✅ Bot info: {me.first_name} (@{me.username})")
        
        # Get webhook info
        webhook_info = await bot.get_webhook_info()
        print(f"📡 Webhook URL: {webhook_info.url or 'None'}")
        print(f"📊 Pending updates: {webhook_info.pending_update_count}")
        
        # Check if webhook is set
        if webhook_info.url:
            print("⚠️  WARNING: Webhook is configured! This might cause conflicts.")
            print("   The bot should use polling, not webhooks.")
            
            # Ask if user wants to delete webhook
            response = input("Do you want to delete the webhook? (y/n): ")
            if response.lower() == 'y':
                await bot.delete_webhook()
                print("✅ Webhook deleted successfully")
        else:
            print("✅ No webhook configured - using polling (correct)")
            
    except Exception as e:
        print(f"❌ Error checking bot status: {e}")

async def check_render_endpoints():
    """Check Render deployment endpoints"""
    # You'll need to replace this with your actual Render URL
    render_url = os.getenv("RENDER_URL", "https://your-bot-name.onrender.com")
    
    endpoints = [
        "/",
        "/health", 
        "/status",
        "/ping",
        "/test-bot"
    ]
    
    print(f"\n🔍 Checking Render endpoints at: {render_url}")
    
    async with aiohttp.ClientSession() as session:
        for endpoint in endpoints:
            try:
                url = f"{render_url}{endpoint}"
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        print(f"✅ {endpoint}: {response.status}")
                    else:
                        print(f"⚠️  {endpoint}: {response.status}")
            except Exception as e:
                print(f"❌ {endpoint}: Error - {e}")

def check_local_processes():
    """Check for local bot processes"""
    print("\n🔍 Checking local processes...")
    
    try:
        import subprocess
        result = subprocess.run(
            ["ps", "aux"], 
            capture_output=True, 
            text=True
        )
        
        lines = result.stdout.split('\n')
        bot_processes = []
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['main.py', 'start_bot', 'app.py', 'wsgi']):
                if 'grep' not in line:
                    bot_processes.append(line.strip())
        
        if bot_processes:
            print("⚠️  Found local bot processes:")
            for proc in bot_processes:
                print(f"   {proc}")
        else:
            print("✅ No local bot processes found")
            
    except Exception as e:
        print(f"❌ Error checking processes: {e}")

def main():
    """Main function"""
    print("🚀 VPN Bot Status Checker")
    print("=" * 40)
    
    # Check local processes
    check_local_processes()
    
    # Check bot status
    print("\n🤖 Checking bot status...")
    asyncio.run(check_bot_status())
    
    # Check Render endpoints (if URL is provided)
    if os.getenv("RENDER_URL"):
        asyncio.run(check_render_endpoints())
    else:
        print("\n📝 To check Render endpoints, set RENDER_URL environment variable")
        print("   Example: export RENDER_URL=https://your-bot-name.onrender.com")
    
    print("\n💡 Troubleshooting tips:")
    print("1. If you see webhook configured, delete it using the option above")
    print("2. If multiple local processes, kill them: pkill -f 'main.py'")
    print("3. If Render shows errors, check the logs in Render dashboard")
    print("4. Restart the Render service if needed")

if __name__ == "__main__":
    main() 