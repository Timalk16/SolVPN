#!/usr/bin/env python3
"""
Enhanced VLESS-only Telegram Bot for VPS deployment
This bot handles VLESS VPN functionality with integrated user management.
"""

import os
import asyncio
import logging
import json
import subprocess
import uuid
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Import VLESS functionality
from vless_config import VLESS_SERVERS
from vless_database import init_vless_db, add_vless_subscription, get_user_subscription, remove_vless_subscription
from vless_utils import add_vless_user, remove_vless_user, generate_vless_uri

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

# Xray configuration paths (for direct config management)
CONFIG_PATH = "/usr/local/etc/xray/config.json"
SERVER_INFO_PATH = "/usr/local/etc/xray/server_info.json"
XRAY_BINARY_PATH = "/usr/local/bin/xray"

# Management mode: 'grpc' or 'config_file'
MANAGEMENT_MODE = os.getenv('MANAGEMENT_MODE', 'grpc')  # Default to gRPC

def run_command(command):
    """Безопасно выполняет системную команду и возвращает ее вывод."""
    try:
        process = subprocess.run(
            command, capture_output=True, text=True, check=True, encoding='utf-8'
        )
        return process.stdout.strip()
    except FileNotFoundError:
        logger.error(f"Ошибка: Команда не найдена. Убедитесь, что '{command[0]}' установлен и доступен в PATH.")
        return None
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка при выполнении команды '{' '.join(command)}': {e.stderr}")
        return None

def read_json_file(path):
    """Читает и возвращает содержимое JSON файла."""
    if not os.path.exists(path):
        logger.error(f"Ошибка: Файл конфигурации {path} не найден!")
        return None
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.error(f"Ошибка: Не удалось декодировать JSON из файла {path}.")
        return None

def write_json_file(path, data):
    """Записывает данные в JSON файл."""
    try:
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except IOError as e:
        logger.error(f"Критическая ошибка записи в файл {path}: {e}")
        return False

def restart_xray():
    """Перезапускает сервис Xray и проверяет статус."""
    logger.info("Перезапуск сервиса Xray...")
    run_command(["systemctl", "restart", "xray"])
    status = run_command(["systemctl", "is-active", "xray"])
    if status == "active":
        logger.info("-> Сервис Xray успешно перезапущен.")
        return True
    else:
        logger.error("-> ВНИМАНИЕ! Сервис Xray не смог запуститься после перезапуска.")
        return False

def generate_vless_link_from_config(user_uuid, email):
    """
    Генерирует ссылку VLESS, читая ВСЕ параметры из файлов конфигурации.
    """
    server_info = read_json_file(SERVER_INFO_PATH)
    config = read_json_file(CONFIG_PATH)

    if not server_info or not config:
        return "Не удалось сгенерировать ссылку: отсутствуют файлы конфигурации."

    # Извлекаем все необходимые данные
    server_ip = server_info.get("server_ip")
    public_key = server_info.get("public_key")
    sni = server_info.get("sni")
    short_id = config['inbounds'][0]['streamSettings']['realitySettings']['shortIds'][0]
    
    # Проверяем, что все данные на месте
    if not all([server_ip, public_key, sni, short_id]):
         return "Ошибка: в файлах конфигурации не хватает данных для генерации ссылки."

    link = (
        f"vless://{user_uuid}@{server_ip}:443?"
        f"encryption=none&security=reality&sni={sni}&fp=chrome"
        f"&pbk={public_key}&sid={short_id}&type=tcp&flow=xtls-rprx-vision"
        f"#{email}"
    )
    return link

def add_user_via_config(email):
    """Добавляет нового пользователя в config.json."""
    config = read_json_file(CONFIG_PATH)
    if not config: return None, None

    # Проверяем, не существует ли уже пользователь с таким email
    for client in config['inbounds'][0]['settings']['clients']:
        if client.get("email") == email:
            logger.error(f"Ошибка: Пользователь с email '{email}' уже существует.")
            return None, None

    # Генерируем новый UUID
    user_uuid = run_command([XRAY_BINARY_PATH, "uuid"])
    if not user_uuid:
        logger.error("Не удалось сгенерировать UUID для нового пользователя.")
        return None, None

    new_client = {
        "id": user_uuid,
        "email": email,
        "flow": "xtls-rprx-vision"
    }

    config['inbounds'][0]['settings']['clients'].append(new_client)
    
    if write_json_file(CONFIG_PATH, config) and restart_xray():
        logger.info(f"Пользователь '{email}' успешно добавлен через config.json.")
        link = generate_vless_link_from_config(user_uuid, email)
        return user_uuid, link
    else:
        logger.error("Ошибка при добавлении пользователя через config.json.")
        return None, None

