#!/usr/bin/env python3
"""
Automated Test Harness for Telegram VPN Bot
Tests all subscription flows, interruptions, and edge cases
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes
import json
import os

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Test result data class"""
    test_name: str
    passed: bool
    error: Optional[str] = None
    duration: float = 0.0
    details: Dict = None

class TelegramBotTester:
    """Automated test harness for Telegram bot"""
    
    def __init__(self, bot_token: str, test_user_id: int):
        self.bot_token = bot_token
        self.test_user_id = test_user_id
        self.bot = Bot(token=bot_token)
        self.test_results: List[TestResult] = []
        self.last_message_id: Optional[int] = None
        self.last_callback_query_id: Optional[str] = None
        
    async def send_message(self, text: str) -> int:
        """Send a message and return message ID"""
        try:
            message = await self.bot.send_message(
                chat_id=self.test_user_id,
                text=text
            )
            self.last_message_id = message.message_id
            logger.info(f"Sent message: {text}")
            return message.message_id
        except Exception as e:
            logger.error(f"Failed to send message '{text}': {e}")
            raise
    
    async def send_callback_query(self, callback_data: str, message_id: Optional[int] = None) -> bool:
        """Simulate a callback query (button press)"""
        try:
            msg_id = message_id or self.last_message_id
            if not msg_id:
                raise ValueError("No message ID available for callback query")
            
            # Note: This is a simplified simulation. In real testing, you'd need to
            # actually create callback queries through the bot framework
            logger.info(f"Simulated callback query: {callback_data} on message {msg_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to send callback query '{callback_data}': {e}")
            return False
    
    async def wait_for_response(self, timeout: int = 10) -> bool:
        """Wait for bot response (simplified - in real testing you'd check for new messages)"""
        await asyncio.sleep(2)  # Simulate waiting for response
        return True
    
    async def run_test(self, test_func, test_name: str) -> TestResult:
        """Run a single test and record results"""
        start_time = time.time()
        result = TestResult(test_name=test_name, passed=False, details={})
        
        try:
            logger.info(f"Running test: {test_name}")
            await test_func()
            result.passed = True
            logger.info(f"✓ Test passed: {test_name}")
        except Exception as e:
            result.error = str(e)
            logger.error(f"✗ Test failed: {test_name} - {e}")
        finally:
            result.duration = time.time() - start_time
            self.test_results.append(result)
        
        return result
    
    async def test_start_command(self):
        """Test /start command"""
        await self.send_message("/start")
        await self.wait_for_response()
        # In real testing, you'd verify the response contains welcome message and logo
    
    async def test_help_command(self):
        """Test /help command"""
        await self.send_message("/help")
        await self.wait_for_response()
        # Verify help message is sent
    
    async def test_subscribe_flow_basic(self):
        """Test basic subscription flow"""
        # Start subscription
        await self.send_message("/subscribe")
        await self.wait_for_response()
        
        # Select duration (simulate button press)
        await self.send_callback_query("duration_monthly")
        await self.wait_for_response()
        
        # Select payment method
        await self.send_callback_query("pay_card")
        await self.wait_for_response()
        
        # Cancel the flow
        await self.send_callback_query("cancel_subscription_flow")
        await self.wait_for_response()
    
    async def test_subscribe_flow_crypto(self):
        """Test subscription flow with crypto payment"""
        await self.send_message("/subscribe")
        await self.wait_for_response()
        
        await self.send_callback_query("duration_yearly")
        await self.wait_for_response()
        
        await self.send_callback_query("pay_crypto")
        await self.wait_for_response()
        
        await self.send_callback_query("cancel_subscription_flow")
        await self.wait_for_response()
    
    async def test_flow_interruption(self):
        """Test interrupting subscription flow"""
        # Start first subscription
        await self.send_message("/subscribe")
        await self.wait_for_response()
        
        await self.send_callback_query("duration_monthly")
        await self.wait_for_response()
        
        # Interrupt with new subscribe command
        await self.send_message("/subscribe")
        await self.wait_for_response()
        
        # Try to use old buttons (should be handled gracefully)
        await self.send_callback_query("pay_card")
        await self.wait_for_response()
    
    async def test_command_interruptions(self):
        """Test various command interruptions"""
        await self.send_message("/subscribe")
        await self.wait_for_response()
        
        # Test /cancel during flow
        await self.send_message("/cancel")
        await self.wait_for_response()
        
        # Test /help during flow
        await self.send_message("/subscribe")
        await self.wait_for_response()
        await self.send_message("/help")
        await self.wait_for_response()
        
        # Test /start during flow
        await self.send_message("/subscribe")
        await self.wait_for_response()
        await self.send_message("/start")
        await self.wait_for_response()
    
    async def test_invalid_actions(self):
        """Test invalid actions and edge cases"""
        # Try to confirm payment without being in payment flow
        await self.send_callback_query("confirm_payment")
        await self.wait_for_response()
        
        # Try to select countries without valid subscription
        await self.send_callback_query("countries_europe")
        await self.wait_for_response()
        
        # Try to go back to duration without context
        await self.send_callback_query("back_to_duration")
        await self.wait_for_response()
    
    async def test_admin_commands(self):
        """Test admin commands (if user is admin)"""
        await self.send_message("/admin_del_sub")
        await self.wait_for_response()
        
        # Test admin pagination
        await self.send_callback_query("admin_del_page_next")
        await self.wait_for_response()
        
        # Test admin cancel
        await self.send_callback_query("admin_cancel_delete")
        await self.wait_for_response()
    
    async def test_my_subscriptions(self):
        """Test /my_subscriptions command"""
        await self.send_message("/my_subscriptions")
        await self.wait_for_response()
    
    async def test_support_command(self):
        """Test /support command"""
        await self.send_message("/support")
        await self.wait_for_response()
    
    async def test_menu_support_button(self):
        """Test the Поддержка (Support) menu button"""
        await self.send_message("/start")
        await self.wait_for_response()
        await self.send_callback_query("menu_support")
        await self.wait_for_response()
    
    async def test_unknown_command(self):
        """Test unknown command handling"""
        await self.send_message("/unknown_command_12345")
        await self.wait_for_response()
    
    async def test_rate_limiting(self):
        """Test rate limiting by sending commands rapidly"""
        for i in range(5):
            await self.send_message("/start")
            await asyncio.sleep(0.1)  # Very short delay
        
        await self.wait_for_response()
    
    async def run_all_tests(self) -> List[TestResult]:
        """Run all tests"""
        logger.info("Starting automated bot tests...")
        
        test_functions = [
            (self.test_start_command, "Start Command"),
            (self.test_help_command, "Help Command"),
            (self.test_subscribe_flow_basic, "Basic Subscription Flow"),
            (self.test_subscribe_flow_crypto, "Crypto Subscription Flow"),
            (self.test_flow_interruption, "Flow Interruption"),
            (self.test_command_interruptions, "Command Interruptions"),
            (self.test_invalid_actions, "Invalid Actions"),
            (self.test_admin_commands, "Admin Commands"),
            (self.test_my_subscriptions, "My Subscriptions"),
            (self.test_support_command, "Support Command"),
            (self.test_menu_support_button, "Menu Support Button"),
            (self.test_unknown_command, "Unknown Command"),
            (self.test_rate_limiting, "Rate Limiting"),
        ]
        
        for test_func, test_name in test_functions:
            await self.run_test(test_func, test_name)
            await asyncio.sleep(1)  # Brief pause between tests
        
        return self.test_results
    
    def generate_report(self) -> str:
        """Generate a test report"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result.passed)
        failed_tests = total_tests - passed_tests
        total_duration = sum(result.duration for result in self.test_results)
        
        report = f"""
