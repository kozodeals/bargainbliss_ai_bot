#!/usr/bin/env python3
"""
Test the specific product issue
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

def test_specific_product_issue():
    print("🔍 Testing Specific Product Issue")
    print("=" * 50)
    
    # The problematic product ID
    product_id = "1005007500365472"
    product_url = f"https://he.aliexpress.com/item/{product_id}.html"
    
    print(f"Product ID: {product_id}")
    print(f"Product URL: {product_url}")
    
    api_url = 'https://api-sg.aliexpress.com/sync'
    
    # Test the API with this specific product
    query_params = {
        'app_key': API_KEY,
        'method': 'aliexpress.affiliate.product.query',
        'format': 'json',
        'v': '2.0',
        'sign_method': 'sha256',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
        'product_ids': product_id,
        'tracking_id': TRACKING_ID,
        'page_no': '1',
        'page_size': '1'
    }
    
    # Generate HMAC-SHA256 signature in uppercase
    query_params['sign'] = generate_hmac_signature_upper(query_params, SECRET_KEY)
    
    try:
        response = requests.get(api_url, params=query_params, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if 'error_response' in data:
                print(f"❌ API Error: {data['error_response']}")
            elif 'aliexpress_affiliate_product_query_response' in data:
                resp = data['aliexpress_affiliate_product_query_response']
                if 'resp_result' in resp and 'result' in resp['resp_result']:
                    products = resp['resp_result']['result'].get('products', {}).get('product', [])
                    if products:
                        print(f"✅ Found {len(products)} products")
                        for i, product in enumerate(products, 1):
                            product_id_in_result = product.get('product_id', '')
                            promotion_link = product.get('promotion_link', '')
                            print(f"\nProduct {i}:")
                            print(f"  Product ID in result: {product_id_in_result}")
                            print(f"  Requested Product ID: {product_id}")
                            print(f"  Match: {'✅' if str(product_id_in_result) == str(product_id) else '❌'}")
                            print(f"  Promotion Link: {promotion_link}")
                            
                            # Check if it's the same product
                            if str(product_id_in_result) == str(product_id):
                                print(f"  ✅ CORRECT PRODUCT FOUND!")
                            else:
                                print(f"  ❌ WRONG PRODUCT! API returned different product")
                    else:
                        print(f"⚠️ No products found")
            else:
                print(f"⚠️ Unexpected response format: {list(data.keys())}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_specific_product_issue() 