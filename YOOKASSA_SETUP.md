# Youkassa Payment Integration Setup

## Overview

The VPN bot now supports both cryptocurrency payments (via CryptoBot) and card payments (via Youkassa) in Russian rubles.

## Features

- **Dual Payment Options**: Users can choose between crypto (USDT) and card (RUB) payments
- **Real-time Payment Processing**: Automatic payment verification and subscription activation
- **Secure Integration**: Uses official Youkassa SDK for secure payment processing

## Setup Instructions

### 1. Get Youkassa Credentials

1. Register at [Youkassa](https://yookassa.ru/)
2. Create a shop in your Youkassa dashboard
3. Get your Shop ID and Secret Key from the dashboard

### 2. Configure Environment Variables

Add the following to your `.env` file:

```bash
# Youkassa Configuration
YOOKASSA_SHOP_ID=your_shop_id_here
YOOKASSA_SECRET_KEY=your_secret_key_here
```

### 3. Install Dependencies

The Youkassa SDK is already included in `requirements.txt`:

```bash
pip install -r requirements.txt
```

## Payment Flow

### User Experience

1. User runs `/subscribe`
2. Selects subscription duration (1 month, 3 months, 12 months)
3. **NEW**: Chooses payment method:
   - 💰 Crypto (USDT) - via CryptoBot
   - 💳 Card (RUB) - via Youkassa
4. Follows payment instructions
5. Confirms payment completion
6. Selects country package
7. Receives VPN access

### Payment Methods

#### Crypto Payment (USDT)

- Uses CryptoBot API
- Supports testnet/mainnet modes
- Real-time payment verification

#### Card Payment (RUB)

- Uses Youkassa payment gateway
- Secure card processing
- Automatic payment verification

## Pricing

Current pricing structure:

| Duration  | USDT Price | RUB Price |
| --------- | ---------- | --------- |
| 1 Month   | 0.10 USDT  | 10 ₽      |
| 3 Months  | 12.00 USDT | 1,200 ₽   |
| 12 Months | 40.00 USDT | 4,000 ₽   |

## Technical Implementation

### Key Files

- `payment_utils.py` - Payment processing functions
- `main.py` - Bot conversation handlers
- `config.py` - Configuration and pricing

### New Functions

- `get_yookassa_payment_details()` - Creates Youkassa payment
- `verify_yookassa_payment()` - Verifies payment status
- `get_yookassa_payment_status()` - Gets payment status

### Error Handling

- Graceful fallback for payment failures
- User-friendly error messages
- Comprehensive logging for debugging

## Testing

### Test Mode

For testing, you can use Youkassa's test environment:

1. Use test credentials from Youkassa dashboard
2. Test payments will not charge real money
3. All payment flows work identically to production

### Test Script

Run the test script to verify integration:

```bash
python test_yookassa.py
```

## Security Considerations

- All payment data is processed securely through Youkassa
- No sensitive payment information is stored locally
- Payment verification happens server-side
- HTTPS encryption for all API communications

## Troubleshooting

### Common Issues

1. **"Youkassa credentials not configured properly"**

   - Check your `.env` file has correct credentials
   - Verify Shop ID and Secret Key are correct

2. **Payment verification fails**

   - Check Youkassa dashboard for payment status
   - Verify webhook configuration (if using)

3. **Import errors**
   - Ensure `yookassa` package is installed
   - Check Python environment and dependencies

### Logs

Check logs for detailed error information:

```bash
tail -f bot.log
```

## Support

For technical support:

- Check Youkassa documentation: https://yookassa.ru/docs
- Review bot logs for error details
- Contact support if issues persist
