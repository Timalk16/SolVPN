import logging
import time
import datetime
from functools import wraps # For admin_only decorator
from enum import Enum, auto
import uuid
from datetime import datetime, timedelta
import sqlite3
import asyncio
import re

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, BotCommandScopeChat, InputFile
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ConversationHandler,
    CallbackQueryHandler, ContextTypes, filters, JobQueue
)
from telegram.error import BadRequest, Conflict

# We will need telegram.error for handling potential bad requests if we try to edit too much
import telegram 

from config import ( 
    TELEGRAM_BOT_TOKEN, DURATION_PLANS, COUNTRY_PACKAGES, ADMIN_USER_ID, OUTLINE_SERVERS,
    COMMAND_RATE_LIMIT, CALLBACK_RATE_LIMIT, MESSAGE_RATE_LIMIT, DB_PATH # Added DB_PATH
)
from database import (
    init_db, add_user_if_not_exists, create_subscription_record,
    activate_subscription, get_active_subscriptions, add_subscription_country,
    get_subscription_countries, update_subscription_country_package,
    # New DB functions for admin:
    get_all_active_subscriptions_for_admin, get_subscription_by_id, cancel_subscription_by_admin,
    get_subscription_for_admin, mark_subscription_expired
)
from outline_utils import (
    get_outline_client, create_outline_key, rename_outline_key, delete_outline_key, get_available_countries
)
from payment_utils import (
    generate_yookassa_payment_link, get_crypto_payment_details,
    verify_yookassa_payment, verify_crypto_payment, get_testnet_status,
    get_payment_status, get_yookassa_payment_details, get_yookassa_payment_status
)
from scheduler_tasks import check_expired_subscriptions

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states for user subscription
class UserConversationState(Enum):
    CHOOSE_DURATION = auto()
    CHOOSE_PAYMENT = auto()
    AWAIT_PAYMENT_CONFIRMATION = auto()
    CHOOSE_COUNTRIES = auto()

# Conversation states for admin deletion (ensure these are distinct from user states)
class AdminConversationState(Enum):
    ADMIN_LIST_SUBS = auto()
    ADMIN_CONFIRM_DELETE_SUB = auto()

ADMIN_PAGE_SIZE = 10  # Number of subscriptions per admin page

# --- Helper Functions ---
def get_duration_plan_details_text(plan_id: str) -> str:
    """Return a formatted string with duration plan details for a given plan_id."""
    plan = DURATION_PLANS[plan_id]
    return f"{plan['name']} - {plan['price_usdt']:.2f} USDT"

def build_duration_selection_keyboard() -> InlineKeyboardMarkup:
    """Build the inline keyboard for duration selection."""
    keyboard = [
        [InlineKeyboardButton(get_duration_plan_details_text(plan_id_key), callback_data=f"duration_{plan_id_key}")]
        for plan_id_key in DURATION_PLANS.keys()
    ]
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel_subscription_flow")])
    return InlineKeyboardMarkup(keyboard)

def build_payment_method_keyboard(duration_plan_id: str) -> InlineKeyboardMarkup:
    """Build the inline keyboard for payment method selection for a given duration plan."""
    plan_details = DURATION_PLANS[duration_plan_id]
    keyboard = [
        [InlineKeyboardButton(f"💰 Оплатить {plan_details['price_usdt']:.2f} USDT (криптовалюта)", callback_data="pay_crypto")],
        [InlineKeyboardButton(f"💳 Оплатить {plan_details['price_rub']:.0f} ₽ картой", callback_data="pay_card")],
        [InlineKeyboardButton("⬅️ Назад к выбору срока", callback_data="back_to_duration")],
    ]
    return InlineKeyboardMarkup(keyboard)

def build_country_selection_keyboard() -> InlineKeyboardMarkup:
    """Build the inline keyboard for country package selection."""
    keyboard = [
        [InlineKeyboardButton(f"{package['name']} - {package['description']}", callback_data=f"countries_{package_id}")]
        for package_id, package in COUNTRY_PACKAGES.items()
    ]
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel_subscription_flow")])
    return InlineKeyboardMarkup(keyboard)

# --- Rate Limiting Helper ---
def is_rate_limited(user_id: int, context: ContextTypes.DEFAULT_TYPE, limit_type: str) -> bool:
    """
    Checks if a user is rate-limited for a specific action type.
    Returns True if limited, False otherwise. Updates last action time if not limited.
    limit_type can be 'command_HANDLER_NAME', 'callback', 'message'
    """
    now = time.time()
    user_data = context.user_data # Store last action times in user_data

    # Ensure 'last_action_times' dictionary exists in user_data
    if 'last_action_times' not in user_data:
        user_data['last_action_times'] = {}

    last_action_times = user_data['last_action_times']
    
    # Determine the specific limit duration
    specific_limit_duration = None
    if limit_type.startswith("command_"):
        command_name = limit_type.split("_", 1)[1]
        specific_limit_duration = COMMAND_RATE_LIMIT.get(command_name, COMMAND_RATE_LIMIT.get("default", 3))
    elif limit_type == "callback":
        specific_limit_duration = CALLBACK_RATE_LIMIT
    elif limit_type == "message":
        specific_limit_duration = MESSAGE_RATE_LIMIT
    else: # Default case if type is unknown, apply a generic limit
        specific_limit_duration = COMMAND_RATE_LIMIT.get("default", 3)

    last_time = last_action_times.get(limit_type, 0)

    if now - last_time < specific_limit_duration:
        # User is rate-limited
        # Optionally, send a message to the user (but be careful not to spam this message either!)
        # For now, just log and return True
        logger.info(f"User {user_id} rate-limited for action type: {limit_type}. Wait {specific_limit_duration - (now - last_time):.1f}s.")
        return True
    
    # Not rate-limited, update last action time and return False
    last_action_times[limit_type] = now
    return False

# --- Rate Limiting Decorator for Command Handlers ---
def rate_limit_command(command_name: str):
    def decorator(func):
        @wraps(func) # Keep this from functools if you're using it (e.g., for admin_only)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            if update.effective_user:
                user_id = update.effective_user.id
                if is_rate_limited(user_id, context, f"command_{command_name}"):
                    # Optional: send a "please wait" message, but be cautious
                    # For instance, only send it if the last "please wait" message was long ago
                    # await update.message.reply_text("You're sending commands too quickly. Please wait a moment.", parse_mode=ParseMode.MARKDOWN_V2)
                    return # Stop processing
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator

