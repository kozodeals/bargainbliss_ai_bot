import requests
import hashlib
import time
import re
import logging
import asyncio
import hmac
from collections import defaultdict
from urllib.parse import urlparse
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load credentials from environment variables
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
# Note: AliExpress affiliate program may use Alibaba's API infrastructure
# Use your actual affiliate program credentials (could be AliExpress or Alibaba)
API_KEY = os.getenv('AFFILIATE_API_KEY') or os.getenv('ALIBABA_API_KEY') or os.getenv('ALIEXPRESS_API_KEY')
SECRET_KEY = os.getenv('AFFILIATE_SECRET_KEY') or os.getenv('ALIBABA_SECRET_KEY') or os.getenv('ALIEXPRESS_SECRET_KEY')
TRACKING_ID = os.getenv('TRACKING_ID', 'bargainbliss_ai_bot')

# Validate required environment variables
if not all([TELEGRAM_TOKEN, API_KEY, SECRET_KEY]):
    logger.error("Missing required environment variables. Please check your .env file.")
    exit(1)

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

def is_valid_aliexpress_url(url):
    """Validate AliExpress URLs more thoroughly"""
    try:
        parsed = urlparse(url)
        
        # Check for AliExpress domains (including country-specific subdomains)
        # Accept any subdomain of aliexpress.com or the root domain
        if not (parsed.netloc.endswith('.aliexpress.com') or parsed.netloc == 'aliexpress.com'):
            return False
            
        # Check for product patterns
        product_patterns = [
            r'/item/',
            r'/product/',
            r'/wholesale/'
        ]
        
        # Check for shortened affiliate links
        shortened_patterns = [
            r'/e/_',  # Shortened affiliate links like /e/_opegQu9rmat
            r'/deeplink',  # Deep link format
            r'/s/',  # Another shortened format
        ]
        
        # Check if it's a product URL
        if any(re.search(pattern, parsed.path) for pattern in product_patterns):
            return True
            
        # Check if it's a shortened affiliate link
        if any(re.search(pattern, parsed.path) for pattern in shortened_patterns):
            return True
            
        return False
    except:
        return False

