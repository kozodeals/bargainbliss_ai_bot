#!/usr/bin/env python3
"""
Test the new deep link API
"""

import requests
import time
import hashlib
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get credentials
API_KEY = os.getenv('ALIEXPRESS_API_KEY') or os.getenv('AFFILIATE_API_KEY')
SECRET_KEY = os.getenv('ALIEXPRESS_SECRET_KEY') or os.getenv('AFFILIATE_SECRET_KEY')
TRACKING_ID = os.getenv('TRACKING_ID', 'bargainbliss_ai_bot')

def generate_md5_signature(params, secret_key):
    """Generate MD5 signature for deep link API"""
    sorted_params = sorted(params.items())
    param_string = ''.join([f"{k}{v}" for k, v in sorted_params])
    param_string += secret_key
    return hashlib.md5(param_string.encode('utf-8')).hexdigest()

def test_deep_link_api():
    print("🔍 Testing AliExpress Deep Link API")
    print("=" * 50)
    
    # Test URLs
    test_urls = [
        "https://www.aliexpress.com/item/1005007300678312.html",  # User's product
        "https://he.aliexpress.com/item/1005009632752847.html",   # Recent test
        "https://www.aliexpress.com/item/1005004842197456.html"   # Another test
    ]
    
    api_url = 'https://api.aliexpress.com/open/api/deep_link'
    
    for i, product_url in enumerate(test_urls, 1):
        print(f"\n{'='*20} Test {i} {'='*20}")
        print(f"Product URL: {product_url}")
        
        # Deep link generation parameters
        link_params = {
            'app_key': API_KEY,
            'method': 'api.link.generate',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
            'format': 'json',
            'sign_method': 'md5',
            'partner_id': TRACKING_ID,
            'promotion_link_type': 'product',
            'source_values': product_url
        }
        
        # Generate MD5 signature
        link_params['sign'] = generate_md5_signature(link_params, SECRET_KEY)
        
        print(f"API URL: {api_url}")
        print(f"Parameters: {link_params}")
        
        try:
            response = requests.get(api_url, params=link_params, timeout=10)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                if 'error_response' in data:
                    print(f"❌ API Error: {data['error_response']}")
                elif 'result' in data:
                    print(f"✅ Success! Result: {data['result']}")
                else:
                    print(f"⚠️ Unexpected response format: {data}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_deep_link_api() 