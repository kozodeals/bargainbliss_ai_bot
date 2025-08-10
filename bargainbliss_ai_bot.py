#!/usr/bin/env python3
"""
Telegram bot for generating AliExpress affiliate links
Updated with working API method
"""

import os
import logging
import time
import hmac
import hashlib
import aiohttp
import asyncio
import re
from urllib.parse import urlparse
from collections import defaultdict
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import Update
from message_manager import message_manager

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
# Note: AliExpress affiliate program may use Alibaba's API infrastructure
# Use your actual affiliate program credentials (could be AliExpress or Alibaba)
API_KEY = os.getenv('AFFILIATE_API_KEY') or os.getenv('ALIBABA_API_KEY') or os.getenv('ALIEXPRESS_API_KEY')
SECRET_KEY = os.getenv('AFFILIATE_SECRET_KEY') or os.getenv('ALIBABA_SECRET_KEY') or os.getenv('ALIEXPRESS_SECRET_KEY')
TRACKING_ID = os.getenv('TRACKING_ID', 'bargainbliss_ai_bot')  # Use human-readable tracking ID

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
        # First, clean the URL to remove common problematic characters
        cleaned_url = clean_url_for_validation(url)
        if not cleaned_url:
            return False
            
        parsed = urlparse(cleaned_url)
        
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
        
        # Check for shortened affiliate links - expanded to include more formats
        shortened_patterns = [
            r'/e/_',  # Shortened affiliate links like /e/_opegQu9rmat
            r'/deeplink',  # Deep link format
            r'/s/',  # Another shortened format
            r'/_[a-zA-Z0-9]+',  # New format like /_mrgRqdB
        ]
        
        # Check if it's a product URL
        if any(re.search(pattern, parsed.path) for pattern in product_patterns):
            return True
            
        # Check if it's a shortened affiliate link
        if any(re.search(pattern, parsed.path) for pattern in shortened_patterns):
            return True
            
        return False
    except Exception as e:
        logger.error(f"Error validating URL: {e}")
        return False

def clean_url_for_validation(url):
    """Clean URL for validation by removing problematic characters and encoding"""
    try:
        # Remove common problematic characters that might be invisible
        cleaned = url.strip()
        
        # Check for common problematic patterns
        problematic_patterns = [
            r'[\u200B-\u200D\uFEFF]',  # Zero-width spaces and other invisible characters
            r'[\u2028\u2029]',  # Line/paragraph separators
            r'[\u2060-\u2064]',  # Other invisible characters
            r'[\u00A0]',  # Non-breaking space
            r'[\u1680\u180E]',  # Other space characters
            r'[\u2000-\u200A]',  # Various space characters
            r'[\u205F]',  # Medium mathematical space
        ]
        
        for pattern in problematic_patterns:
            cleaned = re.sub(pattern, '', cleaned)
        
        # Remove any remaining control characters
        cleaned = ''.join(char for char in cleaned if ord(char) >= 32 or char in '\n\r\t')
        
        # Check if URL contains only printable ASCII characters (basic validation)
        try:
            cleaned.encode('ascii')
        except UnicodeEncodeError:
            logger.warning(f"URL contains non-ASCII characters after cleaning: {cleaned}")
            # Try to encode as UTF-8 and decode as ASCII, removing problematic chars
            try:
                cleaned = cleaned.encode('utf-8', errors='ignore').decode('ascii', errors='ignore')
            except:
                return None
        
        # Check for extremely long URLs (likely problematic)
        if len(cleaned) > 500:
            logger.warning(f"URL too long after cleaning ({len(cleaned)} characters): {cleaned[:100]}...")
            return None
        
        # Check for malformed URL structure
        if not cleaned.startswith(('http://', 'https://')):
            logger.warning(f"URL doesn't start with http/https after cleaning: {cleaned}")
            return None
        
        # Check for double encoding or other encoding issues
        if '%25' in cleaned or '%%' in cleaned:
            logger.warning(f"URL contains double encoding after cleaning: {cleaned}")
            return None
        
        # If we made changes, return the cleaned version
        if cleaned != url:
            logger.info(f"URL cleaned from '{url}' to '{cleaned}'")
        
        return cleaned
        
    except Exception as e:
        logger.error(f"Error cleaning URL for validation: {e}")
        return None

