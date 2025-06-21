import logging
import time
import datetime
from functools import wraps # For admin_only decorator
from enum import Enum, auto
import uuid
from datetime import datetime, timedelta
import sqlite3
import asyncio

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ConversationHandler,
    CallbackQueryHandler, ContextTypes, filters, JobQueue
)
from telegram.error import BadRequest

# We will need telegram.error for handling potential bad requests if we try to edit too much
import telegram 

from config import ( 
    TELEGRAM_BOT_TOKEN, PLANS, ADMIN_USER_ID, OUTLINE_SERVERS,
    COMMAND_RATE_LIMIT, CALLBACK_RATE_LIMIT, MESSAGE_RATE_LIMIT, DB_PATH # Added DB_PATH
)
from database import (
    init_db, add_user_if_not_exists, create_subscription_record,
    activate_subscription, get_active_subscriptions, add_subscription_country,
    get_subscription_countries,
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
    get_payment_status
)
from scheduler_tasks import check_expired_subscriptions

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states for user subscription
class UserConversationState(Enum):
    CHOOSE_PLAN = auto()
    CHOOSE_PAYMENT = auto()
    AWAIT_PAYMENT_CONFIRMATION = auto()

# Conversation states for admin deletion (ensure these are distinct from user states)
class AdminConversationState(Enum):
    ADMIN_LIST_SUBS = auto()
    ADMIN_CONFIRM_DELETE_SUB = auto()

ADMIN_PAGE_SIZE = 10  # Number of subscriptions per admin page

# --- Helper Functions ---
def get_plan_details_text(plan_id: str) -> str:
    """Return a formatted string with plan details for a given plan_id."""
    plan = PLANS[plan_id]
    countries_text = ", ".join([f"{OUTLINE_SERVERS[country]['flag']} {OUTLINE_SERVERS[country]['name']}" 
                               for country in plan.get('countries', [])])
    return f"{plan['name']} - {plan['price_usdt']:.2f} USDT ({countries_text})"

def build_plan_selection_keyboard() -> InlineKeyboardMarkup:
    """Build the inline keyboard for plan selection."""
    keyboard = [
        [InlineKeyboardButton(get_plan_details_text(plan_id_key), callback_data=f"plan_{plan_id_key}")]
        for plan_id_key in PLANS.keys()
    ]
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_subscription_flow")])
    return InlineKeyboardMarkup(keyboard)

