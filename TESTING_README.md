# Telegram VPN Bot Testing Suite

This directory contains a comprehensive testing suite for your Telegram VPN bot. The tests cover all subscription flows, interruptions, edge cases, and ensure that all buttons work correctly regardless of conversation state.

## 📁 Files Overview

- **`test_bot_flows.py`** - Basic test harness that simulates user interactions
- **`advanced_bot_tester.py`** - Advanced test harness with response verification
- **`setup_testing.py`** - Setup script to configure and run tests easily
- **`compress_logo.py`** - Script to compress your bot logo for Telegram
- **`TESTING_README.md`** - This documentation file

## 🚀 Quick Start

### 1. Setup and Run Tests

```bash
# Run the setup script (recommended for first time)
python setup_testing.py
```

The setup script will:

- Check and install required dependencies
- Ask for your bot token and user ID
- Create a `.env` file for configuration
- Run the tests automatically

### 2. Manual Setup

If you prefer manual setup:

```bash
# Install dependencies
pip install python-telegram-bot aiohttp pillow

# Set environment variables
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TEST_USER_ID="your_telegram_user_id"

# Run tests
python test_bot_flows.py
python advanced_bot_tester.py
```

## 🧪 Test Coverage

### Basic Tests (`test_bot_flows.py`)

- ✅ Start command (`/start`)
- ✅ Help command (`/help`)
- ✅ Basic subscription flow (card payment)
- ✅ Crypto subscription flow
- ✅ Flow interruption (multiple `/subscribe` commands)
- ✅ Command interruptions (`/cancel`, `/help`, `/start` during flow)
- ✅ Invalid actions (buttons without context)
- ✅ Admin commands (`/admin_del_sub`)
- ✅ My subscriptions (`/my_subscriptions`)
- ✅ Support command (`/support`)
- ✅ Unknown command handling
- ✅ Rate limiting

### Advanced Tests (`advanced_bot_tester.py`)

All basic tests plus:

- ✅ Payment confirmation flow
- ✅ Country selection flow
- ✅ Response verification
- ✅ Detailed error reporting
- ✅ JSON results export

## 🔧 Configuration

### Environment Variables

Create a `.env` file or set these environment variables:

```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
TEST_USER_ID=your_telegram_user_id
```

### Getting Your User ID

To get your Telegram user ID:

1. Send a message to [@userinfobot](https://t.me/userinfobot)
2. It will reply with your user ID

## 📊 Test Reports

After running tests, you'll get:

1. **Console output** - Real-time test results
2. **Text report** - Detailed test report saved to file
3. **JSON results** - Machine-readable results for analysis

### Report Files

- `test_report.txt` - Basic test results
- `advanced_test_report_YYYYMMDD_HHMMSS.txt` - Advanced test results
- `test_results_YYYYMMDD_HHMMSS.json` - JSON format results

## 🎯 What the Tests Verify

### 1. Subscription Flow Integrity

- Users can start `/subscribe` multiple times
- Old buttons from previous flows still work
- Payment and cancel buttons function correctly
- Country selection works after payment

### 2. Flow Interruptions

- Commands like `/start`, `/help`, `/cancel` properly interrupt flows
- State is reset correctly after interruptions
- No orphaned conversation states

### 3. Edge Cases

- Invalid button presses are handled gracefully
- Missing context doesn't crash the bot
- Rate limiting works as expected

### 4. Admin Functions

- Admin commands work correctly
- Pagination functions properly
- Deletion flows can be cancelled

## 🛠️ Troubleshooting

### Common Issues

1. **"Bot token not found"**

   - Make sure you've set the `TELEGRAM_BOT_TOKEN` environment variable
   - Or run `python setup_testing.py` to configure it

2. **"User ID not found"**

   - Get your user ID from [@userinfobot](https://t.me/userinfobot)
   - Set the `TEST_USER_ID` environment variable

3. **"Module not found"**

   - Run `pip install python-telegram-bot aiohttp pillow`
   - Or use `python setup_testing.py` to install dependencies

4. **Tests fail with network errors**
   - Check your internet connection
   - Verify your bot token is correct
   - Make sure your bot is running

### Debug Mode

To see more detailed logs, modify the logging level in the test files:

```python
logging.basicConfig(level=logging.DEBUG)
```

## 🔄 Continuous Testing

### Automated Testing

You can integrate these tests into your CI/CD pipeline:

```bash
# Example GitHub Actions step
- name: Run Bot Tests
  run: |
    export TELEGRAM_BOT_TOKEN=${{ secrets.BOT_TOKEN }}
    export TEST_USER_ID=${{ secrets.TEST_USER_ID }}
    python test_bot_flows.py
    python advanced_bot_tester.py
```

### Scheduled Testing

Set up a cron job to run tests regularly:

```bash
# Run tests daily at 2 AM
0 2 * * * cd /path/to/your/bot && python test_bot_flows.py
```

## 📈 Test Results Analysis

### Success Criteria

- All tests should pass
- No unhandled exceptions
- Response times under 5 seconds
- Proper error messages for invalid actions

### Performance Metrics

- Test execution time
- Success rate percentage
- Individual test durations
- Error patterns

## 🎯 Customizing Tests

### Adding New Tests

To add a new test, create a new method in the test class:

```python
async def test_new_feature(self):
    """Test new feature"""
    await self.send_message_and_capture("/new_command")
    await self.send_callback_and_capture("new_button")
    # Add assertions here
```

### Modifying Test Data

Update the test data in the test methods to match your bot's configuration:

```python
# Example: Update duration plan IDs
await self.send_callback_and_capture("duration_your_plan_id")
```

## 📞 Support

If you encounter issues with the testing suite:

1. Check the troubleshooting section above
2. Review the test reports for specific error messages
3. Verify your bot configuration matches the test expectations
4. Check that your bot is running and accessible

## 🔄 Updates

The testing suite is designed to be updated as your bot evolves:

- Add new test methods for new features
- Update expected responses when bot messages change
- Modify test data to match configuration changes
- Extend coverage for new edge cases

---

**Happy Testing! 🚀**
