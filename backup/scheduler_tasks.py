import datetime
from telegram.ext import ContextTypes
from database import get_expired_soon_or_active_subscriptions, mark_subscription_expired
from outline_utils import get_outline_client, delete_outline_key, rename_outline_key
from config import PLANS

async def check_expired_subscriptions(context: ContextTypes.DEFAULT_TYPE):
    """
    Checks for subscriptions that have expired and deactivates their Outline keys.
    Also sends renewal reminders for subscriptions expiring soon.
    """
    print(f"Scheduler: Running check_expired_subscriptions at {datetime.datetime.now()}")
    bot = context.bot
    outline_client = get_outline_client()
    if not outline_client:
        print("Scheduler: Could not connect to Outline server. Skipping checks.")
        return

    subscriptions_to_check = get_expired_soon_or_active_subscriptions()
    now = datetime.datetime.utcnow()

    for sub in subscriptions_to_check:
        sub_id, user_id, outline_key_id, status, end_date_str = sub
        end_date = datetime.datetime.fromisoformat(end_date_str) # Ensure it's datetime

        if status == 'active':
            # Check for expiration
            if end_date <= now:
                print(f"Scheduler: Subscription ID {sub_id} for user {user_id} has expired.")
                deleted = delete_outline_key(outline_client, outline_key_id)
                if deleted:
                    mark_subscription_expired(sub_id)
                    try:
                        await bot.send_message(
                            chat_id=user_id,
                            text=(
                                "😔 Your VPN subscription has expired and your access key has been deactivated.\n"
                                "To continue using the VPN, please renew your subscription.\n"
                                "Use /subscribe to choose a new plan."
                            )
                        )
                        print(f"Scheduler: Sent expiration notice to user {user_id} for sub {sub_id}")
                    except Exception as e:
                        print(f"Scheduler: Error sending expiration message to user {user_id}: {e}")
                else:
                    print(f"Scheduler: Failed to delete Outline key {outline_key_id} for expired sub {sub_id}.")
            
            # Check for renewal reminder (e.g., 3 days before expiry)
            elif (end_date - now).days <= 3 and (end_date - now).days >= 0:
                # Basic check to avoid sending multiple reminders if job runs frequently
                # A more robust way would be to store a "reminder_sent" flag in DB
                print(f"Scheduler: Subscription ID {sub_id} for user {user_id} expiring soon ({end_date.strftime('%Y-%m-%d %H:%M')}).")
                try:
                    # Check if we already sent a reminder (very basic, improve with a DB flag)
                    if not context.job.context or sub_id not in context.job.context.get('reminded_subs', []):
                        await bot.send_message(
                            chat_id=user_id,
                            text=(
                                f"🔔 Your VPN subscription is expiring on {end_date.strftime('%Y-%m-%d %H:%M UTC')}.\n"
                                "Don't miss out! Renew now to maintain uninterrupted access.\n"
                                "Use /subscribe to choose a new plan."
                            )
                        )
                        print(f"Scheduler: Sent renewal reminder to user {user_id} for sub {sub_id}")
                        if 'reminded_subs' not in context.job.context:
                            context.job.context['reminded_subs'] = []
                        context.job.context['reminded_subs'].append(sub_id)

                except Exception as e:
                    print(f"Scheduler: Error sending renewal reminder to user {user_id}: {e}")