# --- Apply Rate Limiting ---

# NO escape_markdown_v2 function as per your request


# --- Admin Check Decorator ---
def admin_only(func):
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id != ADMIN_USER_ID:
            logger.warning(f"Unauthorized access attempt to admin command by user {user_id}")
            await update.message.reply_text("Извините, эта команда только для администраторов.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapped

# --- Command Handlers (User & Admin) ---
@rate_limit_command("start")
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message with logo and Russian menu buttons."""
    user = update.effective_user
    add_user_if_not_exists(user.id, user.username, user.first_name)
    logger.info(f"[start_command] User {user.id} ({user.username or user.first_name}) started the bot.")

    # Send logo image
    with open("assets/logo.jpeg", "rb") as img:
        await update.message.reply_photo(photo=InputFile(img))

    # Get testnet status
    testnet_status = get_testnet_status()
    testnet_notice = f"\n\n⚠️ *{testnet_status} Mode*" if testnet_status == "Testnet" else ""

    # Simplified welcome message
    menu_text = (
        f"👋 Добро пожаловать, {user.first_name}!\n\n"
        "Я помогу вам получить быструю и безопасную подписку на VPN."
        f"{testnet_notice}"
    )
    if user.id == ADMIN_USER_ID:
        menu_text += (
            "\n\n*Admin Commands:*\n"
            "/admin_del_sub — Delete a user subscription."
        )
    # Escape special characters for Markdown
    menu_text = menu_text.replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace('`', '\\`')

    # Russian menu buttons
    keyboard = [
        [InlineKeyboardButton("🟢 Подписаться", callback_data="menu_subscribe")],
        [InlineKeyboardButton("📋 Мои подписки", callback_data="menu_my_subscriptions")],
        [InlineKeyboardButton("❓ Помощь", callback_data="menu_help")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(menu_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

@rate_limit_command("help")
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send help information to the user."""
    user = update.effective_user
    
    # Get testnet status
    testnet_status = get_testnet_status()
    testnet_notice = f"\n\n⚠️ *{testnet_status} Mode*" if testnet_status == "Testnet" else ""
    
    help_text = (
        "ℹ️ Как пользоваться этим ботом:\n\n"
        "1\\. Используйте /subscribe, чтобы увидеть доступные тарифы VPN\\.\n"
        "2\\. Выберите тариф и способ оплаты\\.\n"
        "3\\. Следуйте инструкциям для завершения оплаты\\.\n"
        "4\\. После подтверждения оплаты вы получите ключ доступа к VPN\\.\n\n"
        "Используйте /my\\_subscriptions для проверки вашего текущего доступа\\.\n"
        "Если у вас возникли проблемы, обратитесь в поддержку: @SolSuprt или воспользуйтесь командой /support\\."
        f"{testnet_notice}"
    )
    if user.id == ADMIN_USER_ID:
        help_text += (
            "\n\nAdmin Commands:\n"
            "/admin\\_del\\_sub \\- Delete a user subscription\\."
        )
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN_V2)

@rate_limit_command("subscribe")
async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    logger.info(f"User {user.id} initiated /subscribe.")
    reply_markup = build_duration_selection_keyboard()
    await update.message.reply_text("Пожалуйста, выберите срок подписки:", reply_markup=reply_markup)
    return UserConversationState.CHOOSE_DURATION.value