def remove_user_via_config(email):
    """Удаляет пользователя из config.json по email."""
    config = read_json_file(CONFIG_PATH)
    if not config: return False

    clients = config['inbounds'][0]['settings']['clients']
    original_user_count = len(clients)
    
    # Создаем новый список без удаляемого пользователя
    clients_after_removal = [client for client in clients if client.get("email") != email]

    if len(clients_after_removal) == original_user_count:
        logger.error(f"Ошибка: Пользователь с email '{email}' не найден.")
        return False

    config['inbounds'][0]['settings']['clients'] = clients_after_removal

    if write_json_file(CONFIG_PATH, config) and restart_xray():
        logger.info(f"Пользователь '{email}' успешно удален через config.json.")
        return True
    else:
        logger.error("Ошибка при удалении пользователя через config.json.")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        f"Hi {user.mention_html()}! 👋\n\n"
        "🚀 Welcome to Enhanced VLESS VPN Bot!\n\n"
        "Available commands:\n"
        "/vless_subscribe - Get VLESS VPN access\n"
        "/my_subscription - Check your current subscription\n"
        "/help - Show this help message\n\n"
        "This bot provides secure VLESS VPN connections."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = """
🤖 **Enhanced VLESS VPN Bot Help**

**Commands:**
• `/start` - Start the bot
• `/vless_subscribe` - Get VLESS VPN access
• `/my_subscription` - Check your current subscription
• `/help` - Show this help

**Features:**
• 🚀 High-speed VLESS VPN
• 🔒 REALITY protocol for security
• ⚡ Fast and reliable connections
• 📱 Works on all devices
• 🔄 Automatic user management

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
    user_email = f"user-{user_id}"
    
    logger.info(f"Processing VLESS subscription for user {user_id}")
    
    try:
        # Initialize VLESS database
        logger.info("Initializing VLESS database...")
        init_vless_db()
        logger.info("VLESS database initialized")
        
        # Check if user already has an active subscription
        existing_sub = get_user_subscription(user_id)
        if existing_sub:
            await update.message.reply_text(
                "⚠️ You already have an active subscription!\n"
                "Use /my_subscription to check your current access."
            )
            return
        
        user_uuid = None
        vless_uri = None
        
        if MANAGEMENT_MODE == 'grpc':
            # Use gRPC API approach
            logger.info("Using gRPC API for user management...")
            server_config = VLESS_SERVERS["server1"]
            user_uuid, vless_uri = add_vless_user(server_config, str(user_id), expiry_days=7)
        else:
            # Use direct config.json modification
            logger.info("Using direct config.json modification...")
            user_uuid, vless_uri = add_user_via_config(user_email)
        
        if user_uuid and vless_uri:
            # Calculate expiry date
            expiry_date = datetime.now() + timedelta(days=7)
            
            # Store subscription in database
            add_vless_subscription(user_id, user_uuid, vless_uri, expiry_date)
            
            # Send response to user
            response = (
                f"🚀 Your VLESS VPN is ready!\n\n"
                f"**VLESS URI:**\n`{vless_uri}`\n\n"
                f"**Valid until:** {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"📱 Use a V2Ray/Xray client to connect.\n"
                f"🔒 This connection uses REALITY protocol for enhanced security.\n\n"
                f"Use /my_subscription to check your status anytime!"
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

async def my_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check user's current subscription status."""
    user_id = update.effective_user.id
    
    try:
        # Initialize database
        init_vless_db()
        
        # Get user's subscription
        subscription = get_user_subscription(user_id)
        
        if subscription:
            expiry_date = datetime.fromisoformat(subscription['expiry_date'])
            is_expired = expiry_date < datetime.now()
            
            if is_expired:
                response = (
                    "⚠️ **Your subscription has expired!**\n\n"
                    f"**Expired on:** {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    "Send `/vless_subscribe` to get a new subscription."
                )
            else:
                response = (
                    "✅ **Your subscription is active!**\n\n"
                    f"**VLESS URI:**\n`{subscription['vless_uri']}`\n\n"
                    f"**Valid until:** {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    "🔒 Your connection is secure and ready to use!"
                )
        else:
            response = (
                "❌ **No active subscription found!**\n\n"
                "Send `/vless_subscribe` to get VLESS VPN access."
            )
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in my_subscription: {e}")
        await update.message.reply_text(
            "❌ An error occurred while checking your subscription.\n"
            "Please try again later."
        )

async def admin_remove_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command to remove a user's subscription."""
    user_id = update.effective_user.id
    
    # Check if user is admin
    if str(user_id) != ADMIN_USER_ID:
        await update.message.reply_text("❌ Access denied. Admin only.")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /admin_remove <user_id>")
        return
    
    target_user_id = context.args[0]
    user_email = f"user-{target_user_id}"
    
    try:
        # Remove from database
        remove_vless_subscription(target_user_id)
        
        # Remove from Xray configuration
        if MANAGEMENT_MODE == 'grpc':
            server_config = VLESS_SERVERS["server1"]
            remove_vless_user(server_config, target_user_id)
        else:
            remove_user_via_config(user_email)
        
        await update.message.reply_text(f"✅ User {target_user_id} subscription removed successfully.")
        
    except Exception as e:
        logger.error(f"Error removing user {target_user_id}: {e}")
        await update.message.reply_text(f"❌ Error removing user {target_user_id}: {e}")

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
    application.add_handler(CommandHandler("my_subscription", my_subscription))
    application.add_handler(CommandHandler("admin_remove", admin_remove_user))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Add unknown command handler (must be last)
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    
    # Start the bot
    logger.info(f"Starting Enhanced VLESS-only bot with {MANAGEMENT_MODE} management mode...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main() 