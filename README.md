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

### 4. Render Free Tier Configuration (Optional)

If deploying on Render's free tier, add this environment variable to prevent sleep:

```env
# Keep-alive configuration for Render free tier
RENDER_EXTERNAL_URL=https://your-bot-name.onrender.com
```

**Note:** The bot automatically generates external traffic every 30 seconds to prevent Render from sleeping after 15 minutes of inactivity.

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

## Render Free Tier Keep-Alive Strategy

### How It Works
The bot implements a **bulletproof keep-alive strategy** specifically designed for Render's free tier limitations:

1. **External Traffic Generation**: Every 30 seconds, the bot generates external traffic to prevent sleep
2. **Primary Strategy**: Self-pings its own Render URL (most reliable)
3. **Fallback Strategy**: Pings external services if self-ping fails
4. **Sleep Prevention**: Keeps the service active 24/7 on Render's free tier

### Why This Works
- **Render's Rule**: Services sleep after 15 minutes without **external** traffic
- **Internal Traffic**: Localhost pings don't count as external traffic
- **External Traffic**: Self-pinging your own Render URL counts as external traffic
- **30-Second Intervals**: Ensures no gap longer than 15 minutes

### Environment Variables
```env
# Your Render service URL (auto-detected if not set)
RENDER_EXTERNAL_URL=https://your-bot-name.onrender.com
```

### Fallback Services
If self-ping fails, the bot automatically tries:
- `https://httpbin.org/get`
- `https://api.github.com/zen`
- `https://jsonplaceholder.typicode.com/posts/1`

### Monitoring
Check your logs for these messages:
- `🔄 Self-ping successful: https://your-bot.onrender.com`
- `🌐 External keep-alive successful: https://httpbin.org/get`
- `⚠️ Self-ping failed: [status_code]`

### Troubleshooting
- **Service still sleeping?** Check if `RENDER_EXTERNAL_URL` is set correctly
- **Keep-alive errors?** Check network connectivity and external service availability
- **Logs show failures?** The fallback services should handle temporary issues

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