@rate_limit_command("my_subscriptions")
async def my_subscriptions_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the user their active subscriptions."""
    # TODO: While users can create new subscriptions, a direct "renew" option for an existing subscription would be more convenient.
    user_id = update.effective_user.id
    active_subs = get_active_subscriptions(user_id)
    if not active_subs:
        await update.message.reply_text("У вас нет активных подписок. Используйте /subscribe, чтобы приобрести одну!")
        return

    message = "Ваши активные подписки на VPN:\n\n"
    keyboard = []
    
    for sub_id, duration_plan_id, country_package_id, end_date_str, status, countries, access_urls in active_subs:
        duration_plan_name = DURATION_PLANS.get(duration_plan_id, {}).get("name", "Неизвестный срок")
        country_package_name = COUNTRY_PACKAGES.get(country_package_id, {}).get("name", "Неизвестный пакет")
        end_date = datetime.fromisoformat(end_date_str).strftime('%Y-%m-%d %H:%M UTC')
        
        # Parse countries and access URLs
        country_list = countries.split(',') if countries else []
        access_url_list = access_urls.split(',') if access_urls else []
        
        message += f"**Срок:** {duration_plan_name}\n"
        message += f"**Пакет:** {country_package_name}\n"
        message += f"**Истекает:** {end_date}\n\n"
        
        # Add VPN keys for each country
        for i, country in enumerate(country_list):
            if i < len(access_url_list):
                country_name = OUTLINE_SERVERS.get(country, {}).get('name', country.title())
                country_flag = OUTLINE_SERVERS.get(country, {}).get('flag', '🌍')
                message += f"{country_flag} **{country_name}:** `{access_url_list[i]}`\n"
        
        message += "\n"
        
        # Add renew button for each subscription
        keyboard.append([InlineKeyboardButton(f"🔄 Продлить {duration_plan_name}", callback_data=f"renew_{sub_id}")])
    
    message += "Вы можете скопировать ключи доступа и импортировать их в свой клиент Outline."
    await update.message.reply_text(
        message, 
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# --- User Subscription Conversation Handlers ---
async def duration_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    duration_id = query.data[len("duration_"):]
    context.user_data['selected_duration'] = duration_id
    
    logger.info(f"User {update.effective_user.id} selected duration: {duration_id}")

    plan_details = DURATION_PLANS[duration_id]
    text = (
        f"Вы выбрали: {plan_details['name']}\n"
        f"Цена: {plan_details['price_usdt']:.2f} USDT.\n\n"
        "Пожалуйста, выберите способ оплаты:"
    )
    reply_markup = build_payment_method_keyboard(duration_id)
    await query.edit_message_text(text=text, reply_markup=reply_markup)
    return UserConversationState.CHOOSE_PAYMENT.value

async def payment_method_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the payment method selection."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "back_to_duration":
        await query.edit_message_text(
            "Пожалуйста, выберите срок подписки:",
            reply_markup=build_duration_selection_keyboard()
        )
        return UserConversationState.CHOOSE_DURATION.value
    
    duration_id = context.user_data.get('selected_duration')
    if not duration_id:
        await query.edit_message_text("Ошибка: Срок не выбран. Пожалуйста, начните сначала с /subscribe")
        return ConversationHandler.END
    
    plan = DURATION_PLANS[duration_id]
    
    if query.data == "pay_crypto":
        try:
            # Generate crypto payment details
            instructions, invoice_id = await get_crypto_payment_details(
                plan['price_usdt'],
                plan['name']
            )
            
            context.user_data['payment_id'] = invoice_id
            context.user_data['payment_type'] = 'crypto'
            
            keyboard = [
                [InlineKeyboardButton("✅ Я оплатил", callback_data="confirm_payment")],
                [InlineKeyboardButton("❌ Отмена", callback_data="cancel_subscription_flow")]
            ]
            
            await query.edit_message_text(
                instructions,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error creating crypto payment: {e}")
            await query.edit_message_text(
                "Извините, произошла ошибка при создании платежа. Пожалуйста, попробуйте позже.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Назад к выбору срока", callback_data="back_to_duration")
                ]])
            )
            return UserConversationState.CHOOSE_DURATION.value
    
    elif query.data == "pay_card":
        try:
            # Generate Youkassa payment details
            instructions, payment_id = await get_yookassa_payment_details(
                plan['price_rub'],
                plan['name']
            )
            
            context.user_data['payment_id'] = payment_id
            context.user_data['payment_type'] = 'card'
            
            keyboard = [
                [InlineKeyboardButton("✅ Я оплатил", callback_data="confirm_payment")],
                [InlineKeyboardButton("❌ Отмена", callback_data="cancel_subscription_flow")]
            ]
            
            await query.edit_message_text(
                instructions,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error creating card payment: {e}")
            
            # Check if it's a configuration error
            if "Youkassa is not configured" in str(e):
                error_message = (
                    "💳 Оплата картой временно недоступна.\n\n"
                    "Пожалуйста, используйте оплату криптовалютой или обратитесь к администратору."
                )
            elif "network" in str(e).lower() or "timeout" in str(e).lower() or "connection" in str(e).lower():
                error_message = (
                    "💳 Ошибка сети при создании платежа.\n\n"
                    "Пожалуйста, попробуйте еще раз через несколько минут или используйте оплату криптовалютой."
                )
            else:
                error_message = "Извините, произошла ошибка при создании платежа. Пожалуйста, попробуйте позже."
            
            await query.edit_message_text(
                error_message,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Назад к выбору срока", callback_data="back_to_duration")
                ]])
            )
            return UserConversationState.CHOOSE_DURATION.value
    
    return UserConversationState.AWAIT_PAYMENT_CONFIRMATION.value

async def confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle payment confirmation."""
    query = update.callback_query
    await query.answer()
    
    payment_id = context.user_data.get('payment_id')
    payment_type = context.user_data.get('payment_type')
    
    if not payment_id or not payment_type:
        await query.edit_message_text(
            "❌ Ошибка: Платежная информация не найдена. Пожалуйста, начните сначала с /subscribe",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Назад в меню", callback_data="back_to_menu")
            ]])
        )
        return ConversationHandler.END
    
    try:
        # First check payment status
        if payment_type == 'crypto':
            status = await get_payment_status(payment_id)
            logger.info(f"Crypto payment status check result: {status}")
        else:  # card payment
            status = await get_yookassa_payment_status(payment_id)
            logger.info(f"Card payment status check result: {status}")
        
        if status == "paid" or status == "succeeded":
            # Verify the payment
            if payment_type == 'crypto':
                is_verified = await verify_crypto_payment(payment_id)
                logger.info(f"Crypto payment verification result: {is_verified}")
            else:  # card payment
                is_verified = await verify_yookassa_payment(payment_id)
                logger.info(f"Card payment verification result: {is_verified}")
            
            if is_verified:
                # Create subscription
                user_id = update.effective_user.id
                duration_id = context.user_data.get('selected_duration')
                plan = DURATION_PLANS[duration_id]
                
                # Check if this is a renewal
                renewing_sub_id = context.user_data.get('renewing_sub_id')
                
                if renewing_sub_id:
                    # This is a renewal - get existing subscription to find current end_date
                    existing_sub = get_subscription_by_id(renewing_sub_id)
                    if not existing_sub:
                        await query.edit_message_text("Ошибка: Не удалось найти подписку для продления.")
                        return ConversationHandler.END

                    # 0:id, 1:user_id, 2:duration_plan_id, 3:country_package_id, 4:start_date, 5:end_date
                    current_end_date = datetime.fromisoformat(existing_sub[5])
                    
                    # Calculate new end date by adding duration to the *current* end date
                    new_end_date = current_end_date + timedelta(days=plan['duration_days'])

                    # Update existing subscription
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE subscriptions
                        SET end_date = ?, status = 'active', payment_id = ?
                        WHERE id = ? AND user_id = ?
                    ''', (new_end_date, payment_id, renewing_sub_id, user_id))
                    conn.commit()
                    conn.close()
                    
                    success_message = (
                        f"✅ Оплата прошла успешно! Ваша подписка была продлена.\n\n"
                        f"План: {plan['name']}\n"
                        f"Новая дата окончания: {new_end_date.strftime('%Y-%m-%d %H:%M')}\n\n"
                        f"Используйте /my_subscriptions, чтобы проверить статус вашей подписки."
                    )
                    
                    await query.edit_message_text(
                        success_message,
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("⬅️ Назад в меню", callback_data="back_to_menu")
                        ]])
                    )
                    return ConversationHandler.END
                else:
                    # This is a new subscription - create pending subscription
                    subscription_id = create_subscription_record(
                        user_id=user_id,
                        duration_plan_id=duration_id,
                        duration_days=plan['duration_days']
                    )
                    
                    # Store subscription ID for country selection
                    context.user_data['pending_subscription_id'] = subscription_id
                    context.user_data['payment_id'] = payment_id
                    
                    # Move to country selection
                    price_text = f"{plan['price_usdt']:.2f} USDT" if payment_type == 'crypto' else f"{plan['price_rub']:.0f} ₽"
                    text = (
                        f"✅ Оплата прошла успешно!\n\n"
                        f"Срок: {plan['name']}\n"
                        f"Цена: {price_text}\n\n"
                        f"Теперь выберите пакет стран:"
                    )
                    reply_markup = build_country_selection_keyboard()
                    await query.edit_message_text(text=text, reply_markup=reply_markup)
                    return UserConversationState.CHOOSE_COUNTRIES.value
            else:
                await query.edit_message_text(
                    "❌ Проверка платежа не удалась. Пожалуйста, попробуйте еще раз или обратитесь в поддержку.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔄 Проверить еще раз", callback_data="confirm_payment"),
                        InlineKeyboardButton("❌ Отмена", callback_data="cancel_subscription_flow")
                    ]])
                )
                return UserConversationState.AWAIT_PAYMENT_CONFIRMATION.value
        elif status == "not_found":
            await query.edit_message_text(
                "❌ Платеж не найден. Убедитесь, что вы отправили платеж, и попробуйте снова.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔄 Проверить еще раз", callback_data="confirm_payment"),
                    InlineKeyboardButton("❌ Отмена", callback_data="cancel_subscription_flow")
                ]])
            )
            return UserConversationState.AWAIT_PAYMENT_CONFIRMATION.value
    except Exception as e:
        logger.error(f"Error processing payment: {e}")
        await query.edit_message_text(
            "❌ Произошла ошибка при обработке вашего платежа. Пожалуйста, попробуйте еще раз или обратитесь в поддержку.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔄 Попробовать еще раз", callback_data="confirm_payment"),
                InlineKeyboardButton("❌ Отмена", callback_data="cancel_subscription_flow")
            ]])
        )
        return UserConversationState.AWAIT_PAYMENT_CONFIRMATION.value

async def countries_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle country package selection and activate subscription."""
    query = update.callback_query
    await query.answer()
    
    country_package_id = query.data[len("countries_"):]
    subscription_id = context.user_data.get('pending_subscription_id')
    payment_id = context.user_data.get('payment_id')
    duration_id = context.user_data.get('selected_duration')
    
    if not subscription_id or not payment_id or not duration_id:
        await query.edit_message_text(
            "❌ Ошибка: Отсутствует информация о подписке. Пожалуйста, начните сначала с /subscribe",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Назад в меню", callback_data="back_to_menu")
            ]])
        )
        return ConversationHandler.END
    
    try:
        # Get package details
        package = COUNTRY_PACKAGES[country_package_id]
        duration_plan = DURATION_PLANS[duration_id]
        
        # Update subscription with country package
        update_subscription_country_package(subscription_id, country_package_id)
        
        # Create Outline keys for each country in the package
        countries = package.get('countries', [])
        created_keys = []
        
        for country in countries:
            try:
                # Get Outline client for this country
                outline_client = get_outline_client(country)
                if not outline_client:
                    logger.error(f"Failed to get Outline client for country: {country}")
                    continue
                
                # Create VPN key for this country
                outline_key_id, outline_access_url = create_outline_key(outline_client)
                
                if outline_key_id and outline_access_url:
                    # Add country to subscription
                    add_subscription_country(
                        subscription_id=subscription_id,
                        country_code=country,
                        outline_key_id=outline_key_id,
                        outline_access_url=outline_access_url
                    )
                    created_keys.append(country)
                    
                    # Rename the key for better identification
                    user_name = update.effective_user.first_name or update.effective_user.username or f"user_{update.effective_user.id}"
                    key_name = f"{user_name}_{country}_{subscription_id}"
                    rename_outline_key(outline_client, outline_key_id, key_name)
                    
                    logger.info(f"Created VPN key for {country}: {outline_key_id}")
                else:
                    logger.error(f"Failed to create Outline key for country: {country}")
                    
            except Exception as e:
                logger.error(f"Error creating VPN key for {country}: {e}")
        
        if not created_keys:
            raise Exception("Failed to create any VPN keys")
        
        # Activate the subscription
        activate_subscription(
            subscription_db_id=subscription_id,
            duration_days=duration_plan['duration_days'],
            payment_id=payment_id
        )
        
        countries_text = ", ".join([f"{OUTLINE_SERVERS[country]['flag']} {OUTLINE_SERVERS[country]['name']}" 
                                  for country in created_keys])
        
        success_message = (
            f"🎉 Ваша VPN подписка теперь активна!\n\n"
            f"Срок: {duration_plan['name']}\n"
            f"Пакет: {package['name']}\n"
            f"Страны: {countries_text}\n"
            f"Истекает: {(datetime.now() + timedelta(days=duration_plan['duration_days'])).strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"Используйте /my_subscriptions, чтобы получить ваши ключи доступа к VPN."
        )
        
        await query.edit_message_text(
            success_message,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Назад в меню", callback_data="back_to_menu")
            ]])
        )
        
        # Clear user data
        context.user_data.clear()
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error activating subscription: {e}")
        await query.edit_message_text(
            "❌ Произошла ошибка при активации вашей подписки. Пожалуйста, обратитесь в поддержку.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Назад в меню", callback_data="back_to_menu")
            ]])
        )
        return ConversationHandler.END

async def back_to_duration_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    reply_markup = build_duration_selection_keyboard()
    await query.edit_message_text("Пожалуйста, выберите срок подписки:", reply_markup=reply_markup)
    return UserConversationState.CHOOSE_DURATION.value

async def back_to_payment_choice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    duration_id = context.user_data['selected_duration']
    plan_details = DURATION_PLANS[duration_id]
    text = (
        f"Вы выбрали: {plan_details['name']}\n"
        f"Цена: {plan_details['price_usdt']:.2f} USDT.\n\n"
        "Пожалуйста, выберите способ оплаты:"
    )
    reply_markup = build_payment_method_keyboard(duration_id)
    await query.edit_message_text(text=text, reply_markup=reply_markup)
    return UserConversationState.CHOOSE_PAYMENT.value

async def cancel_subscription_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    message_to_send = "Процесс подписки отменен. Используйте /subscribe, чтобы начать сначала."
    if query:
        await query.answer()
        try:
            await query.edit_message_text(message_to_send) # No parse_mode
        except telegram.error.BadRequest:
            if update.effective_message:
                 await update.effective_message.reply_text(message_to_send) # No parse_mode
    elif update.message: # If called by /cancel command
        await update.message.reply_text(message_to_send) # No parse_mode
    context.user_data.clear()
    return ConversationHandler.END

# --- Admin Subscription Deletion Flow ---
@admin_only
@rate_limit_command("admin_del_sub")
async def admin_delete_subscription_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the admin subscription deletion flow, showing a paginated list of subscriptions."""
    subscriptions = get_all_active_subscriptions_for_admin()
    if not subscriptions:
        await update.message.reply_text("No subscriptions found to delete.")
        return ConversationHandler.END

    text_parts = ["Select a subscription to delete by clicking its button, or type the Subscription DB ID:\n"]
    keyboard = []
    
    current_page = context.user_data.get('admin_delete_page', 0)
    start_index = current_page * ADMIN_PAGE_SIZE
    end_index = start_index + ADMIN_PAGE_SIZE
    subs_to_display = subscriptions[start_index:end_index]

    for sub_id, user_id, username, first_name, duration_plan_id, country_package_id, end_date_str, status, countries in subs_to_display:
        user_display = username or first_name or f"User {user_id}"
        plan_name = DURATION_PLANS.get(duration_plan_id, {}).get("name", "Unknown")
        end_date_short = end_date_str[:10] if end_date_str else "N/A"
        
        btn_text = f"ID:{sub_id} U:{user_display[:10]} P:{plan_name[:7]} S:{status[:6]}"
        if len(btn_text) > 60 : btn_text = btn_text[:57] + "..."
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"admin_del_{sub_id}")])

    page_nav_buttons = []
    if current_page > 0:
        page_nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data="admin_del_page_prev"))
    if end_index < len(subscriptions):
        page_nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data="admin_del_page_next"))
    
    if page_nav_buttons:
        keyboard.append(page_nav_buttons)

    keyboard.append([InlineKeyboardButton("❌ Cancel Deletion", callback_data="admin_cancel_delete")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = "".join(text_parts)
    if update.callback_query and update.callback_query.data.startswith("admin_del_page_"):
        try:
            await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup) # No parse_mode
        except telegram.error.BadRequest as e: # If message is identical or other issue
             logger.warning(f"Admin pagination edit failed: {e}") # Log and proceed (list might not update visually)
    else:
        await update.message.reply_text(message_text, reply_markup=reply_markup) # No parse_mode
    
    return AdminConversationState.ADMIN_LIST_SUBS.value

async def admin_paginate_subs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    action = query.data
    
    current_page = context.user_data.get('admin_delete_page', 0)
    if action == "admin_del_page_prev":
        context.user_data['admin_delete_page'] = max(0, current_page - 1)
    elif action == "admin_del_page_next":
        context.user_data['admin_delete_page'] = current_page + 1
        
    return await admin_delete_subscription_start(update, context)

async def admin_sub_chosen_for_deletion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle admin selection of subscription for deletion."""
    query = update.callback_query
    message = update.message
    
    if query:
        await query.answer()
        sub_db_id_to_delete = int(query.data.split('_')[2])  # admin_del_123 -> 123
    elif message:
        try:
            sub_db_id_to_delete = int(message.text.strip())
        except ValueError:
            await message.reply_text("Please enter a valid subscription ID (number).") # No parse_mode
            return AdminConversationState.ADMIN_LIST_SUBS.value
    else:
        return AdminConversationState.ADMIN_LIST_SUBS.value

    # Get subscription details using the admin-specific function
    subscription = get_subscription_for_admin(sub_db_id_to_delete)
    
    if not subscription:
        msg = f"Subscription with DB ID {sub_db_id_to_delete} not found." # No parse_mode
        target_message_obj = query.message if query else update.message
        await target_message_obj.reply_text(msg) # No parse_mode
        return AdminConversationState.ADMIN_LIST_SUBS.value

    context.user_data['sub_to_delete_id'] = sub_db_id_to_delete
    context.user_data['sub_to_delete_details'] = subscription

    s_id, s_user_id, s_status, s_key_ids, s_countries = subscription
    
    countries_str = s_countries or "N/A"
    key_ids_str = s_key_ids or "N/A"

    text = (
        f"Are you sure you want to delete this subscription?\n"
        f"DB ID: {s_id}\n"
        f"User ID: {s_user_id}\n"
        f"Status: {s_status}\n"
        f"Countries: {countries_str}\n"
        f"Outline Key IDs: {key_ids_str}\n\n"
        "This will delete all related Outline keys and mark the subscription as cancelled."
    )
    keyboard = [
        [InlineKeyboardButton(f"🗑️ Yes, Delete Sub ID {s_id}", callback_data="admin_confirm_delete_yes")],
        [InlineKeyboardButton("🚫 No, Keep It", callback_data="admin_confirm_delete_no")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    target_message_obj = query.message if query else update.message
    await target_message_obj.reply_text(text, reply_markup=reply_markup) # No parse_mode
    return AdminConversationState.ADMIN_CONFIRM_DELETE_SUB.value

async def admin_confirm_delete_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    choice = query.data

    if choice == "admin_confirm_delete_yes":
        sub_db_id = context.user_data.get('sub_to_delete_id')
        sub_details = context.user_data.get('sub_to_delete_details')

        if not sub_db_id or not sub_details:
            await query.edit_message_text("Error: Subscription details not found. Start over with /admin_del_sub.")
            context.user_data.clear()
            return ConversationHandler.END

        s_id, s_user_id, current_status, s_key_ids, s_countries = sub_details
        
        all_keys_deleted = True
        
        # Check if there are keys and countries to delete
        if s_key_ids and s_countries:
            key_ids = s_key_ids.split(',')
            countries = s_countries.split(',')
            
            if len(key_ids) != len(countries):
                logger.error(f"Admin Delete: Mismatch between key count ({len(key_ids)}) and country count ({len(countries)}) for sub {sub_db_id}.")
                all_keys_deleted = False
            else:
                for i, key_id in enumerate(key_ids):
                    country = countries[i]
                    try:
                        outline_client = get_outline_client(country)
                        if outline_client:
                            if delete_outline_key(outline_client, str(key_id)):
                                logger.info(f"Admin {update.effective_user.id} deleted Outline key {key_id} from {country}.")
                            else:
                                logger.error(f"Admin {update.effective_user.id} FAILED to delete Outline key {key_id} from {country}.")
                                all_keys_deleted = False
                        else:
                            logger.error(f"Admin {update.effective_user.id}: No Outline client for {country}. Key {key_id} not deleted.")
                            all_keys_deleted = False
                    except Exception as e:
                        logger.error(f"Admin {update.effective_user.id}: Exception deleting key {key_id} from {country}: {e}")
                        all_keys_deleted = False
        else:
            logger.info(f"Admin {update.effective_user.id}: No Outline keys found for sub {sub_db_id} to delete.")

        # Update DB regardless of key deletion status
        db_updated = cancel_subscription_by_admin(sub_db_id)
        
        if all_keys_deleted and db_updated:
            await query.edit_message_text(f"✅ Subscription DB ID {sub_db_id} cancelled. All Outline keys deleted.", parse_mode=None)
        elif db_updated:
            await query.edit_message_text(f"⚠️ Subscription DB ID {sub_db_id} cancelled in DB, but there was an issue deleting one or more Outline keys. Check logs.", parse_mode=None)
        else:
            await query.edit_message_text(f"❌ Failed to process for sub DB ID {sub_db_id}. Check logs.", parse_mode=None)
    else:
        await query.edit_message_text("Deletion cancelled. Subscription remains.", parse_mode=None)

    context.user_data.pop('sub_to_delete_id', None)
    context.user_data.pop('sub_to_delete_details', None)
    context.user_data.pop('admin_delete_page', None)
    return ConversationHandler.END

async def admin_cancel_delete_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle admin cancellation of delete flow."""
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "❌ Subscription deletion cancelled.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Back to Admin", callback_data="admin_menu")
            ]])
        )
    else:
        await update.message.reply_text("❌ Subscription deletion cancelled.")
    return ConversationHandler.END

async def admin_delete_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle admin deletion of subscription."""
    query = update.callback_query
    await query.answer()
    
    sub_id = int(query.data.split('_')[2])  # admin_del_123 -> 123
    
    # Get subscription details
    subscription = get_subscription_for_admin(sub_id)
    if not subscription:
        await query.edit_message_text(
            "❌ Error: Subscription not found.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Back to Admin", callback_data="admin_menu")
            ]])
        )
        return ConversationHandler.END
    
    user_id = subscription[1]
    key_ids = subscription[3].split(',') if subscription[3] else []
    countries = subscription[4].split(',') if subscription[4] else []
    
    # Delete Outline keys for each country
    deleted_keys = []
    failed_keys = []
    
    for i, country in enumerate(countries):
        if i < len(key_ids) and key_ids[i]:
            try:
                outline_client = get_outline_client(country)
                if outline_client:
                    deleted = delete_outline_key(outline_client, key_ids[i])
                    if deleted:
                        deleted_keys.append(f"{country} ({key_ids[i]})")
                    else:
                        failed_keys.append(f"{country} ({key_ids[i]})")
                else:
                    failed_keys.append(f"{country} (no client)")
            except Exception as e:
                logger.error(f"Error deleting key {key_ids[i]} for {country}: {e}")
                failed_keys.append(f"{country} (error)")
    
    # Cancel the subscription in database
    db_updated = cancel_subscription_by_admin(sub_id)
    
    # Prepare result message
    if deleted_keys and db_updated:
        result_message = f"✅ Subscription {sub_id} cancelled. Deleted keys: {', '.join(deleted_keys)}"
        if failed_keys:
            result_message += f"\n⚠️ Failed to delete: {', '.join(failed_keys)}"
    elif db_updated:
        result_message = f"⚠️ Subscription {sub_id} cancelled in DB. Failed to delete keys: {', '.join(failed_keys)}"
    else:
        result_message = f"❌ Failed to cancel subscription {sub_id}"
    
    await query.edit_message_text(
        result_message,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("⬅️ Back to Admin", callback_data="admin_menu")
        ]])
    )
    
    return ConversationHandler.END

async def back_to_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the back to menu button press."""
    query = update.callback_query
    await query.answer()
    
    # Clear any conversation data
    context.user_data.clear()
    
    # Send the main menu message
    await query.edit_message_text(
        "Добро пожаловать в VPN Бот! 🚀\n\n"
        "Доступные команды:\n"
        "/subscribe - Подписаться на услугу VPN\n"
        "/my_subscriptions - Проверить ваши активные подписки\n"
        "/help - Получить помощь и поддержку\n"
        "/start - Показать это меню"
    )
    return ConversationHandler.END

# --- Main Menu Button Handlers ---
async def menu_subscribe_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    # Simulate /subscribe command for callback context
    user = query.from_user
    chat_id = query.message.chat_id
    
    logger.info(f"User {user.id} started subscription flow from menu button")
    
    reply_markup = build_duration_selection_keyboard()
    await context.bot.send_message(chat_id=chat_id, text="Пожалуйста, выберите срок подписки:", reply_markup=reply_markup)
    return UserConversationState.CHOOSE_DURATION.value

async def menu_my_subscriptions_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    # Simulate /my_subscriptions command for callback context
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    active_subs = get_active_subscriptions(user_id)
    if not active_subs:
        await context.bot.send_message(chat_id=chat_id, text="У вас нет активных подписок. Используйте /subscribe, чтобы приобрести одну!")
        return
    message = "Ваши активные подписки на VPN:\n\n"
    keyboard = []
    for sub_id, duration_plan_id, country_package_id, end_date_str, status, countries, access_urls in active_subs:
        duration_plan_name = DURATION_PLANS.get(duration_plan_id, {}).get("name", "Неизвестный срок")
        country_package_name = COUNTRY_PACKAGES.get(country_package_id, {}).get("name", "Неизвестный пакет")
        end_date = datetime.fromisoformat(end_date_str).strftime('%Y-%m-%d %H:%M UTC')
        country_list = countries.split(',') if countries else []
        access_url_list = access_urls.split(',') if access_urls else []
        message += f"**Срок:** {duration_plan_name}\n"
        message += f"**Пакет:** {country_package_name}\n"
        message += f"**Истекает:** {end_date}\n\n"
        for i, country in enumerate(country_list):
            if i < len(access_url_list):
                country_name = OUTLINE_SERVERS.get(country, {}).get('name', country.title())
                country_flag = OUTLINE_SERVERS.get(country, {}).get('flag', '🌍')
                message += f"{country_flag} **{country_name}:** `{access_url_list[i]}`\n"
        message += "\n"
        keyboard.append([InlineKeyboardButton(f"🔄 Продлить {duration_plan_name}", callback_data=f"renew_{sub_id}")])
    message += "Вы можете скопировать ключи доступа и импортировать их в свой клиент Outline."
    await context.bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def menu_help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user = query.from_user
    chat_id = query.message.chat_id
    testnet_status = get_testnet_status()
    testnet_notice = f"\n\n⚠️ *{testnet_status} Mode*" if testnet_status == "Testnet" else ""
    help_text = (
        "ℹ️ Как пользоваться этим ботом:\n\n"
        "1\\. Используйте /subscribe, чтобы увидеть доступные тарифы VPN\\.\n"
        "2\\. Выберите тариф и способ оплаты\\.\n"
        "3\\. Следуйте инструкциям для завершения оплаты\\.\n"
        "4\\. После подтверждения оплаты вы получите ключ доступа к VPN\\.\n\n"
        "Используйте /my\\_subscriptions для проверки вашего текущего доступа\\.\n"
        "Если у вас возникли проблемы, обратитесь в поддержку: @SolSuprt или воспользуйтесь командой /support\\."
        f"{testnet_notice}"
    )
    if user.id == ADMIN_USER_ID:
        help_text += ("\n\nAdmin Commands:\n/admin\\_del\\_sub \\- Delete a user subscription\\.")
    await context.bot.send_message(chat_id=chat_id, text=help_text, parse_mode=ParseMode.MARKDOWN_V2)

@rate_limit_command("support")
async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message with a link or mention to the support account @SolSuprt."""
    support_text = (
        "Связаться с поддержкой можно по аккаунту: @SolSuprt\n"
        "Нажмите на ник или перейдите по ссылке: https://t.me/SolSuprt"
    )
    await update.message.reply_text(support_text)

# --- Fallback and Error Handlers ---
async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Извините, я не понял эту команду. Попробуйте /help.") # No parse_mode

def send_error_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str) -> None:
    """Utility to send an error message to a user, logs on failure."""
    try:
        asyncio.create_task(context.bot.send_message(chat_id=chat_id, text=text))
    except Exception as e:
        logger.error(f"Error sending error message to user: {e}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Global error handler for uncaught exceptions in handlers."""
    error = context.error
    
    # Handle specific conflict error for multiple bot instances
    if isinstance(error, Conflict):
        logger.error("Multiple bot instances detected! Please ensure only one instance is running.")
        logger.error("This usually happens when:")
        logger.error("1. Multiple deployments are running simultaneously")
        logger.error("2. Local development bot is running while production is also running")
        logger.error("3. Render/Railway is restarting the service multiple times")
        return
    
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    if isinstance(update, Update) and update.effective_chat:
        send_error_message(context, update.effective_chat.id, "Произошла непредвиденная ошибка. Пожалуйста, попробуйте еще раз или обратитесь в поддержку.")

async def post_init(application: Application) -> None:
    """Post-initialization function to set bot commands."""
    user_commands = [
        BotCommand("start", "Главное меню"),
        BotCommand("subscribe", "Покупка/продление доступа"),
        BotCommand("my_subscriptions", "Мои подписки"),
        BotCommand("help", "Помощь"),
    ]
    await application.bot.set_my_commands(user_commands)
    logger.info("Set user commands.")

    admin_commands = user_commands + [
        BotCommand("admin_del_sub", "Удалить подписку"),
    ]
    try:
        await application.bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=ADMIN_USER_ID))
        logger.info(f"Set admin commands for admin {ADMIN_USER_ID}.")
    except Exception as e:
        logger.error(f"Could not set admin commands for admin {ADMIN_USER_ID}: {e}")

async def log_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Received message: {update.message.text if update.message else 'No text'} from user {update.effective_user.id if update.effective_user else 'Unknown'}")

# --- Main Function ---
async def main() -> None:
    """Entry point for the bot: initializes the database, sets up handlers, and starts polling."""
    init_db()
    logger.info("Database initialized.")

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).job_queue(JobQueue()).post_init(post_init).build()

    job_queue = application.job_queue
    job_queue.run_repeating(check_expired_subscriptions, interval=60, first=10, name="expiry_check_short_interval")
    logger.info("Scheduled job for checking expired subscriptions.")

    # Add conversation handler for user subscription flow
    user_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("subscribe", subscribe_command),
            CallbackQueryHandler(handle_renewal, pattern=r"^renew_\d+$"),
            CallbackQueryHandler(menu_subscribe_handler, pattern="^menu_subscribe$")
        ],
        states={
            UserConversationState.CHOOSE_DURATION.value: [
                CallbackQueryHandler(duration_chosen, pattern=r"^duration_"),
                CallbackQueryHandler(cancel_subscription_flow, pattern="^cancel_subscription_flow$")
            ],
            UserConversationState.CHOOSE_PAYMENT.value: [
                CallbackQueryHandler(payment_method_chosen, pattern=r"^pay_"),
                CallbackQueryHandler(back_to_duration_handler, pattern="^back_to_duration$"),
                CallbackQueryHandler(cancel_subscription_flow, pattern="^cancel_subscription_flow$") # User cancel
            ],
            UserConversationState.AWAIT_PAYMENT_CONFIRMATION.value: [
                CallbackQueryHandler(confirm_payment, pattern="^confirm_payment$"),
                CallbackQueryHandler(cancel_subscription_flow, pattern="^cancel_subscription_flow$")
            ],
            UserConversationState.CHOOSE_COUNTRIES.value: [
                CallbackQueryHandler(countries_chosen, pattern=r"^countries_"),
                CallbackQueryHandler(cancel_subscription_flow, pattern="^cancel_subscription_flow$")
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel_subscription_flow)],
        per_user=True,
        per_chat=True,
        allow_reentry=True
    )

    admin_del_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("admin_del_sub", admin_delete_subscription_start)],
        states={
            AdminConversationState.ADMIN_LIST_SUBS.value: [
                CallbackQueryHandler(admin_paginate_subs, pattern="^admin_del_page_"),
                CallbackQueryHandler(admin_sub_chosen_for_deletion, pattern=r"^admin_del_\d+$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_sub_chosen_for_deletion),
                CallbackQueryHandler(admin_cancel_delete_flow, pattern="^admin_cancel_delete$") # Admin cancel button
            ],
            AdminConversationState.ADMIN_CONFIRM_DELETE_SUB.value: [
                CallbackQueryHandler(admin_confirm_delete_action, pattern="^admin_confirm_delete_"),
                CallbackQueryHandler(admin_cancel_delete_flow, pattern="^admin_cancel_delete$") # Admin cancel button
            ]
        },
        fallbacks=[
            CommandHandler("cancel", admin_cancel_delete_flow), # Admin flow cancel command
            CallbackQueryHandler(admin_cancel_delete_flow, pattern="^admin_cancel_delete$") # Admin flow cancel button
        ],
        per_user=True, 
        per_chat=True,
        name="admin_delete_conversation",
    )

    application.add_handler(user_conv_handler)
    application.add_handler(admin_del_conv_handler)

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("my_subscriptions", my_subscriptions_command))
    application.add_handler(CommandHandler("support", support_command))
    
    # Add handlers for buttons outside conversation flow
    application.add_handler(CallbackQueryHandler(back_to_menu_handler, pattern="^back_to_menu$"))
    application.add_handler(CallbackQueryHandler(handle_cancel_expired, pattern=r"^cancel_expired_\d+$"))
    
    application.add_handler(CallbackQueryHandler(menu_my_subscriptions_handler, pattern="^menu_my_subscriptions$"))
    application.add_handler(CallbackQueryHandler(menu_help_handler, pattern="^menu_help$"))
    
    # Add debug handler to log all incoming messages
    application.add_handler(MessageHandler(filters.ALL, log_all_messages))
    
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    application.add_error_handler(error_handler)

    logger.info("Deleting any existing webhook configuration...")
    await application.bot.delete_webhook()

    logger.info("Starting bot polling...")
    try:
        # Use a more explicit polling approach with better error handling
        await application.initialize()
        await application.start()
        await application.updater.start_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
        
        # Keep the bot running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
                
    except Exception as e:
        logger.error(f"Critical error during polling: {e}")
        raise
    finally:
        try:
            await application.stop()
            await application.shutdown()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

async def handle_renewal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle subscription renewal request."""
    query = update.callback_query
    await query.answer()
    
    sub_id = int(query.data.split('_')[1])
    user_id = update.effective_user.id
    
    # Get subscription details
    subscription = get_subscription_by_id(sub_id)
    
    if not subscription or subscription[1] != user_id:
        await query.edit_message_text(
            "❌ Error: Subscription not found or you don't have permission to renew it.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_menu")
            ]])
        )
        return ConversationHandler.END
    
    # Store the subscription ID for later use
    context.user_data['renewing_sub_id'] = sub_id
    
    text = "Пожалуйста, выберите срок для продления подписки:"
    reply_markup = build_duration_selection_keyboard()
    await query.edit_message_text(text=text, reply_markup=reply_markup)
    return UserConversationState.CHOOSE_DURATION.value

async def handle_cancel_expired(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle cancellation of expired subscription."""
    query = update.callback_query
    await query.answer()
    
    sub_id = int(query.data.split('_')[2])  # cancel_expired_123 -> 123
    user_id = update.effective_user.id
    
    # Get subscription details
    subscription = get_subscription_for_admin(sub_id)
    if not subscription or subscription[1] != user_id:  # user_id is the 2nd column
        await query.edit_message_text(
            "❌ Error: Subscription not found or you don't have permission to cancel it.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_menu")
            ]])
        )
        return ConversationHandler.END
    
    # Get key IDs and countries
    key_ids = subscription[3].split(',') if subscription[3] else []
    countries = subscription[4].split(',') if subscription[4] else []
    
    # Delete Outline keys for each country
    deleted_count = 0
    total_keys = len(key_ids)
    
    for i, country in enumerate(countries):
        if i < len(key_ids) and key_ids[i]:
            try:
                outline_client = get_outline_client(country)
                if outline_client:
                    deleted = delete_outline_key(outline_client, key_ids[i])
                    if deleted:
                        deleted_count += 1
                    else:
                        print(f"Failed to delete key {key_ids[i]} for {country}")
                else:
                    print(f"Could not connect to Outline server for {country}")
            except Exception as e:
                print(f"Error deleting key {key_ids[i]} for {country}: {e}")
    
    # Mark subscription as expired
    mark_subscription_expired(sub_id)
    
    # Send result message
    if deleted_count == total_keys:
        message = "✅ Ваши ключи доступа к VPN были деактивированы.\nЧтобы получить новую подписку, используйте /subscribe"
    elif deleted_count > 0:
        message = f"⚠️ {deleted_count}/{total_keys} ключей доступа к VPN были деактивированы.\nЧтобы получить новую подписку, используйте /subscribe"
    else:
        message = "❌ Ошибка: Не удалось деактивировать ваши ключи доступа к VPN. Пожалуйста, попробуйте еще раз или обратитесь в поддержку."
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_menu")
        ]])
    )
    
    return ConversationHandler.END

def escape_markdown_v2(text: str) -> str:
    """Escape special characters for Telegram Markdown V2 format."""
    # Characters that need to be escaped in Markdown V2
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    
    return text

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "event loop is already running" in str(e):
            print("Error: Event loop is already running. This usually happens when running in Jupyter/IPython.")
            print("Please run this script in a fresh terminal or Python process.")
        else:
            raise