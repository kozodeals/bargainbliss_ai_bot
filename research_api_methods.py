#!/usr/bin/env python3
"""
Deep research to find the correct API method for generating affiliate links
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

def test_all_api_methods():
    print("🔍 Deep Research: Testing All Possible API Methods")
    print("=" * 60)
    
    product_id = "1005007300678312"  # User's specific product
    product_url = f"https://www.aliexpress.com/item/{product_id}.html"
    
    print(f"Testing with Product ID: {product_id}")
    print(f"Product URL: {product_url}")
    
    api_url = 'https://api-sg.aliexpress.com/sync'
    
    # Test all possible API methods for affiliate link generation
    methods_to_test = [
        {
            'name': 'aliexpress.affiliate.link.generate (current)',
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
                'promotion_link_type': '0',
                'source_values': 'telegram_bot'
            }
        },
        {
            'name': 'aliexpress.affiliate.link.generate (with different types)',
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
                'promotion_link_type': '1',  # Try different type
                'source_values': 'telegram_bot'
            }
        },
        {
            'name': 'aliexpress.affiliate.link.generate (with URL)',
            'params': {
                'app_key': API_KEY,
                'method': 'aliexpress.affiliate.link.generate',
                'format': 'json',
                'v': '2.0',
                'sign_method': 'sha256',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
                'url': product_url,  # Try 'url' instead of 'product_id'
                'tracking_id': TRACKING_ID,
                'promotion_link_type': '0',
                'source_values': 'telegram_bot'
            }
        },
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
            'name': 'aliexpress.affiliate.product.query (with exact product)',
            'params': {
                'app_key': API_KEY,
                'method': 'aliexpress.affiliate.product.query',
                'format': 'json',
                'v': '2.0',
                'sign_method': 'sha256',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
                'keywords': product_id,  # Use product ID as keyword
                'tracking_id': TRACKING_ID,
                'page_no': '1',
                'page_size': '1'  # Get only one result
            }
        },
        {
            'name': 'aliexpress.affiliate.product.query (with product URL)',
            'params': {
                'app_key': API_KEY,
                'method': 'aliexpress.affiliate.product.query',
                'format': 'json',
                'v': '2.0',
                'sign_method': 'sha256',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
                'keywords': product_url,  # Use full URL as keyword
                'tracking_id': TRACKING_ID,
                'page_no': '1',
                'page_size': '1'
            }
        }
    ]
    
    for i, method in enumerate(methods_to_test, 1):
        print(f"\n{'='*20} Test {i}: {method['name']} {'='*20}")
        
        params = method['params'].copy()
        params['sign'] = generate_hmac_signature_upper(params, SECRET_KEY)
        
        try:
            response = requests.get(api_url, params=params, timeout=10)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text[:500]}...")
            
            if response.status_code == 200:
                data = response.json()
                if 'error_response' in data:
                    print(f"❌ API Error: {data['error_response']}")
                elif 'aliexpress_affiliate_link_generate_response' in data:
                    resp = data['aliexpress_affiliate_link_generate_response']
                    if 'resp_result' in resp:
                        result = resp['resp_result']
                        if result.get('resp_code') == 405:
                            print(f"⚠️ Product not available for affiliate links")
                        else:
                            print(f"✅ Success! Result: {result}")
                elif 'aliexpress_affiliate_product_query_response' in data:
                    resp = data['aliexpress_affiliate_product_query_response']
                    if 'resp_result' in resp and 'result' in resp['resp_result']:
                        products = resp['resp_result']['result'].get('products', {}).get('product', [])
                        if products:
                            print(f"✅ Found {len(products)} products")
                            # Check if any product has promotion_link
                            for product in products[:3]:  # Check first 3 products
                                if 'promotion_link' in product:
                                    print(f"✅ Found promotion link: {product['promotion_link']}")
                                    break
                        else:
                            print(f"⚠️ No products found")
                else:
                    print(f"⚠️ Unexpected response format: {list(data.keys())}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_all_api_methods() 