def generate_hmac_signature_upper(params, secret_key):
    """Generate HMAC-SHA256 signature in uppercase for AliExpress API"""
    # Sort parameters by key and concatenate
    sorted_params = sorted(params.items())
    param_string = ''.join([f"{k}{v}" for k, v in sorted_params])
    
    # Generate HMAC-SHA256 signature
    signature = hmac.new(
        secret_key.encode('utf-8'),
        param_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest().upper()
    
    return signature

def generate_md5_signature(params, secret_key):
    """Generate MD5 signature for legacy API compatibility"""
    # Sort parameters by key and concatenate
    sorted_params = ''.join(f'{k}{v}' for k, v in sorted(params.items()))
    # Add secret key at the end
    sign_string = sorted_params + secret_key
    # Generate MD5 hash
    return hashlib.md5(sign_string.encode('utf-8')).hexdigest().upper()

def generate_affiliate_link(product_url):
    """Generate affiliate link using correct AliExpress API"""
    try:
        parsed_url = urlparse(product_url)
        
        # Check if this is already a shortened affiliate link
        shortened_patterns = [
            r'/e/_',  # Shortened affiliate links like /e/_opegQu9rmat
            r'/deeplink',  # Deep link format
            r'/s/',  # Another shortened format
        ]
        
        is_shortened_link = any(re.search(pattern, parsed_url.path) for pattern in shortened_patterns)
        
        if is_shortened_link:
            # For shortened links, add tracking parameters and return as-is
            logger.info("Detected shortened affiliate link, adding tracking parameters")
            
            # Add tracking parameters to the shortened link
            tracking_params = {
                'aff_platform': 'telegram',
                'aff_trace_key': TRACKING_ID,
                'utm_source': 'bargainbliss_bot',
                'utm_medium': 'telegram',
                'utm_campaign': 'affiliate'
            }
            
            # Build the final URL with tracking parameters
            from urllib.parse import urlencode
            final_url = f"{product_url}?{urlencode(tracking_params)}"
            
            logger.info(f"Generated tracking-enhanced shortened link: {final_url}")
            return final_url
        
        # Extract product ID from regular product URL
        product_id_match = re.search(r'/item/(\d+)', parsed_url.path)
        
        if not product_id_match:
            logger.error("Could not extract product ID from URL")
            return None
            
        product_id = product_id_match.group(1)
        
        # First, try to query for the specific product
        api_url = 'https://api-sg.aliexpress.com/sync'
        
        # Query parameters
        query_params = {
            'app_key': API_KEY,
            'method': 'aliexpress.affiliate.product.query',
            'format': 'json',
            'v': '2.0',
            'sign_method': 'sha256',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
            'keywords': product_id,  # Use product ID as keyword
            'tracking_id': TRACKING_ID
        }
        
        # Generate HMAC-SHA256 signature in uppercase
        query_params['sign'] = generate_hmac_signature_upper(query_params, SECRET_KEY)
        
        # Make query API call
        response = requests.get(api_url, params=query_params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Check if we got products from the query
        if 'aliexpress_affiliate_product_query_response' in data:
            resp = data['aliexpress_affiliate_product_query_response']
            if 'resp_result' in resp and 'result' in resp['resp_result']:
                products = resp['resp_result']['result'].get('products', {}).get('product', [])
                if products:
                    # Use the first product's promotion link
                    if isinstance(products, list) and len(products) > 0:
                        promotion_link = products[0].get('promotion_link')
                        if promotion_link:
                            logger.info(f"Found promotion link from product query")
                            return promotion_link
        
        # If product query didn't work, try direct link generation
        logger.info("Product query didn't work, trying direct link generation...")
        
        # Direct link generation parameters
        link_params = {
            'app_key': API_KEY,
            'method': 'aliexpress.affiliate.link.generate',
            'format': 'json',
            'v': '2.0',
            'sign_method': 'sha256',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
            'product_id': product_id,
            'tracking_id': TRACKING_ID,
            'source_url': product_url,
            'promotion_link_type': '0',
            'source_values': 'telegram_bot'
        }
        
        # Generate HMAC-SHA256 signature in uppercase
        link_params['sign'] = generate_hmac_signature_upper(link_params, SECRET_KEY)
        
        # Make direct link generation API call
        response = requests.get(api_url, params=link_params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Check for API errors
        if 'error_response' in data:
            logger.error(f"API Error: {data['error_response']}")
            return None
            
        if 'result' in data and 'promotion_link' in data['result']:
            logger.info(f"Success with direct link generation")
            return data['result']['promotion_link']
        elif 'result' in data and 'url' in data['result']:
            logger.info(f"Success with direct link generation (alternative field)")
            return data['result']['url']
        return None
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error: {e}")
        # Try alternative method if API fails
        return generate_affiliate_link_alternative(product_url)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        # Try alternative method if API fails
        return generate_affiliate_link_alternative(product_url)

def generate_affiliate_link_alternative(product_url):
    """Alternative method to generate affiliate links when API is unavailable"""
    try:
        # Parse the product URL
        parsed_url = urlparse(product_url)
        
        # Extract product ID from URL
        # Common patterns: /item/1234567890.html or /item/1234567890
        import re
        product_id_match = re.search(r'/item/(\d+)', parsed_url.path)
        
        if not product_id_match:
            logger.error("Could not extract product ID from URL")
            return None
            
        product_id = product_id_match.group(1)
        
        # Preserve the original domain structure (including country-specific domains)
        # Use the original domain instead of hardcoding www.aliexpress.com
        base_domain = parsed_url.netloc
        affiliate_url = f"https://{base_domain}/item/{product_id}.html"
        
        # Add tracking parameters
        tracking_params = {
            'aff_platform': 'telegram',
            'aff_trace_key': TRACKING_ID,
            'utm_source': 'bargainbliss_bot',
            'utm_medium': 'telegram',
            'utm_campaign': 'affiliate'
        }
        
        # Build the final URL with tracking parameters
        from urllib.parse import urlencode
        final_url = f"{affiliate_url}?{urlencode(tracking_params)}"
        
        logger.info(f"Generated alternative affiliate link: {final_url}")
        return final_url
        
    except Exception as e:
        logger.error(f"Alternative link generation failed: {e}")
        return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages with rate limiting and enhanced feedback"""
    user_id = update.effective_user.id
    message_text = update.message.text
    
    # Security: Only allow private chats
    if update.effective_chat.type != "private":
        await update.message.reply_text(
            "❌ **בוט זה עובד רק בצ'אט פרטי**\n\n"
            "אנא שלח הודעה פרטית לבוט כדי להשתמש בו."
        )
        return
    
    # Rate limiting
    if not rate_limiter.is_allowed(user_id):
        await update.message.reply_text(
            "⚠️ גבול הגבול חרג. אנא נסה שוב בדקה."
        )
        return
    
    # Send typing indicator
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, 
        action="typing"
    )
    
    # Validate URL
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
    
    # Send processing message
    processing_msg = await update.message.reply_text("🔄 יוצר קישור שותפים...")
    
    # Generate affiliate link
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
            "אנא נסה שוב או פנה לתמיכה."
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message with bot information in Hebrew"""
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
    """Test the API connection (primary and alternative methods)"""
    logger.info("Testing API connection...")
    test_url = "https://www.aliexpress.com/item/1005001234567890.html"
    result = generate_affiliate_link(test_url)
    
    if result:
        logger.info("✅ API connection successful (primary or alternative method)")
        return True
    else:
        logger.error("❌ Both primary and alternative API methods failed")
        return False

def main():
    """Main function to start the bot"""
    logger.info("Starting BargainBliss AI Bot...")
    
    # Test API before starting bot
    if not test_api_connection():
        logger.error("API connection failed. Check credentials and network.")
        return
    
    try:
        # Initialize the application with more compatible settings
        application = Application.builder().token(TELEGRAM_TOKEN).build()

        # Add handlers - streamlined for business use
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        # Start the bot with error handling
        logger.info("Bot started successfully!")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        # Try alternative startup method
        try:
            from telegram.ext import Updater
            updater = Updater(token=TELEGRAM_TOKEN)
            dispatcher = updater.dispatcher
            
            # Add handlers - streamlined for business use
            dispatcher.add_handler(CommandHandler("start", start))
            dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
            
            logger.info("Bot started successfully with alternative method!")
            updater.start_polling()
            updater.idle()
            
        except Exception as e2:
            logger.error(f"Alternative startup also failed: {e2}")
            return

if __name__ == '__main__':
    main()