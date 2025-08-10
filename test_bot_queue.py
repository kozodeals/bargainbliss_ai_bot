#!/usr/bin/env python3
"""
Test script using bot_queue.py's implementation
"""

import os
import json
import logging
import time
import hmac
import hashlib
import asyncio
from dotenv import load_dotenv
import aiohttp
import re

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Load credentials
API_KEY = os.getenv('AFFILIATE_API_KEY') or os.getenv('ALIBABA_API_KEY') or os.getenv('ALIEXPRESS_API_KEY')
SECRET_KEY = os.getenv('AFFILIATE_SECRET_KEY') or os.getenv('ALIBABA_SECRET_KEY') or os.getenv('ALIEXPRESS_SECRET_KEY')
TRACKING_ID = os.getenv('TRACKING_ID', 'bargainbliss_ai_bot')  # Use human-readable tracking ID

class TestBot:
    def __init__(self):
        self.api_key = API_KEY
        self.secret_key = SECRET_KEY
        self.tracking_id = TRACKING_ID
        self.config = {
            'aliexpress': {
                'promotion_link_type': '1',
                'ship_to_country': 'IL'
            }
        }
        self.credentials = {
            'tracking_id': TRACKING_ID,
            'currency': 'ILS',
            'language': 'IL'
        }

    def generate_signature(self, params, secret, sign_method="sha256"):
        """Generate API signature - exact copy from bot_queue.py"""
        sorted_params = sorted(params.items())
        sign_string = "".join(f"{k}{v}" for k, v in sorted_params)
        hash_algorithm = hashlib.sha256 if sign_method.lower() == "sha256" else hashlib.md5
        return hmac.new(secret.encode(), sign_string.encode(), hash_algorithm).hexdigest().upper()

    async def aliexpress_api_request(self, params):
        """Make API request to AliExpress - exact copy from bot_queue.py"""
        api_url = 'https://api-sg.aliexpress.com/sync'
        
        # Add common parameters
        params.update({
            'app_key': self.api_key,
            'sign_method': 'sha256',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
            'format': 'json',
            'v': '2.0'
        })
        
        # Generate signature
        params['sign'] = self.generate_signature(params, self.secret_key)
        
        logger.info(f"Making API request to: {api_url}")
        logger.info(f"Parameters: {json.dumps(params, indent=2)}")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Use POST instead of GET
                async with session.post(api_url, data=params, timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Response Data: {json.dumps(data, indent=2)}")
                        return data
                    else:
                        logger.error(f"HTTP Error: {response.status}")
                        logger.error(f"Response: {await response.text()}")
                        return None
        except Exception as e:
            logger.error(f"Error making API request: {e}")
            return None

    async def generate_affiliate_link(self, product_url):
        """Generate affiliate link - two-step process like main program"""
        # Extract product ID from URL
        product_id = None
        if '/item/' in product_url:
            # Extract product ID from URL like /item/1005009533140539.html
            match = re.search(r'/item/(\d+)', product_url)
            if match:
                product_id = match.group(1)
        
        if not product_id:
            logger.error("Could not extract product ID from URL")
            return None
        
        # Use the correct human-readable tracking ID
        tracking_id = 'bargainbliss_ai_bot'
        logger.info(f"Using tracking ID: {tracking_id}")
        logger.info(f"Using product ID: {product_id}")
        
        # STEP 1: Get product details using aliexpress.affiliate.product.query
        logger.info(f"Step 1: Getting product details for ID: {product_id}")
        params = {
            "method": "aliexpress.affiliate.product.query",
            "format": "json",
            "product_ids": product_id,
            "trackingId": tracking_id,  # Use camelCase for this method
            "fields": "product_id,product_title,promotion_link,product_detail_url",
            "target_currency": "ILS",
            "target_language": "IL"
        }
        
        response = await self.aliexpress_api_request(params)
        if response and "aliexpress_affiliate_product_query_response" in response:
            resp = response["aliexpress_affiliate_product_query_response"]
            if 'resp_result' in resp:
                resp_result = resp['resp_result']
                if resp_result.get('resp_code') in [0, 200]:  # Success
                    if 'result' in resp_result and 'products' in resp_result['result']:
                        products = resp_result['result']['products'].get('product', [])
                        if products and len(products) > 0:
                            product = products[0] if isinstance(products, list) else products
                            product_detail_url = product.get('product_detail_url')
                            
                            if product_detail_url:
                                # STEP 2: Generate short affiliate link using aliexpress.affiliate.link.generate
                                logger.info(f"Step 2: Generating short affiliate link")
                                short_link = await self.generate_short_affiliate_link(product_detail_url, tracking_id)
                                if short_link:
                                    logger.info(f"Generated short affiliate link: {short_link}")
                                    return short_link
        
        logger.error(f"Failed to generate affiliate link for {product_url}")
        return None

    async def generate_short_affiliate_link(self, product_url, tracking_id):
        """Generate short affiliate link using aliexpress.affiliate.link.generate"""
        
        # Use aliexpress.affiliate.link.generate to get short link
        params = {
            "method": "aliexpress.affiliate.link.generate",
            "format": "json",
            "source_values": product_url,
            "tracking_id": tracking_id,
            "promotion_link_type": "0",  # Changed from '1' to '0' for direct product links
            "target_currency": "ILS",
            "target_language": "IL"
        }
        
        response = await self.aliexpress_api_request(params)
        
        if response and "aliexpress_affiliate_link_generate_response" in response:
            resp = response["aliexpress_affiliate_link_generate_response"]
            if "resp_result" in resp:
                resp_result = resp["resp_result"]
                if resp_result.get("resp_code") in [0, 200]:
                    if "result" in resp_result and "promotion_links" in resp_result["result"]:
                        promotion_links = resp_result["result"]["promotion_links"].get("promotion_link", [])
                        if promotion_links and len(promotion_links) > 0:
                            promotion_link = promotion_links[0].get("promotion_link")
                            if promotion_link:
                                print(f"✅ Generated short affiliate link: {promotion_link}")
                                return promotion_link
        
        print("❌ Failed to generate short affiliate link")
        return None

async def main():
    """Main test function"""
    # Test URL
    test_url = "https://he.aliexpress.com/item/1005009533140539.html"
    
    logger.info("Starting test...")
    logger.info(f"Testing with URL: {test_url}")
    logger.info(f"Using API Key: {API_KEY[:8]}...")
    logger.info(f"Using Tracking ID: {TRACKING_ID}")
    
    bot = TestBot()
    result = await bot.generate_affiliate_link(test_url)
    
    if result:
        logger.info("✅ Success! Generated affiliate link:")
        logger.info(result)
    else:
        logger.error("❌ Failed to generate affiliate link")

if __name__ == "__main__":
    asyncio.run(main()) 