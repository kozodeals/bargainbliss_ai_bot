#!/usr/bin/env python3
"""
Modified AliExpress Bot that saves posts to queue instead of posting directly
"""

import asyncio
import json
import logging
import sys
import os
import requests
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from datetime import datetime
from src.database_queue import PostQueueDatabase
from src.hebrew_translations import get_hebrew_title
from utils import (
    RateLimiter, HealthMonitor, DataValidator, GracefulShutdown,
    retry_with_backoff, validate_config, setup_logging
)

# Setup structured logging
setup_logging(level="DEBUG")

def select_account():
    """Connect to database and let user select an account"""
    try:
        # Create a temporary database connection to get accounts
        temp_db = PostQueueDatabase()
        accounts = temp_db.get_accounts()
        temp_db.close()
        
        if not accounts:
            print("No accounts found in database.")
            return None
        
        print("\nAvailable accounts:")
        for i, account in enumerate(accounts, 1):
            print(f"{i}. {account['account_name']} ({account['account_id']})")
        
        while True:
            try:
                choice = input("\nSelect account number: ").strip()
                choice_num = int(choice)
                if 1 <= choice_num <= len(accounts):
                    selected_account = accounts[choice_num - 1]
                    print(f"Selected account: {selected_account['account_name']} ({selected_account['account_id']})")
                    return selected_account['account_id']
                else:
                    print(f"Please enter a number between 1 and {len(accounts)}")
            except ValueError:
                print("Please enter a valid number")
            except KeyboardInterrupt:
                print("\nExiting...")
                return None
    
    except Exception as e:
        logging.error(f"Error connecting to database: {e}")
        return None

