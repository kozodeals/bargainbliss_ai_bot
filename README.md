# BargainBliss AI Bot

A Telegram bot that converts AliExpress product URLs into affiliate links with tracking capabilities.

## Features

- ✅ **Secure**: Environment-based configuration
- ✅ **Robust**: Enhanced error handling and rate limiting
- ✅ **User-friendly**: Rich feedback and status messages
- ✅ **Reliable**: API connection testing and health checks
- ✅ **Scalable**: Rate limiting (60 requests/hour per user)

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the project root with the following variables:

```env
# Telegram Bot Configuration
TELEGRAM_TOKEN=your_telegram_bot_token_here

# Affiliate Program Configuration
# Note: AliExpress affiliate program may use Alibaba's API infrastructure
# Use your actual affiliate program credentials from your affiliate dashboard
AFFILIATE_API_KEY=your_affiliate_api_key_here
AFFILIATE_SECRET_KEY=your_affiliate_secret_key_here
TRACKING_ID=bargainbliss_ai_bot

# Alternative naming (also supported):
# ALIBABA_API_KEY=your_api_key_here
# ALIBABA_SECRET_KEY=your_secret_key_here
# or
# ALIEXPRESS_API_KEY=your_api_key_here
# ALIEXPRESS_SECRET_KEY=your_secret_key_here
```

### 3. Get Your Credentials

#### Telegram Bot Token
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Create a new bot with `/newbot`
3. Copy the token provided

#### Alibaba API Credentials
1. Register for Alibaba Affiliate Program
2. Get your API Key and Secret Key
3. Set up your tracking ID

### 4. Run the Bot

```bash
python bargainbliss_ai_bot.py
```

## Usage

### Commands
- `/start` - Welcome message and instructions
- `/health` - Check bot and API status
- `/help` - Show help information

### How to Use
1. Send any AliExpress product URL to the bot
2. The bot will generate an affiliate link with tracking
3. Share the generated link to earn commissions

### Supported URL Formats
- `https://www.aliexpress.com/item/...`
- `https://m.aliexpress.com/item/...`
- `https://aliexpress.com/item/...`

## Features

### Security
- Environment variable configuration
- Input validation and sanitization
- Rate limiting to prevent abuse

### Error Handling
- Network timeout handling
- API error detection
- Graceful failure messages

### User Experience
- Typing indicators
- Processing status messages
- Rich formatting with emojis
- Clear error messages

### Monitoring
- Comprehensive logging
- Health check functionality
- API connection testing

## Rate Limits

- **60 requests per hour** per user
- Automatic rate limiting with user feedback
- Prevents API abuse and ensures fair usage

## Troubleshooting

### Common Issues

1. **"Missing required environment variables"**
   - Check your `.env` file exists and has all required variables

2. **"API connection failed"**
   - Verify your Alibaba API credentials
   - Check your internet connection
   - Ensure API service is available

3. **"Rate limit exceeded"**
   - Wait a minute before trying again
   - Limit is 60 requests per hour per user

### Logs

The bot logs all activities to help with debugging:
- API calls and responses
- User interactions
- Error messages
- System status

## Development

### Project Structure
```
bargainbliss_ai_bot/
├── bargainbliss_ai_bot.py    # Main bot file
├── requirements.txt           # Python dependencies
├── README.md                 # This file
└── .env                      # Environment variables (create this)
```

### Key Components

- **RateLimiter**: Manages user request limits
- **URL Validation**: Ensures valid AliExpress URLs
- **API Integration**: Handles Alibaba API calls
- **Error Handling**: Comprehensive error management
- **User Feedback**: Rich messaging system

## License

This project is for educational and commercial use. Ensure compliance with Alibaba's affiliate program terms and Telegram's bot policies.

## Support

For issues or questions:
1. Check the logs for error messages
2. Use `/health` command to test bot status
3. Verify your credentials are correct
4. Contact the bot administrator for additional support 