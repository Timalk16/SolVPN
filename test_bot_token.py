import os
import asyncio
from telegram import Bot

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def main():
    if not BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN not set in environment.")
        return
    bot = Bot(token=BOT_TOKEN)
    me = await bot.get_me()
    print(f"Bot info: {me.first_name} (@{me.username}) [ID: {me.id}]")
    webhook_info = await bot.get_webhook_info()
    print(f"Webhook URL: {webhook_info.url or 'None'}")
    print(f"Pending updates: {webhook_info.pending_update_count}")
    print("✅ Bot token is valid and bot is reachable!")

if __name__ == "__main__":
    asyncio.run(main()) 