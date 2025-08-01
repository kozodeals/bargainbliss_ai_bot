#!/usr/bin/env python3
"""
Detailed API test to see exact responses
"""

import requests
import time
import hashlib
import hmac
import os
from urllib.parse import urlparse
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get credentials
API_KEY = os.getenv('ALIEXPRESS_API_KEY') or os.getenv('AFFILIATE_API_KEY')
SECRET_KEY = os.getenv('ALIEXPRESS_SECRET_KEY') or os.getenv('AFFILIATE_SECRET_KEY')
TRACKING_ID = os.getenv('TRACKING_ID', 'bargainbliss_ai_bot')

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

def main():
    print("🔍 Detailed AliExpress API Test")
    print("=" * 50)
    
    # Test different product URLs
    test_urls = [
        "https://www.aliexpress.com/item/1005004842197456.html",
        "https://www.aliexpress.com/item/1005001234567890.html",
        "https://www.aliexpress.com/item/1005009876543210.html"
    ]
    
    print(f"API Key: {API_KEY}")
    print(f"Secret Key: {SECRET_KEY[:10]}...")
    print(f"Tracking ID: {TRACKING_ID}")
    
    # API endpoint
    api_url = 'https://api-sg.aliexpress.com/sync'
    
    for i, test_url in enumerate(test_urls, 1):
        print(f"\n{'='*20} Test {i} {'='*20}")
        
        # Extract product ID
        parsed_url = urlparse(test_url)
        product_id_match = re.search(r'/item/(\d+)', parsed_url.path)
        product_id = product_id_match.group(1) if product_id_match else "1005004842197456"
        
        print(f"Testing with product ID: {product_id}")
        
        # Request parameters
        params = {
            'app_key': API_KEY,
            'method': 'aliexpress.affiliate.link.generate',
            'format': 'json',
            'v': '2.0',
            'sign_method': 'sha256',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
            'product_id': product_id,
            'tracking_id': TRACKING_ID,
            'source_url': test_url,
            'promotion_link_type': '0',
            'source_values': 'telegram_bot'
        }
        
        # Generate signature
        params['sign'] = generate_hmac_signature_upper(params, SECRET_KEY)
        
        print(f"Making API request...")
        
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
                        if result.get('resp_code') == 405:
                            print(f"⚠️ Product not available for affiliate links")
                        else:
                            print(f"✅ Success! Result: {result}")
                else:
                    print(f"⚠️ Unexpected response format: {data}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
    
    # Also test product query method
    print(f"\n{'='*20} Testing Product Query {'='*20}")
    
    params = {
        'app_key': API_KEY,
        'method': 'aliexpress.affiliate.product.query',
        'format': 'json',
        'v': '2.0',
        'sign_method': 'sha256',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
        'keywords': 'phone',
        'tracking_id': TRACKING_ID
    }
    
    # Generate signature
    params['sign'] = generate_hmac_signature_upper(params, SECRET_KEY)
    
    print(f"Testing product query with keywords: 'phone'")
    
    try:
        response = requests.get(api_url, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    main() 