class PostQueueBot:
    """AliExpress Bot that saves posts to queue for manual review"""
    
    def __init__(self, config_file="config.json", account_id=None):
        # Validate config first
        self.config = self.load_config(config_file)
        validate_config(self.config)
        
        # If no account_id provided, let user select one
        if account_id is None:
            account_id = select_account()
            if account_id is None:
                raise ValueError("No account selected")
        
        self.account_id = account_id
        self.db = PostQueueDatabase(config_file, account_id)
        self.credentials = None
        self.load_credentials()
        
        # Initialize rate limiter (10 requests per minute for AliExpress API)
        self.rate_limiter = RateLimiter(max_requests=10, time_window=60)
        
        # Initialize health monitor
        self.health_monitor = HealthMonitor()
        
        # Initialize data validator
        self.validator = DataValidator()
        
        # Initialize graceful shutdown handler (only if not in web context)
        self.shutdown_requested = False
        import threading
        if threading.current_thread() is threading.main_thread():
            # We're in the main thread, safe to use signal handlers
            self.shutdown_handler = GracefulShutdown(self)
            logging.info("Running in standalone context - signal handlers enabled")
        else:
            # We're in a worker thread (web context), skip signal handlers
            self.shutdown_handler = None
            logging.info("Running in web context - skipping signal handlers")
        
        # Load settings from database with fallback to config
        self.keyword_sleep = int(self.db.get_setting('keyword_sleep', self.config['bot_settings']['keyword_sleep']))
        self.cycle_sleep = int(self.db.get_setting('cycle_sleep', self.config['bot_settings']['cycle_sleep']))
        self.error_sleep = int(self.db.get_setting('error_sleep', self.config['bot_settings']['error_sleep']))
        self.debug_full_response = self.db.get_setting('debug_full_response', str(self.config['bot_settings']['debug_full_response'])).lower() == 'true'
        
        # Create queue tables
        self.db.create_queue_tables()
        
        logging.info(f"🔄 Post Queue Bot initialized for account: {self.account_id}")
        logging.info("📋 Posts will be saved to queue for manual translation review")
    
    def load_config(self, config_file):
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.error(f"Config file {config_file} not found!")
            raise
    
    def load_credentials(self):
        """Load credentials from database"""
        self.credentials = self.db.get_credentials()
        if not self.credentials:
            logging.error(f"No credentials found in database for account: {self.account_id}")
            raise ValueError("No credentials found")
        
        logging.info(f"Credentials loaded successfully for account: {self.account_id}")
    
    def generate_signature(self, params, secret, sign_method="sha256"):
        """Generate API signature"""
        import hmac
        import hashlib
        
        sorted_params = sorted(params.items())
        sign_string = "".join(f"{k}{v}" for k, v in sorted_params)
        hash_algorithm = hashlib.sha256 if sign_method.lower() == "sha256" else hashlib.md5
        return hmac.new(secret.encode(), sign_string.encode(), hash_algorithm).hexdigest().upper()
    
    async def aliexpress_api_request(self, params, retries=3, backoff=2):
        """Make API request to AliExpress with rate limiting and retry logic"""
        # Wait for rate limiter
        await self.rate_limiter.acquire()
        
        import time
        import urllib.parse
        
        base_url = self.config['aliexpress']['base_url']
        params["app_key"] = self.credentials['api_key']
        params["timestamp"] = int(time.time() * 1000)
        params["sign_method"] = "sha256"
        params["sign"] = self.generate_signature(params, self.credentials['api_secret'], params["sign_method"])
        url = f"{base_url}?" + urllib.parse.urlencode(params)
        
        async def make_request():
            # Check for shutdown before making request
            if self.shutdown_requested:
                logging.info("Shutdown requested during API call, aborting request")
                return None
                
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            return response
        
        try:
            # Use retry with backoff
            response = await retry_with_backoff(make_request, max_retries=retries, base_delay=backoff)
            
            # Check for shutdown after request
            if self.shutdown_requested:
                logging.info("Shutdown requested after API call, aborting processing")
                return None
                
            if response is None:
                return None
                
            raw_response = response.text
            
            if self.debug_full_response:
                logging.debug(f"Full API response (method: {params.get('method', 'unknown')}): {raw_response}")
            else:
                logging.debug(f"API response (method: {params.get('method', 'unknown')}): {raw_response[:500]}")
            
            if raw_response.strip().startswith("<!DOCTYPE html"):
                logging.warning(f"Maintenance page detected. Waiting {self.error_sleep} seconds.")
                self.health_monitor.record_api_call(success=False, method=params.get('method', 'unknown'))
                return {"maintenance": True}
            
            try:
                data = response.json()
                
                # Validate API response
                if not self.validator.validate_api_response(data):
                    logging.error(f"Invalid API response structure: {data}")
                    self.health_monitor.record_api_call(success=False, method=params.get('method', 'unknown'))
                    return None
                
                if "error_response" in data:
                    code = data["error_response"].get("code")
                    if code == "AppWhiteIpLimit":
                        logging.error(f"IP Whitelist error. Waiting {self.error_sleep} seconds.")
                        self.health_monitor.record_error(f"IP Whitelist error: {code}", "api_error")
                        return {"ip_whitelist_error": True}
                    if code == "InvalidApiPath":
                        logging.error(f"Invalid API path error. URL: {url}")
                        self.health_monitor.record_error(f"Invalid API path: {code}", "api_error")
                        return None
                
                if "aliexpress_affiliate_product_query_response" in data or "aliexpress_affiliate_link_generate_response" in data:
                    self.health_monitor.record_api_call(success=True, method=params.get('method', 'unknown'))
                    return data
                
                self.health_monitor.record_api_call(success=False, method=params.get('method', 'unknown'))
                return None
                
            except ValueError as e:
                logging.error(f"JSON parsing error: {str(e)}. Response: {raw_response[:500]}")
                self.health_monitor.record_error(f"JSON parsing error: {str(e)}", "parsing_error")
                return None
                
        except Exception as e:
            logging.error(f"API request error: {str(e)}")
            self.health_monitor.record_error(f"API request error: {str(e)}", "request_error")
            raise
    
    async def generate_affiliate_link(self, product_url):
        """Generate affiliate link for a product"""
        base_url = product_url.split('?')[0] if '?' in product_url else product_url
        params = {
            "method": "aliexpress.affiliate.link.generate",
            "promotion_link_type": self.config['aliexpress']['promotion_link_type'],
            "source_values": base_url,
            "tracking_id": self.credentials['tracking_id'],
            "format": "json",
            "target_currency": self.credentials['currency'],
            "target_language": self.credentials['language']
        }
        
        response = await self.aliexpress_api_request(params)
        if response and "aliexpress_affiliate_link_generate_response" in response:
            link_data = response["aliexpress_affiliate_link_generate_response"]["resp_result"]
            if "result" in link_data and "promotion_links" in link_data["result"]:
                promotion_links = link_data["result"]["promotion_links"]["promotion_link"]
                if isinstance(promotion_links, list) and promotion_links:
                    link = promotion_links[0]["promotion_link"]
                    logging.debug(f"Generated affiliate link: {link}")
                    return link
        
        logging.error(f"Failed to generate affiliate link for {product_url}")
        return base_url
    
    def safe_float_conversion(self, value, default=0.0):
        """Safely convert a value to float, handling strings with '%' symbols"""
        if value is None:
            return default
        
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            # Remove '%' symbol and any other non-numeric characters except decimal point
            cleaned = value.replace('%', '').replace(',', '').strip()
            try:
                return float(cleaned)
            except ValueError:
                return default
        
        return default

    async def get_products(self, keyword, max_price):
        """Fetch products from AliExpress with advanced filtering and optimization"""
        try:
            # Get advanced filtering settings
            min_discount = self.safe_float_conversion(self.db.get_setting('min_discount_percentage', 15.0))
            min_rating = self.safe_float_conversion(self.db.get_setting('min_product_rating', 4.0))
            min_sales = int(self.db.get_setting('min_product_sales', 5))
            min_quantity = int(self.db.get_setting('min_quantity_sold', 200))  # New: minimum quantity sold
            
            # Enhanced keyword processing
            enhanced_keywords = self.enhance_keyword(keyword)
            
            logging.info(f"🔍 Searching with enhanced keywords: {enhanced_keywords}")
            
            params = {
                "fields": "product_id,product_title,target_sale_price,product_main_image_url,promotion_link,product_detail_url,product_origin,product_weight,product_dimensions,original_price,discount,product_rating,product_review_count,product_sales,product_shop_name,evaluate_rate,lastest_volume",
                "keywords": enhanced_keywords,
                "max_sale_price": max_price,
                "currency": "ILS",  # Force ILS currency
                "language": "IL",   # Force Hebrew language (official AliExpress code)
                "targetLanguage": "IL",  # Add target language for Hebrew (official AliExpress code)
                "isMultiLanguage": "true",  # Enable multi-language support
                "locale": "IL_IL",  # Add locale parameter
                "ship_to_country": self.config['aliexpress']['ship_to_country'],
                "tracking_id": self.credentials['tracking_id'],
                "method": "aliexpress.affiliate.product.query"
            }
            
            response = await self.aliexpress_api_request(params)
            if response and "aliexpress_affiliate_product_query_response" in response:
                products_data = response["aliexpress_affiliate_product_query_response"]["resp_result"]["result"]["products"]
                products = products_data["product"] if isinstance(products_data["product"], list) else [products_data["product"]]
                
                # Convert USD prices to ILS if needed
                for product in products:
                    if product.get('target_sale_price_currency') == 'USD':
                        usd_price = self.safe_float_conversion(product.get('target_sale_price', 0))
                        ils_price = usd_price * 3.7  # Approximate USD to ILS conversion
                        product['target_sale_price'] = round(ils_price, 2)
                        product['target_sale_price_currency'] = 'ILS'
                    
                    # Also convert original_price if it's in USD
                    if product.get('original_price_currency') == 'USD':
                        usd_original = self.safe_float_conversion(product.get('original_price', 0))
                        ils_original = usd_original * 3.7  # Approximate USD to ILS conversion
                        product['original_price'] = round(ils_original, 2)
                        product['original_price_currency'] = 'ILS'
                
                # Pre-filter products before validation
                pre_filtered_products = []
                for product in products:
                    # Quick pre-filtering for performance
                    original_price = self.safe_float_conversion(product.get('original_price', 0))
                    sale_price = self.safe_float_conversion(product.get('target_sale_price', 0))
                    
                    # Skip products without meaningful discounts
                    if original_price <= sale_price:
                        continue
                    
                    # Handle discount percentage - it might come as a string with '%' symbol
                    discount_value = product.get('discount', 0)
                    logging.debug(f"Processing discount value: {discount_value} (type: {type(discount_value)})")
                    if isinstance(discount_value, str):
                        # Remove '%' symbol and convert to float
                        discount_value = discount_value.replace('%', '').strip()
                        logging.debug(f"After removing '%': {discount_value}")
                        try:
                            discount_percentage = self.safe_float_conversion(discount_value)
                            logging.debug(f"Successfully parsed discount: {discount_percentage}")
                        except ValueError as e:
                            logging.warning(f"Failed to parse discount '{discount_value}', calculating from prices: {e}")
                            # If we can't parse the discount, calculate it from prices
                            discount_percentage = round(((original_price - sale_price) / original_price) * 100, 1)
                    else:
                        discount_percentage = round(((original_price - sale_price) / original_price) * 100, 1)
                    
                    if discount_percentage < min_discount:
                        continue
                    
                    # Skip products with low ratings (if available)
                    rating = self.safe_float_conversion(product.get('evaluate_rate', 0))
                    if rating > 0 and rating < min_rating:
                        continue
                    
                    # Skip products with low sales (if available)
                    sales = int(self.safe_float_conversion(product.get('lastest_volume', 0)))
                    if sales > 0 and sales < min_sales:
                        continue
                    
                    # Skip products with low quantity sold (if available)
                    quantity = int(self.safe_float_conversion(product.get('lastest_volume', 0)))
                    if quantity > 0 and quantity < min_quantity:
                        continue
                    
                    pre_filtered_products.append(product)
                
                logging.info(f"📊 Pre-filtered {len(pre_filtered_products)} products from {len(products)} total")
                
                # Validate products
                valid_products = []
                for product in pre_filtered_products:
                    if self.validator.validate_product_data(product):
                        valid_products.append(product)
                    else:
                        logging.warning(f"Invalid product data: {product}")
                
                logging.info(f"✅ Found {len(valid_products)} valid products for keyword: {keyword}")
                return valid_products
            return []
        except Exception as e:
            logging.error(f"Error in get_products for keyword {keyword}: {e}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            return []
    
    def enhance_keyword(self, keyword):
        """Enhance keyword with related terms for better product discovery"""
        # Define keyword enhancements for better product discovery
        enhancements = {
            'kitchen': 'kitchen gadgets,kitchen tools,cooking utensils',
            'electronics': 'electronic gadgets,smart devices,tech accessories',
            'fashion': 'fashion accessories,clothing,shoes',
            'home': 'home decor,home improvement,household items',
            'beauty': 'beauty products,cosmetics,skincare',
            'sports': 'sports equipment,fitness gear,outdoor activities',
            'toys': 'toys games,educational toys,kids entertainment',
            'automotive': 'car accessories,auto parts,vehicle maintenance',
            'garden': 'gardening tools,outdoor plants,garden decor',
            'office': 'office supplies,stationery,work accessories'
        }
        
        # Check if keyword matches any category
        for category, enhanced_terms in enhancements.items():
            if category.lower() in keyword.lower():
                return f"{keyword},{enhanced_terms}"
        
        # If no specific category match, add some general enhancement
        return f"{keyword},best deals,top rated"
    
    async def save_to_queue(self, product, keyword_used):
        """Save product to queue with advanced filtering"""
        # Check if product already posted using product_id (AliExpress's main identifier)
        product_id = product.get('product_id', '')
        if self.db.is_product_posted(product_id):
            logging.info(f"Product already posted, skipping: {product.get('product_title', '')} (ID: {product_id})")
            return False
        
        # Check if product already in queue
        if self.db.is_product_in_queue(product_id):
            logging.info(f"Product already in queue, skipping: {product.get('product_title', '')} (ID: {product_id})")
            return False
        
        # Get filtering settings from database
        min_discount = self.safe_float_conversion(self.db.get_setting('min_discount_percentage', 15.0))  # Increased from 10%
        min_rating = self.safe_float_conversion(self.db.get_setting('min_product_rating', 4.0))  # New: minimum rating
        min_sales = int(self.db.get_setting('min_product_sales', 5))  # New: minimum sales
        min_quantity = int(self.db.get_setting('min_quantity_sold', 200))  # New: minimum quantity sold
        max_price = self.safe_float_conversion(self.db.get_setting('max_product_price', 500.0))  # New: maximum price
        min_price = self.safe_float_conversion(self.db.get_setting('min_product_price', 5.0))  # New: minimum price
        
        # Get excluded categories and keywords from new tables (global)
        excluded_categories = self.db.get_excluded_categories()
        excluded_keywords = self.db.get_excluded_keywords()
        
        # Check if product has actual discount (original_price > target_sale_price)
        original_price = self.safe_float_conversion(product.get('original_price', 0))
        sale_price = self.safe_float_conversion(product.get('target_sale_price', 0))
        
        # Skip products without discounts
        if original_price <= sale_price:
            logging.info(f"Product has no discount, skipping: {product.get('product_title', '')} (Original: {original_price}, Sale: {sale_price})")
            return False
        
        # Calculate discount percentage
        # Handle discount percentage - it might come as a string with '%' symbol
        discount_value = product.get('discount', 0)
        logging.debug(f"save_to_queue: Processing discount value: {discount_value} (type: {type(discount_value)})")
        if isinstance(discount_value, str):
            # Remove '%' symbol and convert to float
            discount_value = discount_value.replace('%', '').strip()
            logging.debug(f"save_to_queue: After removing '%': {discount_value}")
            try:
                discount_percentage = self.safe_float_conversion(discount_value)
                logging.debug(f"save_to_queue: Successfully parsed discount: {discount_percentage}")
            except ValueError as e:
                logging.warning(f"save_to_queue: Failed to parse discount '{discount_value}', calculating from prices: {e}")
                # If we can't parse the discount, calculate it from prices
                discount_percentage = round(((original_price - sale_price) / original_price) * 100, 1)
        else:
            discount_percentage = round(((original_price - sale_price) / original_price) * 100, 1)
        
        # Check minimum discount threshold
        if discount_percentage < min_discount:
            logging.info(f"Product discount too small ({discount_percentage}% < {min_discount}%), skipping: {product.get('product_title', '')}")
            return False
        
        # Check price range
        if sale_price < min_price or sale_price > max_price:
            logging.info(f"Product price out of range ({sale_price} not in {min_price}-{max_price}), skipping: {product.get('product_title', '')}")
            return False
        
        # Check product rating (if available)
        product_rating = self.safe_float_conversion(product.get('evaluate_rate', 0))
        if product_rating < min_rating:
            logging.info(f"Product rating too low ({product_rating} < {min_rating}), skipping: {product.get('product_title', '')}")
            return False
        
        # Check product sales (if available)
        product_sales = int(self.safe_float_conversion(product.get('lastest_volume', 0)))
        if product_sales < min_sales:
            logging.info(f"Product sales too low ({product_sales} < {min_sales}), skipping: {product.get('product_title', '')}")
            return False
        
        # Check product quantity sold (if available)
        product_quantity = int(self.safe_float_conversion(product.get('lastest_volume', 0)))
        if product_quantity < min_quantity:
            logging.info(f"Product quantity too low ({product_quantity} < {min_quantity}), skipping: {product.get('product_title', '')}")
            return False
        
        # Check for excluded categories/keywords in title
        english_title = product.get('product_title', '').lower()
        for exclude_keyword in excluded_keywords:
            if exclude_keyword.strip() and exclude_keyword.strip().lower() in english_title:
                logging.info(f"Product contains excluded keyword '{exclude_keyword}', skipping: {product.get('product_title', '')}")
                return False
        
        # Check for excluded categories in title
        for exclude_category in excluded_categories:
            if exclude_category.strip() and exclude_category.strip().lower() in english_title:
                logging.info(f"Product contains excluded category '{exclude_category}', skipping: {product.get('product_title', '')}")
                return False
        
        # Check shop reputation (if shop name is available)
        shop_name = product.get('shop_name', '')
        if shop_name:
            # You can add shop reputation logic here
            # For now, we'll just log it for analysis
            logging.info(f"Shop: {shop_name}")
        
        # Calculate quality score for prioritization
        try:
            quality_score = self.calculate_quality_score(product, discount_percentage)
            logging.debug(f"Calculated quality score: {quality_score}")
        except Exception as e:
            logging.error(f"Error calculating quality score: {e}")
            quality_score = 0
        
        logging.info(f"✅ Found quality deal: {product.get('product_title', '')} - {discount_percentage}% off (${original_price} → ${sale_price}) - Quality Score: {quality_score}")
        
        # Use the promotion_link from API (already generated affiliate link)
        affiliate_link = product.get("promotion_link", product.get("product_detail_url", "N/A"))
        product['affiliate_link'] = affiliate_link
        
        # Get Hebrew title (auto-translation)
        english_title = product.get('product_title', 'No Title')
        auto_hebrew_title = get_hebrew_title(english_title)
        
        # Prepare post data for queue
        post_data = {
            'product_id': product_id,
            'english_title': english_title,
            'auto_hebrew_title': auto_hebrew_title,
            'manual_hebrew_title': '',  # To be filled by translation team
            'price': product.get('target_sale_price', 0),
            'currency': product.get('target_sale_price_currency', 'ILS'),
            'regular_price': product.get('original_price', 0),
            'discount_percentage': discount_percentage,
            'product_url': product.get('product_detail_url', ''),
            'image_url': product.get('product_main_image_url', ''),
            'affiliate_link': affiliate_link,
            'origin_country': product.get('product_origin', ''),
            'weight': product.get('product_weight', ''),
            'dimensions': product.get('product_dimensions', ''),
            'keyword_used': keyword_used,
            'product_rating': product.get('evaluate_rate', 0),  # Use evaluate_rate instead of product_rating
            'product_review_count': product.get('product_review_count', 0),
            'product_sales': product.get('lastest_volume', 0),  # Use lastest_volume instead of product_sales
            'product_shop_name': product.get('shop_name', ''),  # Use shop_name instead of product_shop_name
            'quality_score': quality_score,  # New: quality score for prioritization
            'notes': f"Auto-translated Hebrew: {auto_hebrew_title} | Discount: {discount_percentage}% off | Quality Score: {quality_score}"
        }
        
        # Save to queue
        if self.db.save_post_to_queue(post_data):
            logging.info(f"✅ Quality deal queued for review: {english_title[:50]}... ({discount_percentage}% off, Score: {quality_score})")
            return True
        else:
            logging.error(f"❌ Failed to queue deal: {english_title}")
            return False
    
    def calculate_quality_score(self, product, discount_percentage):
        """Calculate a quality score for product prioritization"""
        logging.debug(f"calculate_quality_score: discount_percentage = {discount_percentage} (type: {type(discount_percentage)})")
        
        score = 0
        
        # Base score from discount percentage (higher discount = higher score)
        score += min(discount_percentage * 2, 100)  # Cap at 100 points
        
        # Bonus for high ratings
        rating = self.safe_float_conversion(product.get('evaluate_rate', 0))
        if rating >= 4.5:
            score += 30
        elif rating >= 4.0:
            score += 20
        elif rating >= 3.5:
            score += 10
        
        # Bonus for high sales (social proof)
        sales = int(self.safe_float_conversion(product.get('lastest_volume', 0)))
        if sales >= 100:
            score += 25
        elif sales >= 50:
            score += 15
        elif sales >= 10:
            score += 10
        
        # Bonus for established shops (if shop name is available)
        shop_name = product.get('shop_name', '')
        if shop_name and ('store' in shop_name.lower() or 'shop' in shop_name.lower()):
            score += 10
        
        # Penalty for very low prices (might be low quality)
        price = self.safe_float_conversion(product.get('target_sale_price', 0))
        if price < 10:
            score -= 10
        
        return max(score, 0)  # Ensure score is not negative
    
    async def post_queue_post_to_telegram(self, product, keyword_used, post_id):
        """Post queue post to Telegram (bypasses duplicate check)"""
        logging.info(f"🔍 DEBUG: Starting post_queue_post_to_telegram")
        logging.info(f"🔍 DEBUG: Product ID: {product.get('product_id', 'N/A')}")
        logging.info(f"🔍 DEBUG: Product Title: {product.get('product_title', 'N/A')}")
        logging.info(f"🔍 DEBUG: Keyword Used: {keyword_used}")
        logging.info(f"🔍 DEBUG: Post ID: {post_id}")
        
        url = f"https://api.telegram.org/bot{self.credentials['telegram_bot_token']}/sendPhoto"
        
        # Get the post data from database to ensure we have correct discount info
        post_data = self.db.get_post_by_id(post_id)
        if not post_data:
            logging.error(f"❌ Post {post_id} not found in database")
            return False
        
        logging.info(f"🔍 DEBUG: Database post data - Price: {post_data.get('price')}, Regular: {post_data.get('regular_price')}, Discount: {post_data.get('discount_percentage')}%")
        
        # Use the MANUAL Hebrew translation from the database
        manual_hebrew_title = post_data.get('manual_hebrew_title', '')
        auto_hebrew_title = post_data.get('auto_hebrew_title', '')
        
        # Use manual translation if available, otherwise fall back to auto translation
        hebrew_title = manual_hebrew_title if manual_hebrew_title else auto_hebrew_title
        
        logging.info(f"🔍 DEBUG: Using Hebrew title: {hebrew_title}")
        
        # Sanitize and prepare caption
        # Don't sanitize the manual Hebrew translation - it's user-provided content
        title = hebrew_title  # Use the raw manual translation
        price = self.validator.sanitize_text(str(post_data.get('price', 'N/A')))
        currency = post_data.get('currency', 'ILS')
        
        # Convert ILS to Israeli shekel symbol
        if currency == 'ILS':
            currency = '₪'
        
        # Generate proper affiliate link with tracking
        product_url = product.get('product_detail_url', '')
        affiliate_link = await self.generate_affiliate_link(product_url)
        
        logging.info(f"🔍 DEBUG: Product URL: {product_url}")
        logging.info(f"🔍 DEBUG: Generated affiliate link: {affiliate_link}")
        
        # Use database data for discount information
        original_price = post_data.get('regular_price', 0)
        current_price = post_data.get('price', 0)
        
        logging.info(f"🔍 DEBUG: Using database data - Original: {original_price}, Current: {current_price}")
        
        # Build caption - start with rating and reviews at the TOP
        caption = ""  # Start with empty caption
        
        # Add rating and reviews FIRST (at the very top)
        rating = post_data.get('manual_rating', 0)  # Use manual rating instead of API rating
        reviews = post_data.get('manual_reviews', 0)  # Use manual reviews instead of API reviews
        
        logging.info(f"🔍 DEBUG: Manual rating: {rating}, Manual reviews: {reviews}")
        
        # Add rating and reviews at the very top
        if rating and rating > 0:
            # Show correct number of stars based on rating with numerical value
            stars = "⭐" * int(rating)
            caption += f"דירוג מעולה {stars} ({rating} כוכבים)"
        
        if reviews and reviews > 0:
            # Use correct Hebrew translation for "customer reviews"
            if caption:  # If we already have rating, add a line break
                caption += f"\n"
            caption += f"ביקורות לקוחות: {reviews}"
            logging.info(f"🔍 DEBUG: Added customer reviews line with {reviews} reviews")
        
        # Add the manual Hebrew translation AFTER the rating/reviews
        if caption:  # If we have rating/reviews, add line breaks before translation
            caption += f"\n\n"
        caption += title  # Add the manual Hebrew translation
        
        # Check if the manual translation already contains price information
        price_keywords = ['מחיר', '₪', 'ILS', 'USD', 'EUR', 'חיסכון', 'במקום', 'discount', 'price']
        has_price_in_translation = any(keyword in title for keyword in price_keywords)
        
        # Only add automatic price information if the manual translation doesn't already contain it
        if not has_price_in_translation and original_price and original_price > current_price:
            # Calculate discount percentage from database
            discount_percentage = post_data.get('discount_percentage', 0)
            
            caption += f"\n\n💰 מחיר: {current_price} {currency} בלבד"
            caption += f"\n(במקום {original_price} {currency} 😱)"
            caption += f"\n\n🚚 משלוח חינם לישראל"
            caption += f"\n⚡️ מלאי מוגבל!"
            caption += f"\n\n🛒 להזמנות ⬇️⬇️⬇️"
            caption += f"\n\n💰 מחיר מבצע: {current_price} {currency}"
            caption += f"\n📌 מחיר רגיל: {original_price} {currency}"
            caption += f"\n🎯 חיסכון: {discount_percentage}%"
        elif not has_price_in_translation:
            caption += f"\n\n💰 מחיר: {price} {currency} בלבד"
            caption += f"\n\n🚚 משלוח חינם לישראל"
            caption += f"\n⚡️ מלאי מוגבל!"
            caption += f"\n\n🛒 להזמנות ⬇️⬇️⬇️"
        
        # Add affiliate link as a proper hyperlink using Telegram's URL format
        caption += f"\n\n🛒 בדוק את המבצע כאן! {affiliate_link}"
        
        # Add channel link and call to action at the bottom
        caption += f"\n\n🔔 אל תפספסו מבצעים!"
        caption += f"\n<a href=\"https://t.me/{self.config['telegram']['channel_username'].replace('@', '')}\">הצטרפו לערוץ הטלגרם שלנו</a>"
        
        # Don't sanitize HTML tags - we want them preserved for Telegram parsing
        # caption = self.validator.sanitize_text(caption, max_length=1000)
        
        logging.info(f"🔍 DEBUG: Final caption: {caption}")
        
        # Validate photo URL
        photo_url = product.get("product_main_image_url", "")
        if '"' in photo_url:
            photo_url = photo_url.split('"')[0]
        if not photo_url.startswith("http"):
            photo_url = "https://via.placeholder.com/150"
        
        payload = {
            "chat_id": self.credentials['telegram_channel_id'],
            "photo": photo_url,
            "caption": caption,
            "parse_mode": "HTML"
        }
        
        try:
            response = requests.post(url, json=payload, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if self.validator.validate_telegram_response(data):
                # Mark product as posted using the product dictionary
                self.db.mark_product_posted(product, keyword_used, str(data["result"]["message_id"]))
                logging.info(f"Queue post posted successfully: {hebrew_title}")
                self.health_monitor.record_post(success=True)
                return True
            else:
                logging.error(f"Failed to post queue post: {data}")
                self.health_monitor.record_post(success=False)
                return False
                
        except requests.RequestException as e:
            logging.error(f"Telegram posting error: {str(e)}")
            self.health_monitor.record_error(f"Telegram posting error: {str(e)}", "telegram_error")
            self.health_monitor.record_post(success=False)
            return False

    async def post_to_telegram(self, product, keyword_used):
        """Post product to Telegram"""
        # Check if product already posted using product_id (AliExpress's main identifier)
        product_id = product.get('product_id', '')
        if self.db.is_product_posted(product_id):
            logging.info(f"Product already posted, skipping: {product.get('product_title', '')} (ID: {product_id})")
            return False
        
        url = f"https://api.telegram.org/bot{self.credentials['telegram_bot_token']}/sendPhoto"
        
        # Generate affiliate link
        affiliate_link = await self.generate_affiliate_link(product.get("product_detail_url", "N/A"))
        product['affiliate_link'] = affiliate_link
        
        # Get Hebrew title
        english_title = product.get('product_title', 'No Title')
        hebrew_title = get_hebrew_title(english_title)
        
        # Sanitize and prepare caption
        title = self.validator.sanitize_text(hebrew_title)
        price = self.validator.sanitize_text(str(product.get('target_sale_price', 'N/A')))
        currency = product.get('target_sale_price_currency', 'ILS')
        
        # Convert ILS to Israeli shekel symbol
        if currency == 'ILS':
            currency = '₪'
        
        # Generate proper affiliate link with tracking
        product_url = product.get('product_detail_url', '')
        affiliate_link = await self.generate_affiliate_link(product_url)
        
        # Check if this is a discounted product
        original_price = product.get('original_price', 0)
        sale_price = product.get('target_sale_price', 0)
        
        if original_price and original_price > sale_price:
            # Calculate discount percentage
            discount_percentage = round(((original_price - sale_price) / original_price) * 100, 1)
            original_price_formatted = f"{original_price} {currency}"
            sale_price_formatted = f"{price} {currency}"
            
            logging.info(f"✅ Found discount: {discount_percentage}% off ({original_price} → {sale_price})")
            
            caption = (
                f"<b>🔥 מבצע היום: {title}</b>\n\n"
                f"💰 <b>מחיר מבצע:</b> {sale_price_formatted}\n\n"
                f"<s>📌 מחיר רגיל: {original_price_formatted}</s>\n\n"
                f"🎯 <b>חיסכון:</b> {discount_percentage}%\n\n"
                f"<a href=\"{affiliate_link}\">🛒 בדוק את המבצע כאן!</a>\n\n"
                f"🔔 <b>אל תפספסו מבצעים!</b>\n"
                f"<a href=\"https://t.me/{self.config['telegram']['channel_username'].replace('@', '')}\">הצטרפו לערוץ הטלגרם שלנו</a>\n\n"
            )
        else:
            # Regular price (no discount)
            logging.info(f"⚠️  No discount found - Original: {original_price}, Current: {sale_price}")
            
            caption = (
                f"<b>🔥 מבצע היום: {title}</b>\n\n"
                f"💰 <b>מחיר:</b> {price} {currency}\n\n"
                f"<a href=\"{affiliate_link}\">🛒 בדוק את המבצע כאן!</a>\n\n"
                f"🔔 <b>אל תפספסו מבצעים!</b>\n"
                f"<a href=\"https://t.me/{self.config['telegram']['channel_username'].replace('@', '')}\">הצטרפו לערוץ הטלגרם שלנו</a>"
            )
        
        # Don't sanitize HTML tags - we want them preserved for Telegram parsing
        # caption = self.validator.sanitize_text(caption, max_length=1000)
        
        # Validate photo URL
        photo_url = product.get("product_main_image_url", "")
        if '"' in photo_url:
            photo_url = photo_url.split('"')[0]
        if not photo_url.startswith("http"):
            photo_url = "https://via.placeholder.com/150"
        
        payload = {
            "chat_id": self.credentials['telegram_channel_id'],
            "photo": photo_url,
            "caption": caption,
            "parse_mode": "HTML"
        }
        
        try:
            response = requests.post(url, json=payload, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if self.validator.validate_telegram_response(data):
                # Mark product as posted
                self.db.mark_product_posted(product, keyword_used, str(data["result"]["message_id"]))
                logging.info(f"Product posted successfully: {product.get('product_title', '')}")
                self.health_monitor.record_post(success=True)
                return True
            else:
                logging.error(f"Failed to post: {data}")
                self.health_monitor.record_post(success=False)
                return False
                
        except requests.RequestException as e:
            logging.error(f"Telegram posting error: {str(e)}")
            self.health_monitor.record_error(f"Telegram posting error: {str(e)}", "telegram_error")
            self.health_monitor.record_post(success=False)
            return False
    
    async def run_cycle(self):
        """Run one complete cycle of product fetching and queueing"""
        keywords = self.db.get_keywords()
        if not keywords:
            logging.warning("No active keywords found in database")
            return
        
        queued_count = 0
        for keyword in keywords:
            if self.shutdown_requested:
                logging.info("Shutdown requested, stopping cycle")
                break
                
            logging.info(f"Searching products for keyword: {keyword}")
            
            try:
                products = await self.get_products(keyword, self.credentials['max_price'])
                if products is None:
                    logging.warning(f"Maintenance or API path error for {keyword}. Waiting {self.error_sleep} seconds.")
                    await asyncio.sleep(self.error_sleep)
                    continue
                
                if products:
                    max_products = int(self.db.get_setting('max_products_per_keyword', self.config['bot_settings']['max_products_per_keyword']))
                    for product in products[:max_products]:
                        if self.shutdown_requested:
                            break
                        if await self.save_to_queue(product, keyword):
                            queued_count += 1
                        await asyncio.sleep(5)  # Small delay between saves
                else:
                    logging.warning(f"No products found for keyword: {keyword}")
                    
            except Exception as e:
                logging.error(f"Error processing keyword {keyword}: {e}")
                self.health_monitor.record_error(f"Keyword processing error: {str(e)}", "cycle_error")
                continue
            
            if not self.shutdown_requested:
                logging.info(f"Waiting {self.keyword_sleep} seconds before next keyword")
                await asyncio.sleep(self.keyword_sleep)
        
        logging.info(f"Cycle completed. Queued {queued_count} products. Waiting {self.cycle_sleep} seconds before next cycle")
    
    def shutdown(self):
        """Initiate graceful shutdown"""
        logging.info("Initiating graceful shutdown...")
        self.shutdown_requested = True
        
        # Force exit after 10 seconds if graceful shutdown fails
        import threading
        import time
        
        def force_exit():
            time.sleep(10)
            if self.shutdown_requested:
                logging.warning("Graceful shutdown taking too long, forcing exit...")
                import os
                os._exit(0)
        
        force_thread = threading.Thread(target=force_exit, daemon=True)
        force_thread.start()
    
    async def main_loop(self):
        """Main application loop with health monitoring"""
        logging.info(f"🚀 Starting Post Queue Bot for account: {self.account_id}")
        logging.info(f"Testing mode: {self.credentials.get('testing_mode', True)}")
        logging.info(f"Max price: {self.credentials['max_price']} cents")
        logging.info("📋 Posts will be saved to queue for manual translation review")
        
        # Cleanup old posts periodically
        self.db.cleanup_old_posts(30)
        
        cycle_count = 0
        while not self.shutdown_requested:
            try:
                cycle_count += 1
                logging.info(f"Starting cycle {cycle_count}")
                
                await self.run_cycle()
                
                # Log health report every 10 cycles
                if cycle_count % 10 == 0:
                    health_report = self.health_monitor.get_health_report()
                    logging.info(f"Health Report - Cycle {cycle_count}: {health_report}")
                
                if not self.shutdown_requested:
                    await asyncio.sleep(self.cycle_sleep)
                else:
                    logging.info("Shutdown requested, exiting main loop")
                    break
                    
            except KeyboardInterrupt:
                logging.info("Bot stopped by user")
                break
            except Exception as e:
                logging.error(f"Unexpected error in main loop: {str(e)}")
                self.health_monitor.record_error(f"Main loop error: {str(e)}", "main_loop_error")
                await asyncio.sleep(self.error_sleep)
        
        # Final health report
        final_health = self.health_monitor.get_health_report()
        logging.info(f"Final Health Report: {final_health}")
        
        self.db.close()
        logging.info("Bot shutdown complete")

async def main():
    """Main function for queue bot"""
    try:
        bot = PostQueueBot()
        await bot.main_loop()
        
    except Exception as e:
        logging.error(f"❌ Post Queue Bot error: {e}")

if __name__ == "__main__":
    import json
    asyncio.run(main()) 