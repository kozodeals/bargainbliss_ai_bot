#!/usr/bin/env python3
"""
Test Standard API methods that should work with current permissions
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
    """Generate MD5 signature for AliExpress API"""
    sorted_params = sorted(params.items())
    param_string = ''.join([f"{k}{v}" for k, v in sorted_params])
    param_string += secret_key
    return hashlib.md5(param_string.encode('utf-8')).hexdigest()

def test_standard_api():
    print("🔍 Testing Standard API Methods")
    print("=" * 50)
    
    # Test URLs
    test_urls = [
        "https://www.aliexpress.com/item/1005007300678312.html",  # User's product
        "https://he.aliexpress.com/item/1005009632752847.html",   # Recent test
    ]
    
    # Try different API endpoints and methods
    api_configs = [
        {
            'name': 'Standard API - Product Query',
            'url': 'https://api-sg.aliexpress.com/sync',
            'method': 'aliexpress.affiliate.product.query',
            'params': {
                'app_key': API_KEY,
                'method': 'aliexpress.affiliate.product.query',
                'format': 'json',
                'v': '2.0',
                'sign_method': 'sha256',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
                'keywords': 'phone',
                'tracking_id': TRACKING_ID
            },
            'sign_method': 'hmac_sha256'
        },
        {
            'name': 'Standard API - Link Generate',
            'url': 'https://api-sg.aliexpress.com/sync',
            'method': 'aliexpress.affiliate.link.generate',
            'params': {
                'app_key': API_KEY,
                'method': 'aliexpress.affiliate.link.generate',
                'format': 'json',
                'v': '2.0',
                'sign_method': 'sha256',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
                'product_id': '1005007300678312',
                'tracking_id': TRACKING_ID,
                'source_url': 'https://www.aliexpress.com/item/1005007300678312.html',
                'promotion_link_type': '0',
                'source_values': 'telegram_bot'
            },
            'sign_method': 'hmac_sha256'
        }
    ]
    
    for i, config in enumerate(api_configs, 1):
        print(f"\n{'='*20} Test {i}: {config['name']} {'='*20}")
        print(f"API URL: {config['url']}")
        print(f"Method: {config['method']}")
        
        params = config['params'].copy()
        
        # Generate signature based on method
        if config['sign_method'] == 'hmac_sha256':
            import hmac
            sorted_params = sorted(params.items())
            param_string = ''.join([f"{k}{v}" for k, v in sorted_params])
            signature = hmac.new(
                SECRET_KEY.encode('utf-8'),
                param_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest().upper()
            params['sign'] = signature
        else:
            params['sign'] = generate_md5_signature(params, SECRET_KEY)
        
        try:
            # Make GET request for sync API
            response = requests.get(config['url'], params=params, timeout=10)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text[:500]}...")
            
            if response.status_code == 200:
                data = response.json()
                if 'error_response' in data:
                    print(f"❌ API Error: {data['error_response']}")
                else:
                    print(f"✅ Success! Response structure: {list(data.keys())}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_standard_api() 