#!/usr/bin/env python3
"""
Telegram bot for generating AliExpress affiliate links
Updated with working API method and web interface

KEEP-ALIVE STRATEGY:
- Generates external traffic every 30 seconds to prevent Render free tier sleep
- Primary: Self-pings own Render URL (most reliable)
- Fallback: External service pings if self-ping fails
- Prevents 15-minute sleep timeout on Render free tier
"""

import os
import logging
import time
import hmac
import hashlib
import aiohttp
import asyncio
import re
import json
import secrets
from urllib.parse import urlparse
from collections import defaultdict
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import Update
from message_manager import message_manager
from aiohttp import web
import threading

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

# Keep-alive configuration for Render free tier
RENDER_EXTERNAL_URL = os.getenv('RENDER_EXTERNAL_URL', 'https://bargainbliss-ai-bot.onrender.com')

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
        
        # Check for extremely long URLs (increased limit for expanded AliExpress URLs)
        if len(cleaned) > 1000:  # Increased from 500 to 1000
            logger.warning(f"URL too long after cleaning ({len(cleaned)} characters): {cleaned[:100]}...")
            # For very long URLs, try to extract just the essential product part
            if 'aliexpress.com/item/' in cleaned:
                # Extract just the product ID and basic structure
                product_match = re.search(r'(https?://[^/]+/item/\d+\.html)', cleaned)
                if product_match:
                    cleaned = product_match.group(1)
                    logger.info(f"Extracted clean product URL from long URL: {cleaned}")
                else:
                    return None
            else:
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
                    logger.info(f"🔍 API Response Status: {response.status}")
                    logger.info(f"🔍 API Response Data: {data}")
                    
                    # Check if response contains error information
                    if 'error_response' in data:
                        logger.error(f"❌ API Error: {data['error_response']}")
                    elif 'aliexpress_affiliate_link_generate_response' in data:
                        logger.info(f"✅ API Success Response Structure Detected")
                    else:
                        logger.warning(f"⚠️ Unexpected API Response Structure: {list(data.keys())}")
                    
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
            logger.info(f"🎯 Sending SUCCESS response to user:")
            logger.info(f"   Original URL: {message_text}")
            logger.info(f"   Generated Affiliate Link: {affiliate_link}")
            logger.info(f"   Tracking ID: {TRACKING_ID}")
            await processing_msg.edit_text(success_message, parse_mode='HTML')
        else:
            # Error message
            error_message = message_manager.get_message("api_error")
            logger.error(f"❌ Failed to generate affiliate link for: {message_text}")
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

# Web server functions
async def check_auth(request):
    """Check if user is authenticated"""
    # Simple authentication check: check for a cookie named 'authenticated'
    return request.cookies.get('authenticated') == 'true'

async def require_auth(handler):
    """Decorator to require authentication"""
    async def wrapper(request):
        if not await check_auth(request):
            # Redirect to login page if not authenticated
            return web.HTTPFound('/login')
        return await handler(request)
    return wrapper

async def login_page(request):
    """Login page"""
    # If already logged in, redirect to messages
    if await check_auth(request):
        return web.HTTPFound('/messages')
    
    # Handle login form submission
    if request.method == 'POST':
        data = await request.post()
        username = data.get('username', '')
        password = data.get('password', '')
        
        # Get credentials from environment variables
        admin_username = os.getenv('ADMIN_USERNAME', 'admin')
        admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
        
        if username == admin_username and password == admin_password:
            # Set a cookie for authentication and redirect to messages
            response = web.HTTPFound('/messages')
            response.set_cookie('authenticated', 'true')
            response.set_cookie('username', username)
            logger.info(f"User {username} logged in successfully")
            return response
        else:
            error_msg = "Invalid username or password"
            return web.Response(
                text=login_html(error_msg),
                content_type='text/html'
            )
    
    # Show login form
    return web.Response(
        text=login_html(),
        content_type='text/html'
    )

async def logout(request):
    """Logout user"""
    # Invalidate the cookie and redirect to login
    response = web.HTTPFound('/login')
    response.delete_cookie('authenticated')
    response.delete_cookie('username')
    logger.info("User logged out")
    return response