def build_payment_method_keyboard(plan_id: str) -> InlineKeyboardMarkup:
    """Build the inline keyboard for payment method selection for a given plan."""
    plan_details = PLANS[plan_id]
    keyboard = [
        [InlineKeyboardButton(f"💰 Pay {plan_details['price_usdt']:.2f} USDT (Crypto)", callback_data="pay_crypto")],
        [InlineKeyboardButton("⬅️ Back to Plans", callback_data="back_to_plans")],
    ]
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
            await update.message.reply_text("Sorry, this command is for admins only.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapped

# --- Command Handlers (User & Admin) ---
@rate_limit_command("start")
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message and list available commands."""
    user = update.effective_user
    add_user_if_not_exists(user.id, user.username, user.first_name)
    logger.info(f"[start_command] User {user.id} ({user.username or user.first_name}) started the bot.")

    # Get testnet status
    testnet_status = get_testnet_status()
    testnet_notice = f"\n\n⚠️ *{testnet_status} Mode*" if testnet_status == "Testnet" else ""

    welcome_text = (
        f"👋 Welcome, {user.first_name}!\n\n"
        "I can help you get a fast and secure VPN subscription.\n\n"
        "Available commands:\n"
        "/subscribe - Choose a new subscription plan.\n"
        "/my_subscriptions - View your active subscriptions.\n"
        "/help - Get help information."
        f"{testnet_notice}"
    )
    if user.id == ADMIN_USER_ID:
        welcome_text += (
            "\n\nAdmin Commands:\n"
            "/admin_del_sub - Delete a user subscription."
        )
    # Escape special characters for Markdown
    welcome_text = welcome_text.replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace('`', '\\`')
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)

@rate_limit_command("help")
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send help information to the user."""
    user = update.effective_user
    
    # Get testnet status
    testnet_status = get_testnet_status()
    testnet_notice = f"\n\n⚠️ *{testnet_status} Mode*" if testnet_status == "Testnet" else ""
    
    help_text = (
        "ℹ️ How to use this bot:\n\n"
        "1\\. Use /subscribe to see available VPN plans\\.\n"
        "2\\. Choose a plan and a payment method\\.\n"
        "3\\. Follow the instructions to complete your payment\\.\n"
        "4\\. Once payment is confirmed, you'll receive your VPN access key\\.\n\n"
        "Use /my\\_subscriptions to check your current access\\.\n"
        "If you have any issues, contact support \\(details to be added here\\)\\."
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
    reply_markup = build_plan_selection_keyboard()
    await update.message.reply_text("Please choose a subscription plan:", reply_markup=reply_markup)
    return UserConversationState.CHOOSE_PLAN.value

@rate_limit_command("my_subscriptions")
async def my_subscriptions_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the user their active subscriptions."""
    user_id = update.effective_user.id
    active_subs = get_active_subscriptions(user_id)
    if not active_subs:
        await update.message.reply_text("You don't have any active subscriptions. Use /subscribe to get one!")
        return

    message = "Your active VPN subscriptions:\n\n"
    keyboard = []
    
    for sub_id, plan_id, end_date_str, status, countries, access_urls in active_subs:
        plan_name = PLANS.get(plan_id, {}).get("name", "Unknown Plan")
        end_date = datetime.fromisoformat(end_date_str).strftime('%Y-%m-%d %H:%M UTC')
        
        # Parse countries and access URLs
        country_list = countries.split(',') if countries else []
        access_url_list = access_urls.split(',') if access_urls else []
        
        message += f"**Plan:** {plan_name}\n"
        message += f"**Expires on:** {end_date}\n"
        message += f"**Countries:** {', '.join(country_list)}\n\n"
        
        # Add VPN keys for each country
        for i, country in enumerate(country_list):
            if i < len(access_url_list):
                country_name = OUTLINE_SERVERS.get(country, {}).get('name', country.title())
                country_flag = OUTLINE_SERVERS.get(country, {}).get('flag', '🌍')
                message += f"{country_flag} **{country_name}:** `{access_url_list[i]}`\n"
        
        message += "\n"
        
        # Add renew button for each subscription
        keyboard.append([InlineKeyboardButton(f"🔄 Renew {plan_name}", callback_data=f"renew_{sub_id}")])
    
    message += "You can copy the access keys and import them into your Outline client."
    await update.message.reply_text(
        message, 
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# --- User Subscription Conversation Handlers ---
async def plan_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    plan_id = query.data[len("plan_"):]
    context.user_data['selected_plan'] = plan_id

    plan_details = PLANS[plan_id]
    text = (
        f"You've selected: {plan_details['name']}\n"
        f"Price: {plan_details['price_usdt']:.2f} USDT.\n\n"
        "Please choose your payment method:"
    )
    reply_markup = build_payment_method_keyboard(plan_id)
    await query.edit_message_text(text=text, reply_markup=reply_markup)
    return UserConversationState.CHOOSE_PAYMENT.value

async def payment_method_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the payment method selection."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "back_to_plans":
        await query.edit_message_text(
            "Please select a subscription plan:",
            reply_markup=build_plan_selection_keyboard()
        )
        return UserConversationState.CHOOSE_PLAN.value
    
    plan_id = context.user_data.get('selected_plan')
    if not plan_id:
        await query.edit_message_text("Error: No plan selected. Please start over with /subscribe")
        return ConversationHandler.END
    
    plan = PLANS[plan_id]
    
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
                [InlineKeyboardButton("✅ I have paid", callback_data="confirm_payment")],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel_subscription_flow")]
            ]
            
            await query.edit_message_text(
                instructions,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error creating crypto payment: {e}")
            await query.edit_message_text(
                "Sorry, there was an error creating the payment. Please try again later.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Back to Plans", callback_data="back_to_plans")
                ]])
            )
            return UserConversationState.CHOOSE_PLAN.value
    
    return UserConversationState.AWAIT_PAYMENT_CONFIRMATION.value

async def confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle payment confirmation."""
    query = update.callback_query
    await query.answer()
    
    payment_id = context.user_data.get('payment_id')
    payment_type = context.user_data.get('payment_type')
    
    if not payment_id or not payment_type:
        await query.edit_message_text(
            "❌ Error: Payment information not found. Please start over with /subscribe",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_menu")
            ]])
        )
        return ConversationHandler.END
    
    try:
        # First check payment status
        status = await get_payment_status(payment_id)
        logger.info(f"Payment status check result: {status}")
        
        if status == "paid":
            # Verify the payment
            if payment_type == 'crypto':
                is_verified = await verify_crypto_payment(payment_id)
                logger.info(f"Crypto payment verification result: {is_verified}")
            else:
                is_verified = await verify_yookassa_payment(payment_id)
                logger.info(f"YouKassa payment verification result: {is_verified}")
            
            if is_verified:
                # Create subscription
                user_id = update.effective_user.id
                plan_id = context.user_data.get('selected_plan')
                plan = PLANS[plan_id]
                
                # Calculate subscription end date
                end_date = datetime.now() + timedelta(days=plan['duration_days'])
                
                # Check if this is a renewal
                renewing_sub_id = context.user_data.get('renewing_sub_id')
                
                if renewing_sub_id:
                    # This is a renewal - update existing subscription
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE subscriptions
                        SET start_date = ?, end_date = ?, status = 'active', payment_id = ?
                        WHERE id = ? AND user_id = ?
                    ''', (datetime.now(), end_date, payment_id, renewing_sub_id, user_id))
                    conn.commit()
                    conn.close()
                    
                    success_message = (
                        f"✅ Payment successful! Your subscription has been renewed.\n\n"
                        f"Plan: {plan['name']}\n"
                        f"Duration: {plan['duration_days']} days\n"
                        f"New Expiry: {end_date.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                        f"Use /my_subscriptions to check your subscription status."
                    )
                else:
                    # This is a new subscription
                    subscription_id = create_subscription_record(
                        user_id=user_id,
                        plan_id=plan_id,
                        duration_days=plan['duration_days']
                    )
                    
                    # Create Outline keys for each country in the plan
                    countries = plan.get('countries', [])
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
                                user_name = update.effective_user.first_name or update.effective_user.username or f"user_{user_id}"
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
                        duration_days=plan['duration_days'],
                        payment_id=payment_id
                    )
                    
                    countries_text = ", ".join([f"{OUTLINE_SERVERS[country]['flag']} {OUTLINE_SERVERS[country]['name']}" 
                                              for country in created_keys])
                    
                    success_message = (
                        f"✅ Payment successful! Your subscription has been activated.\n\n"
                        f"Plan: {plan['name']}\n"
                        f"Duration: {plan['duration_days']} days\n"
                        f"Countries: {countries_text}\n"
                        f"Expires: {end_date.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                        f"Use /my_subscriptions to get your VPN access keys."
                    )
                
                await query.edit_message_text(
                    success_message,
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_menu")
                    ]])
                )
                return ConversationHandler.END
            else:
                await query.edit_message_text(
                    "❌ Payment verification failed. Please try again or contact support.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔄 Check Again", callback_data="confirm_payment"),
                        InlineKeyboardButton("❌ Cancel", callback_data="cancel_subscription_flow")
                    ]])
                )
                return UserConversationState.AWAIT_PAYMENT_CONFIRMATION.value
        elif status == "not_found":
            await query.edit_message_text(
                "❌ Payment not found. Please make sure you've sent the payment and try again.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔄 Check Again", callback_data="confirm_payment"),
                    InlineKeyboardButton("❌ Cancel", callback_data="cancel_subscription_flow")
                ]])
            )
            return UserConversationState.AWAIT_PAYMENT_CONFIRMATION.value
    except Exception as e:
        logger.error(f"Error processing payment: {e}")
        await query.edit_message_text(
            "❌ An error occurred while processing your payment. Please try again or contact support.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔄 Try Again", callback_data="confirm_payment"),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel_subscription_flow")
            ]])
        )
        return UserConversationState.AWAIT_PAYMENT_CONFIRMATION.value

async def back_to_plans_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    reply_markup = build_plan_selection_keyboard()
    await query.edit_message_text("Please choose a subscription plan:", reply_markup=reply_markup)
    return UserConversationState.CHOOSE_PLAN.value

async def back_to_payment_choice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    plan_id = context.user_data['selected_plan']
    plan_details = PLANS[plan_id]
    text = (
        f"You've selected: {plan_details['name']}\n"
        f"Price: {plan_details['price_usdt']:.2f} USDT.\n\n"
        "Please choose your payment method:"
    )
    reply_markup = build_payment_method_keyboard(plan_id)
    await query.edit_message_text(text=text, reply_markup=reply_markup)
    return UserConversationState.CHOOSE_PAYMENT.value

async def cancel_subscription_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    message_to_send = "Subscription process cancelled. Use /subscribe to start over."
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

    for sub_id, user_id, username, first_name, plan_id, end_date_str, _, status in subs_to_display:
        user_display = username or first_name or f"User {user_id}"
        plan_name = PLANS.get(plan_id, {}).get("name", "Unknown")
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

    s_id, s_user_id, s_outline_key_id, s_status, s_access_url = subscription
    # Using simple strings for admin, with minimal formatting to avoid parse errors
    text = (
        f"Are you sure you want to delete this subscription?\n"
        f"DB ID: {s_id}\n"
        f"User ID: {s_user_id}\n"
        f"Outline Key ID: {s_outline_key_id or 'N/A'}\n"
        f"Status: {s_status}\n"
        f"Access URL: {s_access_url or 'N/A'}\n\n" # Displaying URL plainly for admin
        "This will delete the Outline key and mark the subscription as cancelled."
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
            await query.edit_message_text("Error: Subscription details not found. Start over with /admin_del_sub.") # No parse_mode
            context.user_data.clear()
            return ConversationHandler.END

        _, _, outline_key_id, current_status, _ = sub_details
        key_deleted_from_server = False
        db_updated = False

        if outline_key_id and current_status in ['active', 'pending_payment']:
            outline_client = get_outline_client()
            if outline_client:
                if delete_outline_key(outline_client, str(outline_key_id)):
                    key_deleted_from_server = True
                    logger.info(f"Admin {update.effective_user.id} deleted Outline key {outline_key_id}.")
                else:
                    logger.error(f"Admin {update.effective_user.id} failed to delete Outline key {outline_key_id}.")
            else:
                logger.error(f"Admin {update.effective_user.id}: No Outline client for key {outline_key_id}.")
        elif not outline_key_id:
             logger.info(f"Admin {update.effective_user.id}: No Outline key for sub {sub_db_id}.")
             key_deleted_from_server = True
        else:
            logger.info(f"Admin {update.effective_user.id}: Key {outline_key_id} for sub {sub_db_id} status '{current_status}', not deleting from server.")
            key_deleted_from_server = True

        if cancel_subscription_by_admin(sub_db_id):
            db_updated = True
        
        server_issue_message = ""
        if not key_deleted_from_server and outline_key_id and current_status in ['active', 'pending_payment']: # Only show server issue if we expected to delete
            server_issue_message = "However, there was an issue with the Outline key action on the server."

        if key_deleted_from_server and db_updated:
            await query.edit_message_text(f"✅ Subscription DB ID {sub_db_id} cancelled. Outline key actioned.", parse_mode=None) # Plain
        elif db_updated:
             await query.edit_message_text(f"⚠️ Subscription DB ID {sub_db_id} cancelled in DB. {server_issue_message}", parse_mode=None) # Plain
        else:
            await query.edit_message_text(f"❌ Failed to process for sub DB ID {sub_db_id}. Check logs.", parse_mode=None) # Plain
    else:
        await query.edit_message_text("Deletion cancelled. Subscription remains.", parse_mode=None) # Plain

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
        "Welcome to the VPN Bot! 🚀\n\n"
        "Available commands:\n"
        "/subscribe - Subscribe to VPN service\n"
        "/my_subscriptions - Check your active subscriptions\n"
        "/help - Get help and support\n"
        "/start - Show this menu"
    )
    return ConversationHandler.END

# --- Fallback and Error Handlers ---
async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Sorry, I didn't understand that command. Try /help.") # No parse_mode

def send_error_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str) -> None:
    """Utility to send an error message to a user, logs on failure."""
    try:
        asyncio.create_task(context.bot.send_message(chat_id=chat_id, text=text))
    except Exception as e:
        logger.error(f"Error sending error message to user: {e}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Global error handler for uncaught exceptions in handlers."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    if isinstance(update, Update) and update.effective_chat:
        send_error_message(context, update.effective_chat.id, "An unexpected error occurred. Please try again or contact support.")

# --- Main Function ---
def main() -> None:
    """Entry point for the bot: initializes the database, sets up handlers, and starts polling."""
    init_db()
    logger.info("Database initialized.")

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).job_queue(JobQueue()).build()

    job_queue = application.job_queue
    job_queue.run_repeating(check_expired_subscriptions, interval=60, first=10, name="expiry_check_short_interval")
    logger.info("Scheduled job for checking expired subscriptions.")

    # Add conversation handler for user subscription flow
    user_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("subscribe", subscribe_command),
            CallbackQueryHandler(handle_renewal, pattern=r"^renew_\d+$")
        ],
        states={
            UserConversationState.CHOOSE_PLAN.value: [
                CallbackQueryHandler(plan_chosen, pattern=r"^plan_"),
                CallbackQueryHandler(cancel_subscription_flow, pattern="^cancel_subscription_flow$")
            ],
            UserConversationState.CHOOSE_PAYMENT.value: [
                CallbackQueryHandler(payment_method_chosen, pattern=r"^pay_"),
                CallbackQueryHandler(back_to_plans_handler, pattern="^back_to_plans$"),
                CallbackQueryHandler(cancel_subscription_flow, pattern="^cancel_subscription_flow$") # User cancel
            ],
            UserConversationState.AWAIT_PAYMENT_CONFIRMATION.value: [
                CallbackQueryHandler(confirm_payment, pattern="^confirm_payment$"),
                CallbackQueryHandler(cancel_subscription_flow, pattern="^cancel_subscription_flow$")
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel_subscription_flow)]
    )

    admin_del_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("admin_del_sub", admin_delete_subscription_start)],
        states={
            AdminConversationState.ADMIN_LIST_SUBS.value: [
                CallbackQueryHandler(admin_paginate_subs, pattern="^admin_del_page_"),
                CallbackQueryHandler(admin_sub_chosen_for_deletion, pattern="^admin_del_\d+$"),
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
        per_message=False,
        name="admin_delete_conversation",
    )

    application.add_handler(user_conv_handler)
    application.add_handler(admin_del_conv_handler)

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("my_subscriptions", my_subscriptions_command))
    
    # Add handlers for buttons outside conversation flow
    application.add_handler(CallbackQueryHandler(back_to_menu_handler, pattern="^back_to_menu$"))
    application.add_handler(CallbackQueryHandler(handle_cancel_expired, pattern=r"^cancel_expired_\d+$"))
    
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    application.add_error_handler(error_handler)

    logger.info("Starting bot polling...")
    application.run_polling()

async def handle_renewal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle subscription renewal request."""
    query = update.callback_query
    await query.answer()
    
    sub_id = int(query.data.split('_')[1])
    user_id = update.effective_user.id
    
    # Get subscription details
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT plan_id FROM subscriptions
        WHERE id = ? AND user_id = ?
    ''', (sub_id, user_id))
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        await query.edit_message_text(
            "❌ Error: Subscription not found or you don't have permission to renew it.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_menu")
            ]])
        )
        return ConversationHandler.END
    
    plan_id = result[0]
    plan = PLANS[plan_id]
    
    # Store the subscription ID for later use
    context.user_data['renewing_sub_id'] = sub_id
    context.user_data['selected_plan'] = plan_id
    
    text = (
        f"You're renewing: {plan['name']}\n"
        f"Price: {plan['price_usdt']:.2f} USDT.\n\n"
        "Please choose your payment method:"
    )
    reply_markup = build_payment_method_keyboard(plan_id)
    await query.edit_message_text(text=text, reply_markup=reply_markup)
    return UserConversationState.CHOOSE_PAYMENT.value

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
        message = "✅ Your VPN access keys have been deactivated.\nTo get a new subscription, use /subscribe"
    elif deleted_count > 0:
        message = f"⚠️ {deleted_count}/{total_keys} VPN access keys have been deactivated.\nTo get a new subscription, use /subscribe"
    else:
        message = "❌ Error: Failed to deactivate your VPN access keys. Please try again or contact support."
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_menu")
        ]])
    )
    
    return ConversationHandler.END

if __name__ == "__main__":
    main()