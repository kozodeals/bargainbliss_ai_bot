#!/usr/bin/env python3
"""
Test version of the bot with the working API method
This uses the aliexpress.affiliate.product.query method that we confirmed works
"""

import os
import logging
import time
import hmac
import hashlib
import requests
import re
from urllib.parse import urlparse
from collections import defaultdict
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import Update

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load credentials from environment variables
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
API_KEY = os.getenv('AFFILIATE_API_KEY') or os.getenv('ALIBABA_API_KEY') or os.getenv('ALIEXPRESS_API_KEY')
SECRET_KEY = os.getenv('AFFILIATE_SECRET_KEY') or os.getenv('ALIBABA_SECRET_KEY') or os.getenv('ALIEXPRESS_SECRET_KEY')
TRACKING_ID = os.getenv('TRACKING_ID', 'c01b8d720c9941f5bfbef6686e96e90a')  # Your actual tracking ID

# Check if bot should be paused (for testing)
PAUSE_BOT = os.getenv('PAUSE_BOT', 'false').lower() == 'true'

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
    sorted_params = sorted(params.items())
    param_string = ''.join([f"{k}{v}" for k, v in sorted_params])
    
    signature = hmac.new(
        secret_key.encode('utf-8'),
        param_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest().upper()
    
    return signature

def expand_shortened_link(shortened_url):
    """Expand a shortened AliExpress link to get the actual product URL"""
    try:
        logger.info(f"Expanding shortened link: {shortened_url}")
        response = requests.get(shortened_url, allow_redirects=True, timeout=10)
        
        if response.status_code == 200:
            final_url = response.url
            logger.info(f"Expanded shortened link to: {final_url}")
            return final_url
        else:
            logger.error(f"Failed to expand shortened link. Status code: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error expanding shortened link: {e}")
        return None

def extract_product_id_from_url(url):
    """Extract product ID from AliExpress URL"""
    patterns = [
        r'/item/(\d+)\.html',
        r'product_id=(\d+)',
        r'item/(\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def generate_affiliate_link_new_api(product_url):
    """Generate affiliate link using the working API method"""
    try:
        # Check if it's a shortened link and expand it
        parsed_url = urlparse(product_url)
        shortened_patterns = [
            r'/e/_', r'/deeplink', r'/s/', r'/e/[a-zA-Z0-9]+',
        ]
        is_shortened_link = any(re.search(pattern, parsed_url.path) for pattern in shortened_patterns)

        if is_shortened_link:
            logger.info("Detected shortened affiliate link, expanding to get actual product URL")
            expanded_url = expand_shortened_link(product_url)
            if expanded_url:
                logger.info(f"Successfully expanded shortened link to: {expanded_url}")
                return generate_affiliate_link_new_api(expanded_url)  # Recursive call
            else:
                logger.error("Failed to expand shortened link")
                return None

        # Extract product ID
        product_id = extract_product_id_from_url(product_url)
        if not product_id:
            logger.error(f"Could not extract product ID from: {product_url}")
            return None

        logger.info(f"Extracted product ID: {product_id}")

        # Use the working API method
        api_url = 'https://api-sg.aliexpress.com/sync'
        
        params = {
            'app_key': API_KEY,
            'method': 'aliexpress.affiliate.product.query',
            'format': 'json',
            'v': '2.0',
            'sign_method': 'sha256',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
            'fields': 'product_id,product_title,target_sale_price,product_main_image_url,promotion_link,product_detail_url,product_origin,product_shipping,product_weight,product_dimensions,original_price,discount,product_rating,product_review_count,product_sales,product_shop_name,evaluate_rate,lastest_volume',
            'product_ids': product_id,
            'currency': 'ILS',
            'language': 'IL',
            'targetLanguage': 'IL',
            'isMultiLanguage': 'true',
            'locale': 'IL_IL',
            'ship_to_country': 'IL',
            'trackingId': TRACKING_ID,  # Use the correct parameter name
            'page_no': '1',
            'page_size': '1'
        }
        
        params['sign'] = generate_hmac_signature_upper(params, SECRET_KEY)
        
        logger.info(f"Making API request to: {api_url}")
        logger.info(f"Using API Key: {API_KEY[:8]}...")
        logger.info(f"Using Tracking ID: {TRACKING_ID}")
        
        response = requests.get(api_url, params=params, timeout=15)
        logger.info(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Response Data: {data}")
            
            if 'aliexpress_affiliate_product_query_response' in data:
                resp = data['aliexpress_affiliate_product_query_response']
                
                if 'resp_result' in resp:
                    resp_result = resp['resp_result']
                    # Check if resp_code is 0 (success) or 200 (success)
                    if resp_result.get('resp_code') in [0, 200]:  # Success
                        if 'result' in resp_result:
                            products_data = resp_result['result']['products']
                            products = products_data['product'] if isinstance(products_data['product'], list) else [products_data['product']]
                            
                            if products:
                                product = products[0]
                                promotion_link = product.get('promotion_link')
                                
                                if promotion_link:
                                    logger.info(f"✅ SUCCESS! Got real promotion link from API: {promotion_link}")
                                    return promotion_link
                                else:
                                    logger.error("❌ No promotion link in API response")
                                    return None
                            else:
                                logger.error("❌ No products found in API response")
                                return None
                        else:
                            logger.error("❌ No result in API response")
                            return None
                    else:
                        logger.error(f"❌ API Error: {resp_result.get('resp_msg', 'Unknown error')}")
                        return None
                else:
                    logger.error("❌ Invalid API response structure")
                    return None
            else:
                logger.error("❌ No aliexpress_affiliate_product_query_response in data")
                return None
        else:
            logger.error(f"❌ HTTP Error: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error making API request: {e}")
        return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages"""
    if PAUSE_BOT:
        await update.message.reply_text("🤖 **הבוט מושהה כרגע לתחזוקה**\n\nנסה שוב מאוחר יותר.")
        return

    # Check if it's a private chat
    if update.message.chat.type != 'private':
        await update.message.reply_text("⚠️ **הבוט עובד רק בצ'אט פרטי**\n\nאנא שלח לי הודעה פרטית כדי להשתמש בבוט.")
        return

    user_id = update.message.from_user.id
    
    # Rate limiting
    if not rate_limiter.is_allowed(user_id):
        await update.message.reply_text("⚠️ **יותר מדי בקשות**\n\nאנא המתן דקה לפני שתנסה שוב.")
        return

    message_text = update.message.text.strip()
    
    if not message_text:
        await update.message.reply_text("❌ **אנא שלח קישור AliExpress תקין**")
        return

    # Check if it's a valid AliExpress URL
    if not is_valid_aliexpress_url(message_text):
        await update.message.reply_text(
            "❌ **קישור לא תקין**\n\n"
            "אנא שלח קישור AliExpress תקין.\n"
            "דוגמאות:\n"
            "• https://www.aliexpress.com/item/1234567890.html\n"
            "• https://s.click.aliexpress.com/e/_opegQu9rmat"
        )
        return

    # Send processing message
    processing_msg = await update.message.reply_text("🔄 **מעבד את הקישור...**\n\nאנא המתן...")

    try:
        # Generate affiliate link using the new API method
        affiliate_link = generate_affiliate_link_new_api(message_text)
        
        if affiliate_link:
            # Success message
            success_message = (
                "✅ **קישור השותפים נוצר בהצלחה!**\n\n"
                f"🔗 **הקישור שלך:**\n{affiliate_link}\n\n"
                "📊 **מזהה מעקב:** {TRACKING_ID}\n\n"
                "💡 **טיפ:** העתק את הקישור ושלח אותו לחברים כדי להרוויח עמלות!"
            )
            await processing_msg.edit_text(success_message)
        else:
            # Error message
            error_message = (
                "❌ **נכשל ביצירת קישור השותפים**\n\n"
                "**סיבות אפשריות:**\n"
                "• המוצר לא זמין בתוכנית השותפים\n"
                "• שירות ה-API זמנית לא זמין\n"
                "• קישור מוצר לא תקין\n\n"
                "אנא נסה שוב או פנה לתמיכה."
            )
            await processing_msg.edit_text(error_message)
            
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        await processing_msg.edit_text(
            "❌ **שגיאה בעיבוד הקישור**\n\n"
            "אנא נסה שוב או פנה לתמיכה."
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    welcome_message = (
        "🎉 **ברוכים הבאים לבוט קישורי השותפים!**\n\n"
        "**איך להשתמש:**\n"
        "1. שלח לי קישור AliExpress\n"
        "2. אני אצור עבורך קישור שותפים\n"
        "3. שלח את הקישור לחברים והרווח עמלות!\n\n"
        "**תמיכה:** אם יש בעיות, פנה לתמיכה.\n\n"
        "תודה שהשתמשת בבוט! 🙏"
    )
    await update.message.reply_text(welcome_message)

def main():
    """Main function"""
    logger.info("Starting Telegram bot with new API method...")
    
    # Create application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start the bot
    logger.info("Bot started successfully!")
    application.run_polling()

if __name__ == "__main__":
    main() 