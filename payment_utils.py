import uuid
import asyncio
import logging
import aiohttp
import json
from typing import Tuple, Optional
from config import CRYPTOBOT_TESTNET_API_TOKEN, CRYPTOBOT_MAINNET_API_TOKEN, DURATION_PLANS, USE_TESTNET, TELEGRAM_BOT_TOKEN, YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY

# Import Youkassa SDK
from yookassa import Configuration, Payment
from yookassa.domain.request import PaymentRequest
from yookassa.domain.common import ConfirmationType

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

# Initialize Youkassa configuration
YOOKASSA_CONFIGURED = False
if YOOKASSA_SHOP_ID and YOOKASSA_SECRET_KEY and YOOKASSA_SHOP_ID != "YOUR_YOOKASSA_SHOP_ID":
    try:
        Configuration.account_id = YOOKASSA_SHOP_ID
        Configuration.secret_key = YOOKASSA_SECRET_KEY
        YOOKASSA_CONFIGURED = True
        logger.info(f"Youkassa configured with shop ID: {YOOKASSA_SHOP_ID[:8]}...")
    except Exception as e:
        logger.error(f"Error configuring Youkassa: {e}")
        YOOKASSA_CONFIGURED = False
else:
    logger.warning("Youkassa credentials not configured properly")

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
            "description": f"Подписка на VPN - {plan_name}",
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
                            "⚠️ *ТЕСТОВЫЙ РЕЖИМ*\n"
                            "Вы используете тестовую сеть. Это только для тестирования.\n"
                            "Реальные средства использоваться не будут.\n\n"
                        ) if USE_TESTNET else ""
                        
                        instructions = (
                            f"{testnet_warning}"
                            f"Пожалуйста, оплатите {amount_usdt} {asset} за вашу подписку '{plan_name}'.\n\n"
                            f"1. Нажмите на ссылку для оплаты ниже:\n"
                            f"2. Следуйте инструкциям в интерфейсе CryptoBot\n"
                            f"3. После успешной оплаты нажмите кнопку 'Я оплатил' ниже\n\n"
                            f"Ссылка для оплаты: {pay_url}"
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

async def get_yookassa_payment_details(amount_rub: float, plan_name: str) -> Tuple[str, str]:
    """
    Creates a Youkassa payment and returns payment instructions and payment ID.
    """
    if not YOOKASSA_CONFIGURED:
        raise Exception("Youkassa is not configured. Please set YOOKASSA_SHOP_ID and YOOKASSA_SECRET_KEY in your environment variables.")
    
    try:
        # Generate unique order ID
        order_id = str(uuid.uuid4())
        
        # Create payment request
        payment_request = PaymentRequest(
            amount={
                "value": str(amount_rub),
                "currency": "RUB"
            },
            confirmation={
                "type": ConfirmationType.REDIRECT,
                "return_url": f"https://t.me/{get_bot_username()}?start=payment_success"
            },
            capture=True,
            description=f"Подписка на VPN - {plan_name}",
            metadata={
                "order_id": order_id,
                "plan_name": plan_name
            }
            # Payment methods are managed in the Youkassa dashboard
        )
        
        # Create payment
        payment = Payment.create(payment_request)
        payment_id = payment.id
        confirmation_url = payment.confirmation.confirmation_url
        
        instructions = (
            f"💳 Оплата картой через Youkassa\n\n"
            f"Пожалуйста, оплатите {amount_rub:.2f} ₽ за вашу подписку '{plan_name}'.\n\n"
            f"1. Нажмите на ссылку для оплаты ниже\n"
            f"2. Следуйте инструкциям на странице Youkassa\n"
            f"3. После успешной оплаты нажмите кнопку 'Я оплатил' ниже\n\n"
            f"Ссылка для оплаты: {confirmation_url}"
        )
        
        logger.info(f"Created Youkassa payment: {payment_id}")
        return instructions, payment_id
        
    except Exception as e:
        logger.error(f"Error creating Youkassa payment: {str(e)}")
        raise

async def verify_yookassa_payment(payment_id: str) -> bool:
    """
    Verifies if a Youkassa payment has been completed.
    Returns True if payment is confirmed, False otherwise.
    """
    if not YOOKASSA_CONFIGURED:
        logger.error("Youkassa is not configured. Cannot verify payment.")
        return False
    
    try:
        # Get payment information
        payment = Payment.find_one(payment_id)
        
        logger.info(f"Youkassa payment {payment_id} status: {payment.status}")
        
        # Check if payment is successful
        return payment.status == "succeeded"
        
    except Exception as e:
        logger.error(f"Error verifying Youkassa payment: {str(e)}")
        return False

async def get_yookassa_payment_status(payment_id: str) -> str:
    """
    Gets the current status of a Youkassa payment.
    Returns the status as a string.
    """
    if not YOOKASSA_CONFIGURED:
        logger.error("Youkassa is not configured. Cannot get payment status.")
        return "error"
    
    try:
        payment = Payment.find_one(payment_id)
        logger.info(f"Youkassa payment {payment_id} status: {payment.status}")
        return payment.status
        
    except Exception as e:
        logger.error(f"Error getting Youkassa payment status: {str(e)}")
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
    DEPRECATED: Use get_yookassa_payment_details instead.
    This function is kept for backward compatibility.
    """
    logger.warning("generate_yookassa_payment_link is deprecated. Use get_yookassa_payment_details instead.")
    try:
        payment_request = PaymentRequest(
            amount={
                "value": str(amount_rub),
                "currency": "RUB"
            },
            confirmation={
                "type": ConfirmationType.REDIRECT,
                "return_url": f"https://t.me/{get_bot_username()}?start=payment_success"
            },
            capture=True,
            description=description,
            metadata={"order_id": order_id}
            # Payment methods are managed in the Youkassa dashboard
        )
        
        payment = Payment.create(payment_request)
        return payment.confirmation.confirmation_url, payment.id
        
    except Exception as e:
        logger.error(f"Error in generate_yookassa_payment_link: {str(e)}")
        # Fallback to mock for testing
        mock_payment_id = f"yk_{uuid.uuid4()}"
        return f"https://yookassa.ru/pay/mock_payment_url_for_{mock_payment_id}", mock_payment_id

async def verify_yookassa_payment_legacy(payment_id):
    """
    Legacy function for backward compatibility.
    """
    return await verify_yookassa_payment(payment_id)

def get_testnet_status() -> str:
    """Returns a warning message if in testnet mode."""
    if USE_TESTNET:
        return (
            "⚠️ *ТЕСТОВЫЙ РЕЖИМ*\n"
            "Вы используете тестовую сеть. Это только для тестирования.\n"
            "Реальные средства использоваться не будут."
        )
    return ""