async def messages_editor(request):
    """Message editor interface (protected)"""
    if not await check_auth(request):
        return web.HTTPFound('/login')
    
    username = request.cookies.get('username', 'Unknown')
    
    if request.method == 'POST':
        data = await request.post()
        action = data.get('action', '')
        
        if action == 'save_message':
            key = data.get('key', '')
            content = data.get('content', '')
            
            try:
                # Load current config
                with open('config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Update message
                if 'messages' in config:
                    config['messages'][key] = content
                    
                    # Save back to file
                    with open('config.json', 'w', encoding='utf-8') as f:
                        json.dump(config, f, ensure_ascii=False, indent=2)
                    
                    logger.info(f"Message '{key}' updated by user {username}")
                    success_msg = f"Message '{key}' saved successfully!"
                else:
                    success_msg = "Error: No messages section found in config"
                    
            except Exception as e:
                logger.error(f"Error saving message: {e}")
                success_msg = f"Error saving message: {str(e)}"
            
            return web.Response(
                text=messages_editor_html(success_msg),
                content_type='text/html'
            )
    
    # Show message editor
    return web.Response(
        text=messages_editor_html(),
        content_type='text/html'
    )

def login_html(error_msg=None):
    """Generate login page HTML"""
    error_html = f'<div class="alert alert-danger">{error_msg}</div>' if error_msg else ''
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>BargainBliss Bot - Login</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{ background-color: #f8f9fa; }}
            .login-container {{ max-width: 400px; margin: 100px auto; }}
            .card {{ border: none; border-radius: 15px; box-shadow: 0 0 20px rgba(0,0,0,0.1); }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="login-container">
                <div class="card">
                    <div class="card-body p-4">
                        <h3 class="text-center mb-4">🔐 Bot Login</h3>
                        {error_html}
                        <form method="POST">
                            <div class="mb-3">
                                <label for="username" class="form-label">Username</label>
                                <input type="text" class="form-control" id="username" name="username" required>
                            </div>
                            <div class="mb-3">
                                <label for="password" class="form-label">Password</label>
                                <input type="password" class="form-control" id="password" name="password" required>
                            </div>
                            <button type="submit" class="btn btn-primary w-100">Login</button>
                        </form>
                        <div class="text-center mt-3">
                            <small class="text-muted">BargainBliss AI Bot Admin</small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

def messages_editor_html(success_msg=None):
    """Generate message editor HTML"""
    try:
        # Load current messages
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        messages = config.get('messages', {})
    except Exception as e:
        messages = {}
        logger.error(f"Error loading config: {e}")
    
    success_html = f'<div class="alert alert-success">{success_msg}</div>' if success_msg else ''
    
    messages_html = ""
    for key, content in messages.items():
        messages_html += f"""
        <div class="card mb-3">
            <div class="card-header">
                <strong>{key}</strong>
            </div>
            <div class="card-body">
                <form method="POST">
                    <input type="hidden" name="action" value="save_message">
                    <input type="hidden" name="key" value="{key}">
                    <div class="mb-3">
                        <textarea class="form-control" name="content" rows="4" required>{content}</textarea>
                    </div>
                    <button type="submit" class="btn btn-primary btn-sm">Save Changes</button>
                </form>
            </div>
        </div>
        """
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>BargainBliss Bot - Message Editor</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{ background-color: #f8f9fa; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }}
        </style>
    </head>
    <body>
        <div class="header py-3 mb-4">
            <div class="container">
                <div class="d-flex justify-content-between align-items-center">
                    <h4 class="mb-0">📝 Message Editor</h4>
                    <div>
                        <a href="/logout" class="btn btn-outline-light btn-sm">Logout</a>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="container">
            {success_html}
            
            <div class="row">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="mb-0">Edit Bot Messages</h5>
                        </div>
                        <div class="card-body">
                            <p class="text-muted">Edit your bot's messages below. Changes are saved automatically.</p>
                            {messages_html}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

async def health_check(request):
    """Health check endpoint for Render"""
    return web.json_response({
        'status': 'healthy',
        'bot': 'running',
        'timestamp': time.time(),
        'service': 'BargainBliss AI Bot'
    })

async def status_page(request):
    """Status page showing bot information"""
    return web.json_response({
        'service': 'BargainBliss AI Bot',
        'status': 'operational',
        'uptime': time.time() - start_time if 'start_time' in globals() else 0,
        'features': [
            'AliExpress affiliate link generation',
            'URL validation and cleaning',
            'Rate limiting',
            'Multi-language support'
        ],
        'endpoints': {
            '/health': 'Health check for monitoring',
            '/status': 'Detailed status information',
            '/': 'This status page'
        }
    })

async def root_handler(request):
    """Root endpoint"""
    return web.json_response({
        'message': 'BargainBliss AI Bot is running!',
        'endpoints': {
            '/health': 'Health check for Render',
            '/status': 'Status information',
            '/login': 'Secure login page',
            '/messages': 'Message editor (requires login)'
        },
        'note': 'Use /login to access the message editor'
    })

async def start_web_server():
    """Start the web server"""
    app = web.Application()
    
    # Add routes
    app.router.add_get('/', root_handler)
    app.router.add_get('/health', health_check)
    app.router.add_get('/status', status_page)
    app.router.add_get('/login', login_page)
    app.router.add_post('/login', login_page)
    app.router.add_get('/logout', logout)
    app.router.add_get('/messages', messages_editor)
    app.router.add_post('/messages', messages_editor)
    
    # Get port from environment or use default
    port = int(os.getenv('PORT', 8080))
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    
    logger.info(f"🌐 Starting web server on port {port}")
    await site.start()
    logger.info(f"✅ Web server started successfully on port {port}")
    
    # Show helpful URLs
    logger.info("🔗 Available endpoints:")
    logger.info(f"   • Health check: http://localhost:{port}/health")
    logger.info(f"   • Status page: http://localhost:{port}/status")
    logger.info(f"   • Login page: http://localhost:{port}/login")
    logger.info(f"   • Message editor: http://localhost:{port}/messages")
    logger.info("🔐 Default login credentials: admin / admin123")
    logger.info("💡 Set ADMIN_USERNAME and ADMIN_PASSWORD environment variables to change credentials")
    
    # Log the external keep-alive strategy
    logger.info(f"🔄 External keep-alive strategy: Self-ping {RENDER_EXTERNAL_URL} every 30 seconds")
    logger.info(f"🔄 Fallback: External services if self-ping fails")
    
    # Keep the server running
    while True:
        await asyncio.sleep(1)

async def keep_alive_ping():
    """Generate external traffic to prevent Render from sleeping (bulletproof solution)"""
    while True:
        try:
            # Wait 30 seconds between pings (optimal for Render's 15-minute sleep threshold)
            await asyncio.sleep(30)  # 30 seconds
            
            # Strategy 1: Self-ping our own external Render URL (most reliable)
            render_url = RENDER_EXTERNAL_URL
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{render_url}/health", timeout=10) as response:
                        if response.status == 200:
                            logger.info(f"🔄 Self-ping successful: {render_url}")
                            continue  # Success, move to next cycle
                        else:
                            logger.warning(f"⚠️ Self-ping failed: {response.status}")
            except Exception as e:
                logger.warning(f"⚠️ Self-ping error: {e}")
                
                # Strategy 2: Fallback to external services if self-ping fails
                external_services = [
                    "https://httpbin.org/get",
                    "https://api.github.com/zen",
                    "https://jsonplaceholder.typicode.com/posts/1"
                ]
                
                for service in external_services:
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(service, timeout=10) as response:
                                if response.status == 200:
                                    logger.info(f"🌐 External keep-alive successful: {service}")
                                    break  # One success is enough
                    except Exception as e:
                        logger.warning(f"⚠️ External service {service} failed: {e}")
                        continue
                    
        except Exception as e:
            logger.error(f"❌ Keep-alive loop error: {e}")
            await asyncio.sleep(10)  # Quick retry on errors

def main():
    """Main function"""
    global start_time
    start_time = time.time()
    
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
    
    # Run both bot and web server concurrently
    async def run_both():
        try:
            # Start web server FIRST and wait for it to be ready
            logger.info("🚀 Starting web server first...")
            web_task = asyncio.create_task(start_web_server())
            
            # Wait a moment for web server to fully start
            await asyncio.sleep(2)
            logger.info("✅ Web server should now be ready")
            
            # Start keep-alive ping task
            logger.info("🔄 Starting keep-alive ping...")
            keep_alive_task = asyncio.create_task(keep_alive_ping())
            
            # Start bot
            logger.info("🤖 Starting Telegram bot...")
            await application.initialize()
            await application.start()
            await application.updater.start_polling()
            
            logger.info("✅ Both bot and web server are now running!")
            logger.info("🤖 Bot is listening for Telegram messages...")
            logger.info("🌐 Web server is running for message editing...")
            logger.info("🔄 Keep-alive ping is active (prevents sleep)")
            
            # Keep all tasks running
            await asyncio.gather(
                web_task,
                keep_alive_task,
                return_exceptions=True
            )
            
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            # Clean shutdown
            try:
                await application.updater.stop()
                await application.stop()
                await application.shutdown()
            except Exception as e:
                logger.error(f"Error during shutdown: {e}")
    
    # Run the async event loop
    try:
        asyncio.run(run_both())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")

if __name__ == "__main__":
    main()