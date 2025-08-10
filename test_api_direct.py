#!/usr/bin/env python3
"""
Test the API directly with user's product
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

def test_api_direct():
    print("🔍 Testing API Directly with User's Product")
    print("=" * 50)
    
    # User's specific product
    product_id = "1005007300678312"
    product_url = f"https://www.aliexpress.com/item/{product_id}.html"
    
    print(f"Testing with Product ID: {product_id}")
    print(f"Product URL: {product_url}")
    
    api_url = 'https://api-sg.aliexpress.com/sync'
    
    # Test the working method we found
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
        'promotion_link_type': '1',  # Use type '1' which works!
        'source_values': 'telegram_bot'
    }
    
    # Generate HMAC-SHA256 signature in uppercase
    link_params['sign'] = generate_hmac_signature_upper(link_params, SECRET_KEY)
    
    print(f"API URL: {api_url}")
    print(f"Method: {link_params['method']}")
    print(f"Product ID: {product_id}")
    print(f"Promotion Link Type: {link_params['promotion_link_type']}")
    
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
                    if result.get('resp_code') == 200:
                        print(f"✅ SUCCESS! Real affiliate link generated!")
                        if 'result' in result and 'promotion_links' in result['result']:
                            promotion_links = result['result']['promotion_links'].get('promotion_link', [])
                            if promotion_links and len(promotion_links) > 0:
                                promotion_link = promotion_links[0].get('promotion_link')
                                print(f"✅ Real Affiliate Link: {promotion_link}")
                    elif result.get('resp_code') == 405:
                        print(f"⚠️ Product not available for affiliate links")
                    else:
                        print(f"⚠️ Unexpected response: {result}")
            else:
                print(f"⚠️ Unexpected response format: {list(data.keys())}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_api_direct() 