def extract_clean_product_url(url):
    """Extract a clean product URL that's safe for the API"""
    try:
        # First clean the URL
        cleaned_url = clean_url_for_validation(url)
        if not cleaned_url:
            return None
            
        # Parse the URL
        parsed = urlparse(cleaned_url)
        
        # Extract just the path without query parameters
        clean_path = parsed.path
        
        # Check if it's a product URL
        if '/item/' in clean_path:
            # Extract product ID
            match = re.search(r'/item/(\d+)', clean_path)
            if match:
                product_id = match.group(1)
                # Construct clean URL
                clean_url = f"{parsed.scheme}://{parsed.netloc}/item/{product_id}.html"
                logger.info(f"Extracted clean product URL: {clean_url}")
                return clean_url
        
        # If it's a shortened link, return as-is (will be expanded later)
        shortened_patterns = [
            r'/e/_', r'/deeplink', r'/s/', r'/_[a-zA-Z0-9]+'
        ]
        if any(re.search(pattern, clean_path) for pattern in shortened_patterns):
            return cleaned_url
            
        return None
        
    except Exception as e:
        logger.error(f"Error extracting clean product URL: {e}")
        return None

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

async def aliexpress_api_request(params):
    """Make API request to AliExpress with retry logic"""
    api_url = 'https://api-sg.aliexpress.com/sync'
    params['app_key'] = API_KEY
    params['sign_method'] = 'sha256'
    params['timestamp'] = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
    params['v'] = '2.0'
    params['sign'] = generate_hmac_signature_upper(params, SECRET_KEY)
    
    logger.info(f"Making API request to: {api_url}")
    logger.info(f"Using API Key: {API_KEY[:8]}...")
    logger.info(f"Using Tracking ID: {TRACKING_ID}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, params=params, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Response Data: {data}")
                    return data
                else:
                    logger.error(f"HTTP Error: {response.status}")
                    logger.error(f"Response: {await response.text()}")
                    return None
    except Exception as e:
        logger.error(f"Error making API request: {e}")
        return None

async def generate_affiliate_link(product_url):
    """Generate affiliate link directly from product URL"""
    try:
        # First, validate and clean the URL
        if not is_valid_aliexpress_url(product_url):
            logger.error(f"Invalid AliExpress URL: {product_url}")
            return None
            
        # Extract clean product URL
        clean_url = extract_clean_product_url(product_url)
        if not clean_url:
            logger.error(f"Could not extract clean product URL from: {product_url}")
            return None
            
        # Check if it's a shortened link and expand it
        parsed_url = urlparse(clean_url)
        shortened_patterns = [
            r'/e/_', r'/deeplink', r'/s/', r'/e/[a-zA-Z0-9]+',
            r'/_[a-zA-Z0-9]+',  # New format like /_mrgRqdB
        ]
        is_shortened_link = any(re.search(pattern, parsed_url.path) for pattern in shortened_patterns)

        if is_shortened_link:
            logger.info("Detected shortened affiliate link, expanding to get actual product URL")
            expanded_url = await expand_shortened_link(clean_url)
            if expanded_url:
                logger.info(f"Successfully expanded shortened link to: {expanded_url}")
                return await generate_affiliate_link(expanded_url)  # Recursive call
            else:
                logger.error("Failed to expand shortened link")
                return None

        # Use the correct human-readable tracking ID
        tracking_id = 'bargainbliss_ai_bot'
        
        # Generate short affiliate link directly from the clean product URL
        logger.info(f"Generating short affiliate link directly from URL: {clean_url}")
        short_link = await generate_short_affiliate_link(clean_url, tracking_id)
        if short_link:
            logger.info(f"✅ SUCCESS! Generated short affiliate link: {short_link}")
            return short_link
        else:
            logger.error("❌ Failed to generate short affiliate link")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error making API request: {e}")
        return None

async def generate_short_affiliate_link(product_url, tracking_id):
    """Generate short affiliate link using aliexpress.affiliate.link.generate"""
    
    # Use aliexpress.affiliate.link.generate to get short link
    params = {
        'method': 'aliexpress.affiliate.link.generate',
        'format': 'json',
        'source_values': product_url,
        'tracking_id': tracking_id,
        'promotion_link_type': '0',  # Changed from '1' to '0' for direct product links
        'target_currency': 'ILS',
        'target_language': 'IL'
    }
    
    response = await aliexpress_api_request(params)
    
    if response and 'aliexpress_affiliate_link_generate_response' in response:
        resp = response['aliexpress_affiliate_link_generate_response']
        if 'resp_result' in resp:
            resp_result = resp['resp_result']
            if resp_result.get('resp_code') in [0, 200]:
                if 'result' in resp_result and 'promotion_links' in resp_result['result']:
                    promotion_links = resp_result['result']['promotion_links'].get('promotion_link', [])
                    if promotion_links and len(promotion_links) > 0:
                        promotion_link = promotion_links[0].get('promotion_link')
                        if promotion_link:
                            logger.info(f"✅ Generated short affiliate link: {promotion_link}")
                            return promotion_link
        
    logger.error("❌ Failed to generate short affiliate link")
    return None

