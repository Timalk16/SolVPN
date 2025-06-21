import logging
import time
import datetime
from functools import wraps # For admin_only decorator
from enum import Enum, auto
import uuid
from datetime import datetime, timedelta

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
    TELEGRAM_BOT_TOKEN, PLANS, ADMIN_USER_ID,
    COMMAND_RATE_LIMIT, CALLBACK_RATE_LIMIT, MESSAGE_RATE_LIMIT # Import new settings
)
from database import (
    init_db, add_user_if_not_exists, create_subscription_record,
    activate_subscription, get_active_subscriptions,
    # New DB functions for admin:
    get_all_active_subscriptions_for_admin, get_subscription_by_id, cancel_subscription_by_admin
)
from outline_utils import (
    get_outline_client, create_outline_key, rename_outline_key, delete_outline_key # Ensure delete_outline_key
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
    return f"{plan['name']} - {plan['price_usdt']:.2f} USDT"

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
    for sub_id, plan_id, end_date_str, access_url, status in active_subs:
        plan_name = PLANS.get(plan_id, {}).get("name", "Unknown Plan")
        end_date = datetime.fromisoformat(end_date_str).strftime('%Y-%m-%d %H:%M UTC')
        message += (
            f"Plan: {plan_name}\n"
            f"Expires on: {end_date}\n"
            f"Access Key: `{access_url}`\n\n"
        )
    message += "You can copy the access key and import it into your Outline client."
    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

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
    
    if query.data == "cancel_subscription_flow":
        await query.edit_message_text(
            "Subscription process cancelled. Use /subscribe to start again.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Back to Plans", callback_data="back_to_plans")
            ]])
        )
        return UserConversationState.CHOOSE_PLAN.value
    
    payment_id = context.user_data.get('payment_id')
    payment_type = context.user_data.get('payment_type')
    
    if not payment_id or not payment_type:
        await query.edit_message_text(
            "Error: Payment information not found. Please start over with /subscribe",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Back to Plans", callback_data="back_to_plans")
            ]])
        )
        return UserConversationState.CHOOSE_PLAN.value
    
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
                
                # Create subscription in database
                subscription_id = create_subscription_record(
                    user_id=user_id,
                    plan_id=plan_id,
                    duration_days=plan['duration_days']
                )
                
                # Create Outline key and activate subscription
                outline_client = get_outline_client()
                outline_key_id, outline_access_url = create_outline_key(outline_client)
                
                if not outline_key_id or not outline_access_url:
                    raise Exception("Failed to create Outline key")
                
                # Activate the subscription with the Outline key
                activate_subscription(
                    subscription_db_id=subscription_id,
                    outline_key_id=outline_key_id,
                    outline_access_url=outline_access_url,
                    duration_days=plan['duration_days'],
                    payment_id=payment_id
                )
                
                # Send success message
                await query.edit_message_text(
                    f"✅ Payment successful! Your subscription has been activated.\n\n"
                    f"Plan: {plan['name']}\n"
                    f"Duration: {plan['duration_days']} days\n"
                    f"Expires: {end_date.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    f"Use /my_subscriptions to check your subscription status.",
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
        elif status == "error":
            await query.edit_message_text(
                "❌ Error checking payment status. Please try again in a few moments.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔄 Check Again", callback_data="confirm_payment"),
                    InlineKeyboardButton("❌ Cancel", callback_data="cancel_subscription_flow")
                ]])
            )
            return UserConversationState.AWAIT_PAYMENT_CONFIRMATION.value
        else:
            await query.edit_message_text(
                f"❌ Payment status: {status}. Please make sure you've sent the payment and try again.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔄 Check Again", callback_data="confirm_payment"),
                    InlineKeyboardButton("❌ Cancel", callback_data="cancel_subscription_flow")
                ]])
            )
            return UserConversationState.AWAIT_PAYMENT_CONFIRMATION.value
            
    except Exception as e:
        logger.error(f"Error in confirm_payment: {e}")
        await query.edit_message_text(
            "❌ An error occurred while verifying your payment. Please try again or contact support.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔄 Check Again", callback_data="confirm_payment"),
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
    query = update.callback_query
    sub_db_id_to_delete = None

    if query:
        await query.answer()
        if query.data.startswith("admin_del_page_"):
            return await admin_paginate_subs(update, context)
        if query.data.startswith("admin_del_"):
            try:
                sub_db_id_to_delete = int(query.data.split("_")[-1])
            except ValueError:
                logger.error(f"Invalid callback data for admin_del: {query.data}")
                await query.edit_message_text("Invalid selection. Please try again or /cancel.") # No parse_mode
                return AdminConversationState.ADMIN_LIST_SUBS.value
        elif query.data == "admin_cancel_delete": # Added direct handling for cancel from this state
            return await admin_cancel_delete_flow(update, context)
        else: # Should not happen
            await query.edit_message_text("Invalid action. Please try again or /cancel.") # No parse_mode
            return AdminConversationState.ADMIN_LIST_SUBS.value
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except telegram.error.BadRequest as e:
            logger.warning(f"Could not remove keyboard in admin_sub_chosen: {e}")
    elif update.message and update.message.text:
        try:
            sub_db_id_to_delete = int(update.message.text.strip())
        except ValueError:
            await update.message.reply_text("Invalid ID format. Please enter a numeric Subscription DB ID or use /cancel.") # No parse_mode
            return AdminConversationState.ADMIN_LIST_SUBS.value

    if not sub_db_id_to_delete:
        err_msg = "No subscription ID provided. Please try again or use /cancel." # No parse_mode
        target_message_obj = query.message if query else update.message
        await target_message_obj.reply_text(err_msg) # No parse_mode
        return AdminConversationState.ADMIN_LIST_SUBS.value

    subscription = get_subscription_by_id(sub_db_id_to_delete)
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
    query = update.callback_query
    message_to_send = "Subscription deletion process cancelled." # No parse_mode
    if query:
        await query.answer()
        try:
            await query.edit_message_text(message_to_send) # No parse_mode
        except telegram.error.BadRequest:
            if update.effective_message:
                 await update.effective_message.reply_text(message_to_send) # No parse_mode
    elif update.message:
        await update.message.reply_text(message_to_send) # No parse_mode
    
    context.user_data.pop('sub_to_delete_id', None)
    context.user_data.pop('sub_to_delete_details', None)
    context.user_data.pop('admin_delete_page', None)
    return ConversationHandler.END

