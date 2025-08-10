#!/usr/bin/env python3
"""
Test with user's specific product ID
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
    """Generate HMAC-SHA256 signature in uppercase for AliExpress API"""
    sorted_params = sorted(params.items())
    param_string = ''.join([f"{k}{v}" for k, v in sorted_params])
    signature = hmac.new(
        secret_key.encode('utf-8'),
        param_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest().upper()
    return signature

def test_specific_product():
    print("🔍 Testing User's Specific Product")
    print("=" * 50)
    
    # User's specific product ID from their affiliate link
    product_id = "1005007300678312"
    product_url = f"https://www.aliexpress.com/item/{product_id}.html"
    
    print(f"Testing Product ID: {product_id}")
    print(f"Product URL: {product_url}")
    
    api_url = 'https://api-sg.aliexpress.com/sync'
    
    # Test direct link generation
    link_params = {
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
    
    link_params['sign'] = generate_hmac_signature_upper(link_params, SECRET_KEY)
    
    print(f"\n🔄 Testing Direct Link Generation...")
    
    try:
        response = requests.get(api_url, params=link_params, timeout=10)
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
                        print(f"⚠️ Product not available for affiliate links via API")
                        print(f"💡 This product might not be in the affiliate program")
                    else:
                        print(f"✅ Success! Result: {result}")
            else:
                print(f"⚠️ Unexpected response format: {data}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_specific_product() 