async def expand_shortened_link(shortened_url):
    """Expand a shortened AliExpress link to get the actual product URL"""
    try:
        logger.info(f"Expanding shortened link: {shortened_url}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(shortened_url, allow_redirects=True, timeout=10) as response:
                if response.status == 200:
                    final_url = str(response.url)
                    logger.info(f"Expanded shortened link to: {final_url}")
                    return final_url
                else:
                    logger.error(f"Failed to expand shortened link. Status code: {response.status}")
                    return None
    except Exception as e:
        logger.error(f"Error expanding shortened link: {e}")
        return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages"""
    if PAUSE_BOT:
        await update.message.reply_text(message_manager.get_message("bot_paused"), parse_mode='HTML')
        return

    # Check if it's a private chat
    if update.message.chat.type != 'private':
        await update.message.reply_text(message_manager.get_message("private_chat_only"), parse_mode='HTML')
        return

    user_id = update.message.from_user.id
    message_id = update.message.message_id
    
    # Add message ID logging to prevent duplicate processing
    logger.info(f"🆔 Processing message ID: {message_id} from user {user_id}")
    
    # Rate limiting
    if not rate_limiter.is_allowed(user_id):
        await update.message.reply_text(message_manager.get_message("rate_limit"), parse_mode='HTML')
        return

    message_text = update.message.text.strip()
    
    # Add debug logging for message processing
    logger.info(f"📨 Received message from user {user_id}: '{message_text}'")
    logger.info(f"📨 Message length: {len(message_text)}")
    logger.info(f"📨 Message bytes: {message_text.encode('utf-8')}")
    logger.info(f"📨 Message type: {type(message_text)}")
    
    # Check if user wants to try salvaged URL
    if message_text.lower() in ['כן', 'yes', 'y', 'ok', 'בסדר']:
        if 'salvaged_url' in context.user_data:
            salvaged_url = context.user_data['salvaged_url']
            del context.user_data['salvaged_url']  # Clear it after use
            
            # Send processing message
            processing_msg = await update.message.reply_text(message_manager.get_message("processing_salvaged"), parse_mode='HTML')
            
            try:
                # Generate affiliate link using the salvaged URL
                affiliate_link = await generate_affiliate_link(salvaged_url)
                
                if affiliate_link:
                    success_message = message_manager.get_message("affiliate_success", 
                        original_url=salvaged_url, 
                        affiliate_url=affiliate_link, 
                        tracking_id=TRACKING_ID
                    )
                    await processing_msg.edit_text(success_message, parse_mode='HTML')
                else:
                    error_message = message_manager.get_message("api_error")
                    await processing_msg.edit_text(error_message, parse_mode='HTML')
                    
            except Exception as e:
                logger.error(f"Error processing salvaged URL: {e}")
                await processing_msg.edit_text(message_manager.get_message("processing_error"), parse_mode='HTML')
            return
    
    if not message_text:
        await update.message.reply_text(message_manager.get_message("invalid_link"), parse_mode='HTML')
        return

    # Enhanced URL validation with detailed error messages
    validation_result = validate_aliexpress_url_detailed(message_text)
    if not validation_result['is_valid']:
        # Try to salvage the URL
        salvaged_url = try_salvage_url(message_text)
        if salvaged_url and salvaged_url != message_text:
            # If we have a salvaged URL that's different, validate it
            salvaged_validation = validate_aliexpress_url_detailed(salvaged_url)
            if salvaged_validation['is_valid']:
                # The salvaged URL is valid, proceed directly with it
                logger.info(f"✅ URL salvaged and validated, proceeding with: {salvaged_url}")
                
                # Send processing message
                processing_msg = await update.message.reply_text(message_manager.get_message("processing_salvaged"), parse_mode='HTML')
                
                try:
                    # Generate affiliate link using the salvaged URL
                    affiliate_link = await generate_affiliate_link(salvaged_url)
                    
                    if affiliate_link:
                        success_message = message_manager.get_message("affiliate_success", 
                            original_url=salvaged_url, 
                            affiliate_url=affiliate_link, 
                            tracking_id=TRACKING_ID
                        )
                        await processing_msg.edit_text(success_message, parse_mode='HTML')
                    else:
                        error_message = message_manager.get_message("api_error")
                        await processing_msg.edit_text(error_message, parse_mode='HTML')
                        
                except Exception as e:
                    logger.error(f"Error processing salvaged URL: {e}")
                    await processing_msg.edit_text(message_manager.get_message("processing_error"), parse_mode='HTML')
                return
            else:
                # Store the salvaged URL for later use
                context.user_data['salvaged_url'] = salvaged_url
                
                # Ask user if they want to try with the salvaged URL
                salvage_message = message_manager.get_message("salvage_question", 
                    original_url=message_text,
                    error_message=validation_result['error_message'],
                    salvaged_url=salvaged_url
                )
                await update.message.reply_text(salvage_message, parse_mode='HTML')
                return
        else:
            error_message = message_manager.get_message("validation_failed", 
                error_message=validation_result['error_message']
            )
            await update.message.reply_text(error_message, parse_mode='HTML')
            return

    # Send processing message
    processing_msg = await update.message.reply_text(message_manager.get_message("processing_url", url=message_text), parse_mode='HTML')

    try:
        # Generate affiliate link using the working API method
        affiliate_link = await generate_affiliate_link(message_text)
        
        if affiliate_link:
            # Success message with customized text
            success_message = message_manager.get_message("affiliate_success", 
                original_url=message_text, 
                affiliate_url=affiliate_link, 
                tracking_id=TRACKING_ID
            )
            await processing_msg.edit_text(success_message, parse_mode='HTML')
        else:
            # Error message
            error_message = message_manager.get_message("api_error")
            await processing_msg.edit_text(error_message, parse_mode='HTML')
            
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        await processing_msg.edit_text(message_manager.get_message("processing_error"), parse_mode='HTML')

def try_salvage_url(url):
    """Try to salvage a problematic URL by cleaning it"""
    try:
        logger.info(f"🔧 Attempting to salvage URL: '{url}'")
        
        # Remove common problematic characters
        cleaned = url.strip()
        logger.info(f"🔧 After strip: '{cleaned}'")
        
        # Remove invisible characters
        problematic_chars = ['\u200B', '\u200C', '\u200D', '\uFEFF', '\u2028', '\u2029']
        for char in problematic_chars:
            if char in cleaned:
                logger.info(f"🔧 Found problematic character: {repr(char)}")
                cleaned = cleaned.replace(char, '')
                logger.info(f"🔧 After removing {repr(char)}: '{cleaned}'")
        
        # Try to extract product ID from messy URLs
        product_id_match = re.search(r'/item/(\d+)', cleaned)
        if product_id_match:
            product_id = product_id_match.group(1)
            logger.info(f"🔧 Found product ID: {product_id}")
            # Try to construct a clean URL
            if 'aliexpress.com' in cleaned:
                salvaged = f"https://www.aliexpress.com/item/{product_id}.html"
                logger.info(f"🔧 Salvaged to: {salvaged}")
                return salvaged
        
        # Try to extract from shortened links
        shortened_match = re.search(r'(https?://[^/]+/[a-zA-Z0-9/_]+)', cleaned)
        if shortened_match:
            salvaged = shortened_match.group(1)
            logger.info(f"🔧 Salvaged shortened link: {salvaged}")
            return salvaged
        
        logger.info(f"🔧 Could not salvage URL")
        return None
        
    except Exception as e:
        logger.error(f"Error salvaging URL: {e}")
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    welcome_message = message_manager.get_message("start")
    await update.message.reply_text(welcome_message, parse_mode='HTML')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_message = message_manager.get_message("help")
    await update.message.reply_text(help_message, parse_mode='HTML')

async def tips_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /tips command"""
    tips_message = message_manager.get_message("tips")
    await update.message.reply_text(tips_message, parse_mode='HTML')

def test_api_connection():
    """Test API connection"""
    try:
        logger.info("Testing API connection...")
        # Add your API test logic here
        return True
    except Exception as e:
        logger.error(f"API connection test failed: {e}")
        return False

def validate_aliexpress_url_detailed(url):
    """Validate AliExpress URL and return detailed error information"""
    try:
        # Add debug logging
        logger.info(f"🔍 Validating URL: '{url}'")
        logger.info(f"🔍 URL length: {len(url)}")
        logger.info(f"🔍 URL starts with https://: {url.startswith('https://')}")
        logger.info(f"🔍 URL starts with http://: {url.startswith('http://')}")
        logger.info(f"🔍 URL bytes: {url.encode('utf-8')}")
        
        # First, try to clean the URL to remove invisible characters
        cleaned_url = clean_url_for_validation(url)
        if cleaned_url and cleaned_url != url:
            logger.info(f"🔍 URL cleaned from '{url}' to '{cleaned_url}'")
            # If cleaning helped, validate the cleaned version
            return validate_aliexpress_url_detailed(cleaned_url)
        
        # Check if URL is empty or too short
        if not url or len(url.strip()) < 10:
            logger.warning(f"URL too short or empty: '{url}'")
            return {
                'is_valid': False,
                'error_message': 'הקישור קצר מדי או ריק'
            }
        
        # Check if URL starts with http/https
        if not url.startswith(('http://', 'https://')):
            logger.warning(f"URL doesn't start with http/https: '{url}'")
            return {
                'is_valid': False,
                'error_message': 'הקישור חייב להתחיל ב-http:// או https://'
            }
        
        # Check for extremely long URLs
        if len(url) > 500:
            logger.warning(f"URL too long: {len(url)} characters")
            return {
                'is_valid': False,
                'error_message': 'הקישור ארוך מדי (מעל 500 תווים)'
            }
        
        # Check for problematic characters
        problematic_chars = ['\u200B', '\u200C', '\u200D', '\uFEFF', '\u2028', '\u2029']
        for char in problematic_chars:
            if char in url:
                logger.warning(f"URL contains problematic character: {repr(char)}")
                return {
                    'is_valid': False,
                    'error_message': 'הקישור מכיל תווים לא תקינים'
                }
        
        # Check for double encoding
        if '%25' in url or '%%' in url:
            logger.warning(f"URL contains double encoding")
            return {
                'is_valid': False,
                'error_message': 'הקישור מכיל קידוד כפול'
            }
        
        # Try to parse the URL
        try:
            parsed = urlparse(url)
            logger.info(f"🔍 Parsed URL - scheme: {parsed.scheme}, netloc: {parsed.netloc}, path: {parsed.path}")
        except Exception as e:
            logger.error(f"Failed to parse URL: {e}")
            return {
                'is_valid': False,
                'error_message': 'הקישור לא בפורמט תקין'
            }
        
        # Check domain
        if not (parsed.netloc.endswith('.aliexpress.com') or parsed.netloc == 'aliexpress.com'):
            logger.warning(f"URL domain not AliExpress: {parsed.netloc}")
            return {
                'is_valid': False,
                'error_message': 'הקישור חייב להיות מ-AliExpress'
            }
        
        # Check for product patterns
        product_patterns = [r'/item/', r'/product/', r'/wholesale/']
        shortened_patterns = [r'/e/_', r'/deeplink', r'/s/', r'/_[a-zA-Z0-9]+']
        
        has_product_pattern = any(re.search(pattern, parsed.path) for pattern in product_patterns)
        has_shortened_pattern = any(re.search(pattern, parsed.path) for pattern in shortened_patterns)
        
        logger.info(f"🔍 Has product pattern: {has_product_pattern}")
        logger.info(f"🔍 Has shortened pattern: {has_shortened_pattern}")
        
        if not (has_product_pattern or has_shortened_pattern):
            logger.warning(f"URL doesn't match product or shortened patterns: {parsed.path}")
            return {
                'is_valid': False,
                'error_message': 'הקישור חייב להיות למוצר או קישור מקוצר'
            }
        
        logger.info(f"✅ URL validation passed for: {url}")
        return {'is_valid': True, 'error_message': ''}
        
    except Exception as e:
        logger.error(f"Error in detailed URL validation: {e}")
        return {
            'is_valid': False,
            'error_message': 'שגיאה בבדיקת הקישור'
        }

def main():
    """Main function"""
    logger.info("Starting Telegram bot...")
    
    # Test API connection
    if not test_api_connection():
        logger.error("API connection test failed. Exiting.")
        return
    
    # Create application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("tips", tips_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start the bot
    logger.info("Bot started successfully!")
    application.run_polling()

if __name__ == "__main__":
    main()