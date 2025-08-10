#!/usr/bin/env python3
"""
Test different parameter combinations for generating direct product links
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

class DirectLinkTester:
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

    async def test_different_approaches(self, product_url):
        """Test different approaches to generate direct product links"""
        product_id = None
        if '/item/' in product_url:
            match = re.search(r'/item/(\d+)', product_url)
            if match:
                product_id = match.group(1)
        
        if not product_id:
            logger.error("Could not extract product ID from URL")
            return None
        
        logger.info(f"Testing different approaches for product ID: {product_id}")
        
        # Approach 1: Try different promotion_link_type values
        promotion_link_types = ['0', '1', '2', '3']
        
        for link_type in promotion_link_types:
            logger.info(f"\n=== Testing promotion_link_type: {link_type} ===")
            
            params = {
                'method': 'aliexpress.affiliate.link.generate',
                'format': 'json',
                'source_values': product_url,
                'tracking_id': self.tracking_id,
                'promotion_link_type': link_type,
                'target_currency': 'ILS',
                'target_language': 'IL'
            }
            
            response = await self.aliexpress_api_request(params)
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
                                    logger.info(f"✅ Generated link with type {link_type}: {promotion_link}")
                                    # Check if it's a direct link (no SearchText)
                                    if 'SearchText' not in promotion_link:
                                        logger.info(f"🎉 FOUND DIRECT LINK! Type {link_type} works!")
                                        return promotion_link
                                    else:
                                        logger.info(f"❌ Still search link with type {link_type}")
        
        # Approach 2: Try using productdetail.get method
        logger.info(f"\n=== Testing aliexpress.affiliate.productdetail.get ===")
        
        params = {
            'method': 'aliexpress.affiliate.productdetail.get',
            'format': 'json',
            'product_ids': product_id,
            'trackingId': self.tracking_id,
            'fields': 'product_id,product_title,promotion_link,product_detail_url',
            'target_currency': 'ILS',
            'target_language': 'IL'
        }
        
        response = await self.aliexpress_api_request(params)
        if response and 'aliexpress_affiliate_productdetail_get_response' in response:
            resp = response['aliexpress_affiliate_productdetail_get_response']
            if 'resp_result' in resp:
                resp_result = resp['resp_result']
                if resp_result.get('resp_code') in [0, 200]:
                    if 'result' in resp_result and 'products' in resp_result['result']:
                        products = resp_result['result']['products'].get('product', [])
                        if products and len(products) > 0:
                            product = products[0] if isinstance(products, list) else products
                            promotion_link = product.get('promotion_link')
                            if promotion_link:
                                logger.info(f"✅ Generated link with productdetail.get: {promotion_link}")
                                if 'SearchText' not in promotion_link:
                                    logger.info(f"🎉 FOUND DIRECT LINK! productdetail.get works!")
                                    return promotion_link
                                else:
                                    logger.info(f"❌ Still search link with productdetail.get")
        
        # Approach 3: Try using product.details.get method
        logger.info(f"\n=== Testing aliexpress.affiliate.product.details.get ===")
        
        params = {
            'method': 'aliexpress.affiliate.product.details.get',
            'format': 'json',
            'product_ids': product_id,
            'trackingId': self.tracking_id,
            'fields': 'product_id,product_title,promotion_link,product_detail_url',
            'target_currency': 'ILS',
            'target_language': 'IL'
        }
        
        response = await self.aliexpress_api_request(params)
        if response and 'aliexpress_affiliate_product_details_get_response' in response:
            resp = response['aliexpress_affiliate_product_details_get_response']
            if 'resp_result' in resp:
                resp_result = resp['resp_result']
                if resp_result.get('resp_code') in [0, 200]:
                    if 'result' in resp_result and 'products' in resp_result['result']:
                        products = resp_result['result']['products'].get('product', [])
                        if products and len(products) > 0:
                            product = products[0] if isinstance(products, list) else products
                            promotion_link = product.get('promotion_link')
                            if promotion_link:
                                logger.info(f"✅ Generated link with product.details.get: {promotion_link}")
                                if 'SearchText' not in promotion_link:
                                    logger.info(f"🎉 FOUND DIRECT LINK! product.details.get works!")
                                    return promotion_link
                                else:
                                    logger.info(f"❌ Still search link with product.details.get")
        
        logger.error("❌ No direct link generation method found")
        return None

async def main():
    """Main test function"""
    # Test URL - clean URL without query parameters
    test_url = "https://he.aliexpress.com/item/1005004896181006.html"  # Clean URL
    
    logger.info("Starting direct link test...")
    logger.info(f"Testing with URL: {test_url}")
    logger.info(f"Using API Key: {API_KEY[:8]}...")
    logger.info(f"Using Tracking ID: {TRACKING_ID}")
    
    tester = DirectLinkTester()
    result = await tester.test_different_approaches(test_url)
    
    if result:
        logger.info("✅ Success! Found direct product link:")
        logger.info(result)
    else:
        logger.error("❌ Failed to find direct product link generation method")

if __name__ == "__main__":
    asyncio.run(main()) 