import uuid
import asyncio
import logging
import aiohttp
import json
from typing import Tuple, Optional
from config import CRYPTOBOT_TESTNET_API_TOKEN, CRYPTOBOT_MAINNET_API_TOKEN, PLANS, USE_TESTNET, TELEGRAM_BOT_TOKEN

# Initialize logger
logger = logging.getLogger(__name__)

# Get the appropriate token based on USE_TESTNET setting
CRYPTOBOT_API_TOKEN = CRYPTOBOT_TESTNET_API_TOKEN if USE_TESTNET else CRYPTOBOT_MAINNET_API_TOKEN

# Debug log the token (first few characters for security)
if CRYPTOBOT_API_TOKEN:
    masked_token = CRYPTOBOT_API_TOKEN[:8] + "..." + CRYPTOBOT_API_TOKEN[-4:]
    logger.info(f"Using CryptoBot token: {masked_token}")
else:
    logger.error("CRYPTOBOT_API_TOKEN is not set!")

# API endpoints
API_BASE_URL = "https://testnet-pay.crypt.bot/api" if USE_TESTNET else "https://pay.crypt.bot/api"

async def get_crypto_payment_details(amount_usdt: float, plan_name: str) -> Tuple[str, str]:
    """
    Creates a crypto payment invoice using CryptoBot API.
    Returns a tuple of (payment_instructions, invoice_id)
    """
    try:
        # Use USDT as the asset
        asset = "USDT"
        logger.info(f"Creating invoice for {amount_usdt} {asset}")
        
        # Prepare request data
        headers = {
            "Crypto-Pay-API-Token": CRYPTOBOT_API_TOKEN
        }
        
        data = {
            "asset": asset,
            "amount": str(amount_usdt),
            "description": f"VPN Subscription - {plan_name}",
            "paid_btn_name": "callback",
            "paid_btn_url": f"https://t.me/{get_bot_username()}?start=payment_success",
            "allow_comments": False,
            "allow_anonymous": False,
            "expires_in": 3600  # 1 hour
        }
        
        # Make API request
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_BASE_URL}/createInvoice",
                headers=headers,
                json=data
            ) as response:
                if response.status == 200:
                    response_data = await response.json()
                    if response_data.get("ok"):
                        result = response_data["result"]
                        pay_url = result["pay_url"]
                        invoice_id = result["invoice_id"]
                        
                        # Add testnet warning if in testnet mode
                        testnet_warning = (
                            "⚠️ *TESTNET MODE*\n"
                            "You are using the testnet. This is for testing purposes only.\n"
                            "No real funds will be used.\n\n"
                        ) if USE_TESTNET else ""
                        
                        instructions = (
                            f"{testnet_warning}"
                            f"Please pay {amount_usdt} {asset} for your {plan_name} subscription.\n\n"
                            f"1. Click the payment link below:\n"
                            f"2. Follow the instructions in the CryptoBot interface\n"
                            f"3. After successful payment, click 'I have paid' button below\n\n"
                            f"Payment Link: {pay_url}"
                        )
                        
                        logger.info(f"Created crypto payment invoice: {invoice_id}")
                        return instructions, invoice_id
                    else:
                        error_msg = response_data.get("error", {}).get("message", "Unknown error")
                        logger.error(f"API error: {error_msg}")
                        raise Exception(f"API error: {error_msg}")
                else:
                    error_text = await response.text()
                    logger.error(f"HTTP error {response.status}: {error_text}")
                    raise Exception(f"HTTP error {response.status}: {error_text}")
        
    except Exception as e:
        logger.error(f"Error creating crypto payment: {str(e)}")
        raise

async def verify_crypto_payment(invoice_id: str) -> bool:
    """
    Verifies if a crypto payment has been completed.
    Returns True if payment is confirmed, False otherwise.
    """
    try:
        headers = {
            "Crypto-Pay-API-Token": CRYPTOBOT_API_TOKEN
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_BASE_URL}/getInvoices",
                headers=headers,
                params={"invoice_ids": [invoice_id]}
            ) as response:
                response_text = await response.text()
                logger.info(f"Verification response for invoice {invoice_id}: {response_text}")
                
                if response.status == 200:
                    response_data = await response.json()
                    if response_data.get("ok"):
                        result = response_data.get("result", {})
                        items = result.get("items", [])
                        if items:
                            status = items[0].get("status")
                            logger.info(f"Payment status for invoice {invoice_id}: {status}")
                            return status == "paid"
                        else:
                            logger.warning(f"No invoice found for ID {invoice_id}")
                            return False
                    else:
                        error_msg = response_data.get("error", {}).get("message", "Unknown error")
                        logger.error(f"API error in verification: {error_msg}")
                        return False
                else:
                    logger.error(f"HTTP error {response.status} in verification: {response_text}")
                    return False
                    
    except Exception as e:
        logger.error(f"Error verifying crypto payment: {str(e)}")
        return False

