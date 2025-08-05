#!/usr/bin/env python3
"""
Simplified VLESS-only Telegram Bot for VPS deployment
This bot generates VLESS URIs without gRPC API calls
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Import simplified VLESS functionality
from vless_config import VLESS_SERVERS
from vless_database import init_vless_db, add_vless_subscription
from vless_utils_simple import add_vless_user

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_USER_ID = os.getenv('ADMIN_USER_ID')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        f"Hi {user.mention_html()}! 👋\n\n"
        "🚀 Welcome to VLESS VPN Bot!\n\n"
        "Available commands:\n"
        "/vless_subscribe - Get VLESS VPN access\n"
        "/help - Show this help message\n\n"
        "This bot provides secure VLESS VPN connections."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = """
🤖 **VLESS VPN Bot Help**

**Commands:**
• `/start` - Start the bot
• `/vless_subscribe` - Get VLESS VPN access
• `/help` - Show this help

**Features:**
• 🚀 High-speed VLESS VPN
• 🔒 REALITY protocol for security
• ⚡ Fast and reliable connections
• 📱 Works on all devices

**How to use:**
1. Send `/vless_subscribe`
2. Get your VLESS URI
3. Use a V2Ray/Xray client to connect

**Supported clients:**
• V2RayN (Windows)
• V2RayU (macOS)
• V2RayNG (Android)
• Shadowrocket (iOS)
• And many more!

Need help? Contact the administrator.
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def vless_subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle VLESS subscription requests."""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    logger.info(f"vless_subscribe function called")
    logger.info(f"Processing VLESS subscription for user {user_id}")
    
    try:
        # Initialize VLESS database
        logger.info("Initializing VLESS database...")
        init_vless_db()
        logger.info("VLESS database initialized")
        
        # Get server configuration
        logger.info("Getting server config...")
        server_config = VLESS_SERVERS["server1"]  # Use first server
        logger.info(f"Server config: {server_config}")
        
        # Add VLESS user (simplified approach)
        logger.info("Adding VLESS user...")
        user_uuid, vless_uri = add_vless_user(server_config, str(user_id), expiry_days=7)
        logger.info(f"VLESS user added - UUID: {user_uuid}, URI: {vless_uri}")
        
        if user_uuid and vless_uri:
            # Calculate expiry date
            expiry_date = datetime.now() + timedelta(days=7)
            
            # Store subscription in database
            add_vless_subscription(user_id, user_uuid, vless_uri, expiry_date)
            
            # Send response to user
            response = (
                f"{server_config['flag']} Your VLESS VPN ({server_config['name']}) is ready!\n\n"
                f"**VLESS URI:**\n`{vless_uri}`\n\n"
                f"**Valid until:** {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"📱 Use a V2Ray/Xray client to connect.\n"
                f"🔒 This connection uses REALITY protocol for enhanced security.\n\n"
                f"**Note:** This is a test version that generates URIs without server-side user management."
            )
            
            await update.message.reply_text(response, parse_mode='Markdown')
            logger.info("Response sent to user successfully")
            
        else:
            logger.error("Failed to create VLESS user")
            await update.message.reply_text(
                "❌ Sorry, there was an error creating your VLESS subscription.\n"
                "Please try again later or contact the administrator."
            )
            
    except Exception as e:
        logger.error(f"Error in vless_subscribe: {e}")
        await update.message.reply_text(
            "❌ An error occurred while processing your request.\n"
            "Please try again later."
        )

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle unknown commands."""
    await update.message.reply_text(
        "❓ Unknown command. Use /help to see available commands."
    )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main() -> None:
    """Start the bot."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set in environment variables")
        return
    
    if not ADMIN_USER_ID:
        logger.error("ADMIN_USER_ID not set in environment variables")
        return
    
    # Create the Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("vless_subscribe", vless_subscribe))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Add unknown command handler (must be last)
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    
    # Start the bot
    logger.info("Starting simplified VLESS-only bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main() 