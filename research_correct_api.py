#!/usr/bin/env python3
"""
Research the correct API method for specific products
"""

import requests
import time
import hashlib
import hmac
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get credentials
API_KEY = os.getenv('ALIEXPRESS_API_KEY') or os.getenv('AFFILIATE_API_KEY')
SECRET_KEY = os.getenv('ALIEXPRESS_SECRET_KEY') or os.getenv('AFFILIATE_SECRET_KEY')
TRACKING_ID = os.getenv('TRACKING_ID', 'bargainbliss_ai_bot')

def generate_hmac_signature_upper(params, secret_key):
    """Generate HMAC-SHA256 signature in uppercase"""
    sorted_params = sorted(params.items())
    param_string = ''.join([f"{k}{v}" for k, v in sorted_params])
    signature = hmac.new(
        secret_key.encode('utf-8'),
        param_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest().upper()
    return signature

def research_correct_api():
    print("🔍 Researching Correct API Method for Specific Products")
    print("=" * 60)
    
    # User's specific product
    product_id = "1005007300678312"
    product_url = f"https://www.aliexpress.com/item/{product_id}.html"
    
    print(f"Product ID: {product_id}")
    print(f"Product URL: {product_url}")
    
    api_url = 'https://api-sg.aliexpress.com/sync'
    
    # Test different API methods and parameters
    test_cases = [
        {
            'name': 'aliexpress.affiliate.productdetail.get',
            'params': {
                'app_key': API_KEY,
                'method': 'aliexpress.affiliate.productdetail.get',
                'format': 'json',
                'v': '2.0',
                'sign_method': 'sha256',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
                'product_id': product_id,
                'tracking_id': TRACKING_ID
            }
        },
        {
            'name': 'aliexpress.affiliate.product.info.get',
            'params': {
                'app_key': API_KEY,
                'method': 'aliexpress.affiliate.product.info.get',
                'format': 'json',
                'v': '2.0',
                'sign_method': 'sha256',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
                'product_id': product_id,
                'tracking_id': TRACKING_ID
            }
        },
        {
            'name': 'aliexpress.affiliate.product.query with product_ids',
            'params': {
                'app_key': API_KEY,
                'method': 'aliexpress.affiliate.product.query',
                'format': 'json',
                'v': '2.0',
                'sign_method': 'sha256',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
                'product_ids': product_id,  # Try product_ids instead of keywords
                'tracking_id': TRACKING_ID,
                'page_no': '1',
                'page_size': '1'
            }
        },
        {
            'name': 'aliexpress.affiliate.link.generate with different type',
            'params': {
                'app_key': API_KEY,
                'method': 'aliexpress.affiliate.link.generate',
                'format': 'json',
                'v': '2.0',
                'sign_method': 'sha256',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
                'product_id': product_id,
                'tracking_id': TRACKING_ID,
                'source_url': product_url,
                'promotion_link_type': '2',  # Try different type
                'source_values': 'telegram_bot'
            }
        },
        {
            'name': 'aliexpress.affiliate.link.generate with product_url',
            'params': {
                'app_key': API_KEY,
                'method': 'aliexpress.affiliate.link.generate',
                'format': 'json',
                'v': '2.0',
                'sign_method': 'sha256',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
                'product_url': product_url,  # Try product_url instead of product_id
                'tracking_id': TRACKING_ID,
                'promotion_link_type': '1',
                'source_values': 'telegram_bot'
            }
        },
        {
            'name': 'aliexpress.affiliate.link.generate with item_id',
            'params': {
                'app_key': API_KEY,
                'method': 'aliexpress.affiliate.link.generate',
                'format': 'json',
                'v': '2.0',
                'sign_method': 'sha256',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
                'item_id': product_id,  # Try item_id instead of product_id
                'tracking_id': TRACKING_ID,
                'source_url': product_url,
                'promotion_link_type': '1',
                'source_values': 'telegram_bot'
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*20} Test {i}: {test_case['name']} {'='*20}")
        
        params = test_case['params'].copy()
        params['sign'] = generate_hmac_signature_upper(params, SECRET_KEY)
        
        try:
            response = requests.get(api_url, params=params, timeout=10)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                if 'error_response' in data:
                    print(f"❌ API Error: {data['error_response']}")
                elif 'aliexpress_affiliate_link_generate_response' in data:
                    resp = data['aliexpress_affiliate_link_generate_response']
                    if 'resp_result' in resp:
                        result = resp['resp_result']
                        if result.get('resp_code') == 200:
                            if 'result' in result and 'promotion_links' in result['result']:
                                promotion_links = result['result']['promotion_links'].get('promotion_link', [])
                                if promotion_links and len(promotion_links) > 0:
                                    promotion_link = promotion_links[0].get('promotion_link')
                                    print(f"✅ Generated Link: {promotion_link}")
                                    if 'SearchText=' in promotion_link:
                                        print(f"⚠️ WARNING: Link contains SearchText - this is a search result!")
                                    else:
                                        print(f"✅ SUCCESS: Direct product link!")
                        elif result.get('resp_code') == 405:
                            print(f"⚠️ Product not available for affiliate links")
                        else:
                            print(f"⚠️ Unexpected response: {result}")
                elif 'aliexpress_affiliate_product_query_response' in data:
                    resp = data['aliexpress_affiliate_product_query_response']
                    if 'resp_result' in resp and 'result' in resp['resp_result']:
                        products = resp['resp_result']['result'].get('products', {}).get('product', [])
                        if products:
                            print(f"✅ Found {len(products)} products")
                            for product in products[:2]:
                                if 'promotion_link' in product:
                                    promotion_link = product['promotion_link']
                                    print(f"✅ Product Promotion Link: {promotion_link}")
                                    if 'SearchText=' in promotion_link:
                                        print(f"⚠️ WARNING: Link contains SearchText - this is a search result!")
                                    else:
                                        print(f"✅ SUCCESS: Direct product link!")
                        else:
                            print(f"⚠️ No products found")
                elif 'aliexpress_affiliate_productdetail_get_response' in data:
                    resp = data['aliexpress_affiliate_productdetail_get_response']
                    print(f"✅ Product Detail Response: {resp}")
                elif 'aliexpress_affiliate_product_info_get_response' in data:
                    resp = data['aliexpress_affiliate_product_info_get_response']
                    print(f"✅ Product Info Response: {resp}")
                else:
                    print(f"⚠️ Unexpected response format: {list(data.keys())}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")

if __name__ == "__main__":
    research_correct_api() 