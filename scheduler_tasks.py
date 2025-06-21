import datetime
from telegram.ext import ContextTypes
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import get_expired_soon_or_active_subscriptions, mark_subscription_expired, get_subscription_by_id
from outline_utils import get_outline_client, delete_outline_key, rename_outline_key
from config import DURATION_PLANS, DB_PATH

async def check_expired_subscriptions(context: ContextTypes.DEFAULT_TYPE):
    """
    Checks for subscriptions that have expired and deactivates their Outline keys.
    Also sends renewal reminders for subscriptions expiring soon.
    """
    print(f"Scheduler: Running check_expired_subscriptions at {datetime.datetime.now()}")
    bot = context.bot

    subscriptions_to_check = get_expired_soon_or_active_subscriptions()
    now = datetime.datetime.utcnow()

    for sub in subscriptions_to_check:
        sub_id, user_id, status, end_date_str, key_ids, countries = sub
        end_date = datetime.datetime.fromisoformat(end_date_str) # Ensure it's datetime

        if status == 'active':
            # Check for expiration
            if end_date <= now:
                print(f"Scheduler: Subscription ID {sub_id} for user {user_id} has expired.")
                
                # Get subscription details for the renewal message
                subscription = get_subscription_by_id(sub_id)
                if not subscription:
                    print(f"Scheduler: Could not find subscription {sub_id} for renewal message")
                    continue
                
                duration_plan_id = subscription[2]  # duration_plan_id is the 3rd column
                plan = DURATION_PLANS.get(duration_plan_id, {})
                plan_name = plan.get('name', 'Unknown Plan')
                
                try:
                    # Send expiration message with renewal options
                    keyboard = [
                        [
                            InlineKeyboardButton("🔄 Renew Now", callback_data=f"renew_{sub_id}"),
                            InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_expired_{sub_id}")
                        ]
                    ]
                    
                    await bot.send_message(
                        chat_id=user_id,
                        text=(
                            f"😔 Your VPN subscription ({plan_name}) has expired.\n\n"
                            "You have 5 minutes to renew your subscription before your access keys are deactivated.\n\n"
                            "To continue using the VPN, please choose an option below:"
                        ),
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                    print(f"Scheduler: Sent expiration notice with renewal options to user {user_id} for sub {sub_id}")
                    
                    # Schedule key deletion after 5 minutes
                    context.job_queue.run_once(
                        delete_expired_keys,
                        datetime.timedelta(minutes=5),
                        data={'sub_id': sub_id, 'user_id': user_id, 'key_ids': key_ids, 'countries': countries}
                    )
                    
                except Exception as e:
                    print(f"Scheduler: Error sending expiration message to user {user_id}: {e}")
            
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
                                "Use /my_subscriptions to renew your subscription."
                            )
                        )
                        print(f"Scheduler: Sent renewal reminder to user {user_id} for sub {sub_id}")
                        if 'reminded_subs' not in context.job.context:
                            context.job.context['reminded_subs'] = []
                        context.job.context['reminded_subs'].append(sub_id)

                except Exception as e:
                    print(f"Scheduler: Error sending renewal reminder to user {user_id}: {e}")

async def delete_expired_keys(context: ContextTypes.DEFAULT_TYPE):
    """Delete the Outline keys after the grace period if not renewed."""
    job = context.job
    sub_id = job.data['sub_id']
    user_id = job.data['user_id']
    key_ids = job.data['key_ids'].split(',') if job.data['key_ids'] else []
    countries = job.data['countries'].split(',') if job.data['countries'] else []
    
    # Check if subscription was renewed
    subscription = get_subscription_by_id(sub_id)
    if subscription and subscription[5] == 'active':  # status is the 6th column
        print(f"Scheduler: Subscription {sub_id} was renewed, skipping key deletion")
        return
    
    # Delete keys for each country
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
                        print(f"Scheduler: Deleted key {key_ids[i]} for {country}")
                    else:
                        print(f"Scheduler: Failed to delete key {key_ids[i]} for {country}")
                else:
                    print(f"Scheduler: Could not connect to Outline server for {country}")
            except Exception as e:
                print(f"Scheduler: Error deleting key {key_ids[i]} for {country}: {e}")
    
    # Mark subscription as expired
    mark_subscription_expired(sub_id)
    
    # Send final message to user
    try:
        if deleted_count == total_keys:
            message = "❌ Your VPN access keys have been deactivated as the subscription was not renewed.\nTo get a new subscription, use /subscribe"
        elif deleted_count > 0:
            message = f"❌ {deleted_count}/{total_keys} VPN access keys have been deactivated as the subscription was not renewed.\nTo get a new subscription, use /subscribe"
        else:
            message = "❌ Your VPN subscription has expired. To get a new subscription, use /subscribe"
        
        await context.bot.send_message(chat_id=user_id, text=message)
    except Exception as e:
        print(f"Scheduler: Error sending final expiration message to user {user_id}: {e}")