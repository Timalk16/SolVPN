#!/usr/bin/env python3
"""
Test script to verify all Telegram bot handlers are async and callable.
Also simulates a call to a main handler to ensure no NoneType or sync function is used.
"""
import sys
import asyncio
import inspect
import unittest
from unittest.mock import MagicMock, AsyncMock

# Import handlers from main.py
from main import (
    start_command, help_command, subscribe_command, my_subscriptions_command,
    duration_chosen, payment_method_chosen, confirm_payment, countries_chosen,
    cancel_subscription_flow, back_to_duration_handler, menu_subscribe_handler,
    menu_my_subscriptions_handler, menu_help_handler, handle_renewal, log_all_messages
)

class TestHandlers(unittest.TestCase):
    def test_handlers_are_async(self):
        handlers = [
            start_command, help_command, subscribe_command, my_subscriptions_command,
            duration_chosen, payment_method_chosen, confirm_payment, countries_chosen,
            cancel_subscription_flow, back_to_duration_handler, menu_subscribe_handler,
            menu_my_subscriptions_handler, menu_help_handler, handle_renewal, log_all_messages
        ]
        for handler in handlers:
            self.assertTrue(inspect.iscoroutinefunction(handler), f"Handler {handler.__name__} is not async!")

    def test_handler_invocation(self):
        # Simulate a call to subscribe_command
        update = MagicMock()
        context = MagicMock()
        # Simulate update.message.reply_text as an async method
        update.message.reply_text = AsyncMock()
        # Simulate context.user_data as a dict
        context.user_data = {}
        # Simulate update.effective_user
        update.effective_user.id = 12345
        update.effective_user.username = 'testuser'
        update.effective_user.first_name = 'Test'
        # Run the handler
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(subscribe_command(update, context))
        self.assertIsNotNone(result, "subscribe_command did not return a value (should return a state)")

if __name__ == "__main__":
    unittest.main() 