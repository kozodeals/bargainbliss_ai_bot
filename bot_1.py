import requests
import hashlib
import time
import re
import logging
import asyncio
import hmac
import socket
from collections import defaultdict
from urllib.parse import urlparse, urlencode
from dotenv import load_dotenv
from telegram import Update
import os

# Configure logging to output to both console and file
log_file = os.path.join(os.getcwd(), 'bot_debug.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Log script start
logger.info("Script started")

# Check python-telegram-bot version
try:
    import pkg_resources
    telegram_version = pkg_resources.get_distribution("python-telegram-bot").version
    logger.info(f"Using python-telegram-bot version: {telegram_version}")
except Exception as e:
    logger.error(f"Failed to check python-telegram-bot version: {e}")

# Load environment variables with debugging
env_path = os.path.join(os.getcwd(), '.env')
logger.info(f"Looking for .env file at: {env_path}")
if not os.path.exists(env_path):
    logger.error(".env file not found in current directory")
else:
    logger.info("Found .env file")
load_success = load_dotenv(env_path)
logger.info(f"load_dotenv() returned: {load_success}")

# Load credentials from environment variables
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
API_KEY = os.getenv('AFFILIATE_API_KEY') or os.getenv('ALIBABA_API_KEY') or os.getenv('ALIEXPRESS_API_KEY')
SECRET_KEY = os.getenv('AFFILIATE_SECRET_KEY') or os.getenv('ALIBABA_SECRET_KEY') or os.getenv('ALIEXPRESS_SECRET_KEY')
TRACKING_ID = os.getenv('TRACKING_ID', 'bargainbliss_ai_bot')

# Log environment variables (mask sensitive parts)
logger.info(f"TELEGRAM_TOKEN loaded: {bool(TELEGRAM_TOKEN)}")
logger.info(f"AFFILIATE_API_KEY loaded: {bool(API_KEY)}")
logger.info(f"AFFILIATE_SECRET_KEY loaded: {bool(SECRET_KEY)}")
logger.info(f"TRACKING_ID: {TRACKING_ID}")

# Validate required environment variables
missing_vars = []
if not TELEGRAM_TOKEN:
    missing_vars.append("TELEGRAM_TOKEN")
if not API_KEY:
    missing_vars.append("AFFILIATE_API_KEY")
if not SECRET_KEY:
    missing_vars.append("AFFILIATE_SECRET_KEY")
if missing_vars:
    logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
    logger.error(f"Current values - TELEGRAM_TOKEN: {bool(TELEGRAM_TOKEN)}, AFFILIATE_API_KEY: {bool(API_KEY)}, AFFILIATE_SECRET_KEY: {bool(SECRET_KEY)}")
    exit(1)
else:
    logger.info("All required environment variables loaded successfully")
    # Check API key format
    if API_KEY and len(API_KEY) < 6:
        logger.warning(f"AFFILIATE_API_KEY ({API_KEY}) is unusually short. Expected 6-10 digits or alphanumeric. Verify in openservice.aliexpress.com")

# Check if bot should be paused (for testing)
PAUSE_BOT = os.getenv('PAUSE_BOT', 'false').lower() == 'true'

# Import Telegram dependencies after env validation to avoid import errors
try:
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
except ImportError:
    Application = None
    from telegram.ext import Updater, CommandHandler, MessageHandler, Filters as filters
    ContextTypes = None
    logger.info("Using Updater (older python-telegram-bot version)")

class RateLimiter:
    def __init__(self, max_requests=60, time_window=60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = defaultdict(list)
    
    def is_allowed(self, user_id):
        now = time.time()
        user_requests = self.requests[user_id]
        
        # Remove old requests
        user_requests = [req for req in user_requests if now - req < self.time_window]
        self.requests[user_id] = user_requests
        
        if len(user_requests) >= self.max_requests:
            return False
            
        user_requests.append(now)
        return True

rate_limiter = RateLimiter()

def get_local_ip():
    """Get the local IP address used for outgoing requests"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Google's DNS server
        ip = s.getsockname()[0]
        s.close()
        logger.info(f"Local IP detected: {ip}")
        return ip
    except Exception as e:
        logger.error(f"Failed to get local IP: {e}")
        return "Unknown"

def get_public_ip():
    """Get the public IP address used for HTTP requests"""
    try:
        response = requests.get('https://api.ipify.org', timeout=5)
        if response.status_code == 200:
            ip = response.text
            logger.info(f"Public IP detected: {ip}")
            return ip
        else:
            logger.error(f"Failed to get public IP: HTTP {response.status_code}")
            return "Unknown"
    except Exception as e:
        logger.error(f"Failed to get public IP: {e}")
        return "Unknown"

def is_valid_aliexpress_url(url):
    """Validate AliExpress URLs more thoroughly"""
    try:
        parsed = urlparse(url)
        if not (parsed.netloc.endswith('.aliexpress.com') or parsed.netloc == 'aliexpress.com'):
            return False
        product_patterns = [
            r'/item/',
            r'/product/',
            r'/wholesale/'
        ]
        shortened_patterns = [
            r'/e/_',
            r'/deeplink',
            r'/s/',
        ]
        if any(re.search(pattern, parsed.path) for pattern in product_patterns):
            return True
        if any(re.search(pattern, parsed.path) for pattern in shortened_patterns):
            return True
        return False
    except:
        return False

def generate_hmac_signature_upper(params, secret_key):
    """Generate HMAC-SHA256 signature in uppercase for AliExpress API"""
    sorted_params = sorted(params.items())
    param_string = ''.join([f"{k}{v}" for k, v in sorted_params])
    signature = hmac.new(
        secret_key.encode('utf-8'),
        param_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest().upper()
    logger.info(f"Generated HMAC signature: {signature}")
    return signature

def generate_affiliate_link(product_url):
    """Generate affiliate link using AliExpress API"""
    logger.info(f"\n=== Generating affiliate link for URL: {product_url} ===")
    
    # Log IP addresses
    local_ip = get_local_ip()
    public_ip = get_public_ip()
    logger.info(f"Local IP: {local_ip}")
    logger.info(f"Public IP used for API request: {public_ip}")

    try:
        is_shortened_link = any(re.search(pattern, urlparse(product_url).path) for pattern in [
            r'/e/_', r'/deeplink', r'/s/'
        ])
        if is_shortened_link:
            logger.info("Detected shortened link; using directly in source_values")

        product_id_match = re.search(r'/item/(\d+)', urlparse(product_url).path)
        product_id = product_id_match.group(1) if product_id_match else None
        logger.info(f"Extracted product ID: {product_id or 'None'}")

        # Try multiple API endpoints
        api_endpoints = [
            'https://api-sg.aliexpress.com/sync',
            'http://gw.api.taobao.com/router/rest'
        ]

        api_methods = [
            {
                'name': 'aliexpress.affiliate.link.generate',
                'params': {
                    'app_key': API_KEY,
                    'method': 'aliexpress.affiliate.link.generate',
                    'format': 'json',
                    'v': '2.0',
                    'sign_method': 'sha256',
                    'timestamp': str(int(time.time() * 1000)),
                    'source_values': product_url,
                    'tracking_id': TRACKING_ID,
                    'promotion_link_type': '0'
                }
            },
            {
                'name': 'aliexpress.affiliate.productdetail.get (fallback)',
                'params': {
                    'app_key': API_KEY,
                    'method': 'aliexpress.affiliate.productdetail.get',
                    'format': 'json',
                    'v': '2.0',
                    'sign_method': 'sha256',
                    'timestamp': str(int(time.time() * 1000)),
                    'product_ids': product_id if product_id else product_url,
                    'tracking_id': TRACKING_ID,
                    'target_currency': 'USD',
                    'target_language': 'EN'
                }
            }
        ]

        for api_url in api_endpoints:
            logger.info(f"\n=== Trying API endpoint: {api_url} ===")
            for method in api_methods:
                try:
                    logger.info(f"Trying API method: {method['name']}")
                    
                    params = method['params'].copy()
                    params['sign'] = generate_hmac_signature_upper(params, SECRET_KEY)
                    
                    full_url = f"{api_url}?{urlencode(params)}"
                    logger.info(f"API Request URL: {full_url}")
                    
                    response = requests.get(api_url, params=params, timeout=10)
                    
                    logger.info(f"HTTP Status: {response.status_code}")
                    logger.info(f"Response Headers: {response.headers}")
                    try:
                        data = response.json()
                        logger.info(f"API Response JSON: {data}")
                    except ValueError:
                        logger.info(f"API Response Text (non-JSON): {response.text}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if 'error_response' in data:
                            logger.warning(f"API Error for {method['name']}: {data['error_response']}")
                            continue
                        
                        if 'aliexpress_affiliate_link_generate_response' in data:
                            resp = data['aliexpress_affiliate_link_generate_response']
                            if 'resp_result' in resp and 'result' in resp['resp_result']:
                                promotion_links = resp['resp_result']['result'].get('promotion_links', {}).get('promotion_link', [])
                                if promotion_links:
                                    promotion_link = promotion_links[0].get('promotion_link')
                                    if promotion_link:
                                        logger.info(f"Generated affiliate link via link.generate: {promotion_link}")
                                        return promotion_link
                        
                        elif 'aliexpress_affiliate_productdetail_get_response' in data:
                            resp = data['aliexpress_affiliate_productdetail_get_response']
                            if 'resp_result' in resp and 'result' in resp['resp_result']:
                                products = resp['resp_result']['result'].get('products', {}).get('product', [])
                                if products:
                                    promotion_link = products[0].get('promotion_link') or products[0].get('affiliate_product_url')
                                    if promotion_link:
                                        logger.info(f"Generated affiliate link via productdetail.get: {promotion_link}")
                                        return promotion_link
                    
                    else:
                        logger.warning(f"HTTP Error {response.status_code} for {method['name']}: {response.text}")
                        
                except Exception as e:
                    logger.error(f"Exception in {method['name']}: {e}")
                    continue
        
        logger.error("All API methods and endpoints failed to generate affiliate link")
        return None
        
    except Exception as e:
        logger.error(f"Unexpected error in generate_affiliate_link: {e}")
        return None

async def handle_message(update: Update, context):
    """Handle incoming messages with rate limiting and enhanced feedback"""
    user_id = update.effective_user.id
    message_text = update.message.text
    
    logger.info(f"Received message from user {user_id}: {message_text}")
    
    if update.effective_chat.type != "private":
        await update.message.reply_text(
            "❌ **בוט זה עובד רק בצ'אט פרטי**\n\n"
            "אנא שלח הודעה פרטית לבוט כדי להשתמש בו."
        )
        return
    
    if not rate_limiter.is_allowed(user_id):
        await update.message.reply_text(
            "⚠️ גבול הגבול חרג. אנא נסה שוב בדקה."
        )
        return
    
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, 
        action="typing"
    )
    
    if not is_valid_aliexpress_url(message_text):
        await update.message.reply_text(
            "❌ **פורמט URL לא תקין**\n\n"
            "אנא שלח קישור מוצר תקין מ-AliExpress.\n\n"
            "**דוגמאות:**\n"
            "• https://www.aliexpress.com/item/1234567890.html\n"
            "• https://m.aliexpress.com/item/1234567890.html\n"
            "• https://he.aliexpress.com/item/1234567890.html\n"
            "• https://us.aliexpress.com/item/1234567890.html\n"
            "• https://s.click.aliexpress.com/e/_opegQu9rmat\n\n"
            "**הערה:** כל תת-דומיין של AliExpress נתמך!"
        )
        return
    
    processing_msg = await update.message.reply_text("🔄 יוצר קישור שותפים...")
    
    affiliate_link = generate_affiliate_link(message_text)
    
    if affiliate_link:
        await processing_msg.edit_text(
            f"✅ **קישור השותפים נוצר!**\n\n"
            f"🔗 {affiliate_link}\n\n"
            f"💡 **שתף קישור זה כדי להרוויח עמלות על רכישות!**\n\n"
            f"📊 **מזהה מעקב:** {TRACKING_ID}"
        )
    else:
        await processing_msg.edit_text(
            "❌ **נכשל ביצירת קישור השותפים**\n\n"
            "**סיבות אפשריות:**\n"
            "• המוצר לא זמין בתוכנית השותפים\n"
            "• שירות ה-API זמנית לא זמין\n"
            "• קישור מוצר לא תקין\n\n"
            "אנא נסה שוב או השתמש ביוצר הקישורים הרשמי ב-portals.aliexpress.com."
        )

async def start(update: Update, context):
    """Welcome message with bot information in Hebrew"""
    logger.info("Received /start command")
    welcome_text = (
        "**ברוכים הבאים לבוט BargainBliss AI!**\n\n"
        "אני יכול להמיר קישורי AliExpress לקישורי שותפים עבורך.\n\n"
        "**איך להשתמש:**\n"
        "1. שלח לי כל קישור מוצר מ-AliExpress\n"
        "2. אני אצור קישור שותפים עם מעקב\n\n"
        "**דוגמה:**\n"
        "שלח: https://www.aliexpress.com/item/1234567890.html\n\n"
        "תודה שהשתמשת בבוט שלנו!"
    )
    await update.message.reply_text(welcome_text)

def test_api_connection():
    """Test the API connection"""
    logger.info("\n=== Starting API connection test ===")
    # Log IPs before making API call
    local_ip = get_local_ip()
    public_ip = get_public_ip()
    logger.info(f"Local IP before API test: {local_ip}")
    logger.info(f"Public IP before API test: {public_ip}")
    
    test_url = "https://www.aliexpress.com/item/1005006468625.html"
    logger.info(f"Testing with URL: {test_url}")
    result = generate_affiliate_link(test_url)
    
    if result:
        logger.info("✅ API connection successful")
        return True
    else:
        logger.error("❌ API connection failed")
        return False

def main():
    """Main function to start the bot"""
    logger.info("\n=== Starting BargainBliss AI Bot ===")
    
    if PAUSE_BOT:
        logger.info("Bot is paused due to PAUSE_BOT environment variable")
        logger.info("To resume, remove PAUSE_BOT=true from environment variables")
        return
    
    if not test_api_connection():
        logger.error("API connection failed. Check credentials and network.")
        logger.error("💡 If you see 'AppWhiteIpLimit' errors, update your AliExpress affiliate dashboard IP whitelist")
        return
    
    if Application:
        try:
            logger.info("Attempting to start bot with Application (v20+)")
            application = Application.builder().token(TELEGRAM_TOKEN).build()
            application.add_handler(CommandHandler("start", start))
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
            logger.info("Bot started successfully with Application!")
            application.run_polling(allowed_updates=Update.ALL_TYPES)
        except Exception as e:
            logger.error(f"Failed to start bot with Application: {e}")
            logger.error("Ensure python-telegram-bot is version 20.0 or higher. Run 'pip install --upgrade python-telegram-bot'")
    else:
        try:
            logger.info("Falling back to Updater (older version)")
            updater = Updater(token=TELEGRAM_TOKEN)
            dispatcher = updater.dispatcher
            dispatcher.add_handler(CommandHandler("start", start))
            dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
            logger.info("Bot started successfully with Updater!")
            updater.start_polling()
            updater.idle()
        except Exception as e:
            logger.error(f"Failed to start bot with Updater: {e}")
            logger.error("Ensure TELEGRAM_TOKEN is valid and network is accessible.")
            return

if __name__ == '__main__':
    main()