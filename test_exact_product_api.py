#!/usr/bin/env python3
"""
Test script to find the correct API method for exact product queries
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
    sorted_params = sorted(params.items())
    param_string = ''.join([f"{k}{v}" for k, v in sorted_params])
    signature = hmac.new(
        secret_key.encode('utf-8'),
        param_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest().upper()
    return signature

def test_api_methods():
    print("🔍 Testing AliExpress API Methods for Exact Product Queries")
    print("=" * 60)
    
    # Test product ID from user's example
    product_id = "1005007300678312"  # From user's affiliate link
    
    print(f"Testing with Product ID: {product_id}")
    print(f"API Key: {API_KEY}")
    print(f"Secret Key: {SECRET_KEY[:10]}...")
    print(f"Tracking ID: {TRACKING_ID}")
    
    api_url = 'https://api-sg.aliexpress.com/sync'
    
    # Test different API methods
    methods_to_test = [
        {
            'name': 'aliexpress.affiliate.product.details.get',
            'params': {
                'app_key': API_KEY,
                'method': 'aliexpress.affiliate.product.details.get',
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
            'name': 'aliexpress.affiliate.product.query (with exact ID)',
            'params': {
                'app_key': API_KEY,
                'method': 'aliexpress.affiliate.product.query',
                'format': 'json',
                'v': '2.0',
                'sign_method': 'sha256',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
                'product_ids': product_id,  # Try product_ids instead of keywords
                'tracking_id': TRACKING_ID
            }
        },
        {
            'name': 'aliexpress.affiliate.product.query (with product_id)',
            'params': {
                'app_key': API_KEY,
                'method': 'aliexpress.affiliate.product.query',
                'format': 'json',
                'v': '2.0',
                'sign_method': 'sha256',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
                'product_id': product_id,  # Try product_id parameter
                'tracking_id': TRACKING_ID
            }
        },
        {
            'name': 'aliexpress.affiliate.link.generate (direct)',
            'params': {
                'app_key': API_KEY,
                'method': 'aliexpress.affiliate.link.generate',
                'format': 'json',
                'v': '2.0',
                'sign_method': 'sha256',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
                'product_id': product_id,
                'tracking_id': TRACKING_ID,
                'source_url': f"https://www.aliexpress.com/item/{product_id}.html",
                'promotion_link_type': '0',
                'source_values': 'telegram_bot'
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
                else:
                    print(f"✅ Success! Response structure: {list(data.keys())}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_api_methods() 