# --- Fallback and Error Handlers ---
async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Sorry, I didn't understand that command. Try /help.") # No parse_mode

def send_error_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str) -> None:
    """Utility to send an error message to a user, logs on failure."""
    try:
        context.bot.send_message(chat_id=chat_id, text=text)
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

    user_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("subscribe", subscribe_command)],
        states={
            UserConversationState.CHOOSE_PLAN.value: [
                CallbackQueryHandler(plan_chosen, pattern="^plan_"),
                CallbackQueryHandler(cancel_subscription_flow, pattern="^cancel_subscription_flow$")
            ],
            UserConversationState.CHOOSE_PAYMENT.value: [
                CallbackQueryHandler(payment_method_chosen, pattern="^pay_"),
                CallbackQueryHandler(back_to_plans_handler, pattern="^back_to_plans$"),
                CallbackQueryHandler(cancel_subscription_flow, pattern="^cancel_subscription_flow$") # User cancel
            ],
            UserConversationState.AWAIT_PAYMENT_CONFIRMATION.value: [
                CallbackQueryHandler(confirm_payment, pattern="^confirm_payment$"),
                CallbackQueryHandler(back_to_payment_choice_handler, pattern="^back_to_payment_choice$"),
                CallbackQueryHandler(cancel_subscription_flow, pattern="^cancel_subscription_flow$") # User cancel
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_subscription_flow), # User flow cancel command
            CallbackQueryHandler(cancel_subscription_flow, pattern="^cancel_subscription_flow$") # User flow cancel button
        ],
        per_message=False
    )

    admin_del_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("admin_del_sub", admin_delete_subscription_start)],
        states={
            AdminConversationState.ADMIN_LIST_SUBS.value: [
                CallbackQueryHandler(admin_sub_chosen_for_deletion, pattern="^admin_del_"),
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
    
    # If you want a global /cancel that can end any active conversation from these handlers:
    # async def global_cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    #     await update.message.reply_text("Operation cancelled.")
    #     context.user_data.clear() # Clear any specific data
    #     return ConversationHandler.END # This will end ANY active conversation
    # application.add_handler(CommandHandler("cancel", global_cancel_command))
    # Note: The above global cancel needs to be carefully placed or might interfere
    # with ConversationHandler's own fallbacks if they also use /cancel.
    # For now, specific cancels in each handler's fallbacks are safer.

    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    application.add_error_handler(error_handler)

    logger.info("Starting bot polling...")
    application.run_polling()

if __name__ == "__main__":
    main()