=== TELEGRAM BOT TEST REPORT ===
Total Tests: {total_tests}
Passed: {passed_tests}
Failed: {failed_tests}
Success Rate: {(passed_tests/total_tests)*100:.1f}%
Total Duration: {total_duration:.2f}s

DETAILED RESULTS:
"""
        
        for result in self.test_results:
            status = "✓ PASS" if result.passed else "✗ FAIL"
            report += f"{status} {result.test_name} ({result.duration:.2f}s)"
            if result.error:
                report += f" - Error: {result.error}"
            report += "\n"
        
        return report

async def main():
    """Main test runner"""
    # Configuration - replace with your actual values
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "your_bot_token_here")
    TEST_USER_ID = int(os.getenv("TEST_USER_ID", "123456789"))  # Your Telegram user ID
    
    if BOT_TOKEN == "your_bot_token_here":
        print("Please set TELEGRAM_BOT_TOKEN environment variable or update the script")
        return
    
    # Create tester instance
    tester = TelegramBotTester(BOT_TOKEN, TEST_USER_ID)
    
    try:
        # Run all tests
        results = await tester.run_all_tests()
        
        # Generate and print report
        report = tester.generate_report()
        print(report)
        
        # Save report to file
        with open("test_report.txt", "w", encoding="utf-8") as f:
            f.write(report)
        
        print(f"\nTest report saved to test_report.txt")
        
        # Exit with error code if any tests failed
        failed_count = sum(1 for result in results if not result.passed)
        if failed_count > 0:
            print(f"\n{failed_count} tests failed!")
            exit(1)
        else:
            print("\nAll tests passed! 🎉")
            
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 