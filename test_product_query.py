#!/usr/bin/env python3
"""
Test if aliexpress.affiliate.product.query correctly finds specific products
"""

import os
import json
import logging
import time
import hmac
import hashlib
import asyncio
import re
from dotenv import load_dotenv
import aiohttp

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
TRACKING_ID = 'bargainbliss_ai_bot'

class ProductQueryTester:
    def __init__(self):
        self.api_key = API_KEY
        self.secret_key = SECRET_KEY
        self.tracking_id = TRACKING_ID

    def generate_signature(self, params, secret, sign_method="sha256"):
        """Generate API signature"""
        sorted_params = sorted(params.items())
        sign_string = "".join(f"{k}{v}" for k, v in sorted_params)
        hash_algorithm = hashlib.sha256 if sign_method.lower() == "sha256" else hashlib.md5
        return hmac.new(secret.encode(), sign_string.encode(), hash_algorithm).hexdigest().upper()

    async def aliexpress_api_request(self, params):
        """Make API request to AliExpress"""
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

    async def test_product_query(self, product_id):
        """Test if aliexpress.affiliate.product.query finds the specific product"""
        logger.info(f"Testing product query for ID: {product_id}")
        
        params = {
            'method': 'aliexpress.affiliate.product.query',
            'format': 'json',
            'product_ids': product_id,
            'trackingId': self.tracking_id,
            'fields': 'product_id,product_title,promotion_link,product_detail_url',
            'target_currency': 'ILS',
            'target_language': 'IL'
        }
        
        response = await self.aliexpress_api_request(params)
        
        if response and 'aliexpress_affiliate_product_query_response' in response:
            resp = response['aliexpress_affiliate_product_query_response']
            if 'resp_result' in resp:
                resp_result = resp['resp_result']
                if resp_result.get('resp_code') in [0, 200]:
                    if 'result' in resp_result and 'products' in resp_result['result']:
                        products = resp_result['result']['products'].get('product', [])
                        if products and len(products) > 0:
                            product = products[0] if isinstance(products, list) else products
                            returned_product_id = product.get('product_id')
                            product_title = product.get('product_title', 'N/A')
                            
                            logger.info(f"✅ Found product:")
                            logger.info(f"   Requested ID: {product_id}")
                            logger.info(f"   Returned ID: {returned_product_id}")
                            logger.info(f"   Title: {product_title}")
                            
                            if str(returned_product_id) == str(product_id):
                                logger.info("✅ SUCCESS! Returned product matches requested ID")
                                return product
                            else:
                                logger.error(f"❌ MISMATCH! Returned product ID {returned_product_id} doesn't match requested {product_id}")
                                return None
                        else:
                            logger.error("❌ No products found in response")
                            return None
                    else:
                        logger.error("❌ No result or products in response")
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

async def main():
    """Main test function"""
    # Test with the product ID from the user's URL
    test_product_id = "1005004896181006"  # The toilet product ID from the screenshot
    
    logger.info("Starting product query test...")
    logger.info(f"Testing with product ID: {test_product_id}")
    logger.info(f"Using API Key: {API_KEY[:8]}...")
    logger.info(f"Using Tracking ID: {TRACKING_ID}")
    
    tester = ProductQueryTester()
    result = await tester.test_product_query(test_product_id)
    
    if result:
        logger.info("✅ Success! Product query returned correct product")
        logger.info(f"Product Title: {result.get('product_title', 'N/A')}")
        logger.info(f"Product Detail URL: {result.get('product_detail_url', 'N/A')}")
    else:
        logger.error("❌ Failed to get correct product")

if __name__ == "__main__":
    asyncio.run(main()) 