async def get_payment_status(invoice_id: str) -> str:
    """
    Gets the current status of a crypto payment.
    Returns the status as a string.
    """
    try:
        headers = {
            "Crypto-Pay-API-Token": CRYPTOBOT_API_TOKEN
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_BASE_URL}/getInvoices",
                headers=headers,
                params={"invoice_ids": [invoice_id]}
            ) as response:
                response_text = await response.text()
                logger.info(f"Status check response for invoice {invoice_id}: {response_text}")
                
                if response.status == 200:
                    response_data = await response.json()
                    if response_data.get("ok"):
                        result = response_data.get("result", {})
                        items = result.get("items", [])
                        if items:
                            status = items[0].get("status")
                            logger.info(f"Payment status for invoice {invoice_id}: {status}")
                            return status
                        else:
                            logger.warning(f"No invoice found for ID {invoice_id}")
                            return "not_found"
                    else:
                        error_msg = response_data.get("error", {}).get("message", "Unknown error")
                        logger.error(f"API error in status check: {error_msg}")
                        return "error"
                else:
                    logger.error(f"HTTP error {response.status} in status check: {response_text}")
                    return "error"
                    
    except Exception as e:
        logger.error(f"Error getting payment status: {str(e)}")
        return "error"

def get_bot_username() -> str:
    """Extract bot username from the token."""
    try:
        # The token format is: <bot_id>:<random_string>
        # We'll use the bot_id to get the username
        bot_id = TELEGRAM_BOT_TOKEN.split(':')[0]
        return f"bot_{bot_id}"  # This is a temporary solution
    except Exception as e:
        logger.error(f"Error getting bot username: {str(e)}")
        return "YourBotUsername"  # Fallback

# IMPORTANT: This is a MOCK implementation.
# Real YouKassa integration requires their SDK and webhook handling.
# Real Crypto payment needs a way to verify transactions.

def generate_yookassa_payment_link(amount_rub, description, order_id):
    """
    MOCK: Generates a placeholder YouKassa payment link.
    In a real scenario, you'd use the YouKassa SDK to create a payment object
    and get a confirmation_url.
    """
    # from yookassa import Configuration, Payment
    # Configuration.account_id = YOOKASSA_SHOP_ID
    # Configuration.secret_key = YOOKASSA_SECRET_KEY
    # payment = Payment.create({
    #     "amount": {"value": str(amount_rub), "currency": "RUB"},
    #     "confirmation": {"type": "redirect", "return_url": "https://t.me/YourBotUsername?start=payment_success"}, # Example
    #     "capture": True,
    #     "description": description,
    #     "metadata": {"order_id": order_id}
    # })
    # return payment.confirmation.confirmation_url, payment.id
    print(f"[MOCK YOOKASSA] Generating payment link for {amount_rub} RUB, order {order_id}")
    mock_payment_id = f"yk_{uuid.uuid4()}"
    return f"https://yookassa.ru/pay/mock_payment_url_for_{mock_payment_id}", mock_payment_id

async def verify_yookassa_payment(payment_id):
    """
    MOCK: Simulates verifying a YouKassa payment.
    Real: Use YouKassa API or webhook to check payment status.
    """
    # from yookassa import Payment
    # payment_info = Payment.find_one(payment_id)
    # return payment_info.status == 'succeeded'
    print(f"[MOCK YOOKASSA] Verifying payment {payment_id}. Assuming success for demo.")
    return True # Assume success for demo

def get_testnet_status() -> str:
    """Returns a warning message if in testnet mode."""
    if USE_TESTNET:
        return (
            "⚠️ *TESTNET MODE*\n"
            "You are using the testnet. This is for testing purposes only.\n"
            "No real funds will be used."
        )
    return ""