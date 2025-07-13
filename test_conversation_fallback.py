#!/usr/bin/env python3
"""
Test script to verify conversation fallback handlers work correctly.
This tests that users can break out of conversation states using fallback commands.
"""

import asyncio
import logging
from unittest.mock import Mock, AsyncMock, patch
from telegram import Update, User, Message, Chat, CallbackQuery
from telegram.ext import ContextTypes
from main import (
    subscribe_command, start_command, help_command, cancel_subscription_flow,
    UserConversationState, ConversationHandler
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_mock_update(command: str = None, callback_data: str = None, user_id: int = 123456):
    """Create a mock Update object for testing."""
    mock_user = Mock(spec=User)
    mock_user.id = user_id
    mock_user.username = "testuser"
    mock_user.first_name = "Test"
    
    mock_chat = Mock(spec=Chat)
    mock_chat.id = user_id
    
    mock_message = Mock(spec=Message)
    mock_message.text = f"/{command}" if command else None
    mock_message.from_user = mock_user
    mock_message.chat = mock_chat
    
    mock_update = Mock(spec=Update)
    mock_update.effective_user = mock_user
    mock_update.message = mock_message
    mock_update.callback_query = None
    
    if callback_data:
        mock_callback_query = Mock(spec=CallbackQuery)
        mock_callback_query.data = callback_data
        mock_callback_query.answer = AsyncMock()
        mock_callback_query.edit_message_text = AsyncMock()
        mock_update.callback_query = mock_callback_query
    
    return mock_update

def create_mock_context():
    """Create a mock Context object for testing."""
    mock_context = Mock(spec=ContextTypes.DEFAULT_TYPE)
    mock_context.user_data = {}
    return mock_context

async def test_subscribe_command_clears_state():
    """Test that subscribe_command clears conversation state."""
    print("Testing subscribe_command state clearing...")
    
    update = create_mock_update("subscribe")
    context = create_mock_context()
    
    # Simulate existing conversation state
    context.user_data['selected_duration'] = 'monthly'
    context.user_data['payment_id'] = 'test_payment'
    
    print(f"Before: context.user_data = {context.user_data}")
    
    result = await subscribe_command(update, context)
    
    print(f"After: context.user_data = {context.user_data}")
    print(f"Result: {result}")
    
    # Verify state was cleared
    assert len(context.user_data) == 0, "User data should be cleared"
    assert result == UserConversationState.CHOOSE_DURATION.value, "Should return CHOOSE_DURATION state"
    
    print("✅ subscribe_command clears state correctly")

async def test_start_command_clears_state():
    """Test that start_command clears conversation state."""
    print("Testing start_command state clearing...")
    
    update = create_mock_update("start")
    context = create_mock_context()
    
    # Simulate existing conversation state
    context.user_data['selected_duration'] = 'monthly'
    context.user_data['payment_id'] = 'test_payment'
    
    print(f"Before: context.user_data = {context.user_data}")
    
    # Mock the database function to avoid connection issues
    with patch('main.add_user_if_not_exists'):
        await start_command(update, context)
    
    print(f"After: context.user_data = {context.user_data}")
    
    # Verify state was cleared
    assert len(context.user_data) == 0, "User data should be cleared"
    
    print("✅ start_command clears state correctly")

async def test_help_command_clears_state():
    """Test that help_command clears conversation state."""
    print("Testing help_command state clearing...")
    
    update = create_mock_update("help")
    context = create_mock_context()
    
    # Simulate existing conversation state
    context.user_data['selected_duration'] = 'monthly'
    context.user_data['payment_id'] = 'test_payment'
    
    print(f"Before: context.user_data = {context.user_data}")
    
    # Mock the database function to avoid connection issues
    with patch('main.get_testnet_status', return_value="Mainnet"):
        await help_command(update, context)
    
    print(f"After: context.user_data = {context.user_data}")
    
    # Verify state was cleared
    assert len(context.user_data) == 0, "User data should be cleared"
    
    print("✅ help_command clears state correctly")

async def test_cancel_command_ends_conversation():
    """Test that cancel_subscription_flow ends conversation."""
    print("Testing cancel_subscription_flow...")
    
    update = create_mock_update("cancel")
    context = create_mock_context()
    
    # Simulate existing conversation state
    context.user_data['selected_duration'] = 'monthly'
    
    print(f"Before: context.user_data = {context.user_data}")
    
    # Mock the message reply to avoid errors
    update.message.reply_text = AsyncMock()
    
    result = await cancel_subscription_flow(update, context)
    
    print(f"After: context.user_data = {context.user_data}")
    print(f"Result: {result}")
    
    # Verify conversation ends
    assert result == ConversationHandler.END, "Should end conversation"
    
    print("✅ cancel_subscription_flow ends conversation correctly")

async def test_conversation_fallback_handlers():
    """Test all conversation fallback handlers."""
    print("\n🧪 Testing Conversation Fallback Handlers")
    print("=" * 50)
    
    try:
        await test_subscribe_command_clears_state()
        await test_start_command_clears_state()
        await test_help_command_clears_state()
        await test_cancel_command_ends_conversation()
        
        print("\n✅ All conversation fallback tests passed!")
        print("\nThis means users can now:")
        print("- Type /subscribe to restart subscription flow from any conversation state")
        print("- Type /start to break out of conversation and return to main menu")
        print("- Type /help to break out of conversation and get help")
        print("- Type /cancel to properly end the conversation")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_conversation_fallback_handlers()) 