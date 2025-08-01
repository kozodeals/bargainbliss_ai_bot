#!/usr/bin/env python3
"""
Test script to find the correct AliExpress affiliate API endpoint
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

def generate_hmac_signature(params, secret_key):
    """Generate HMAC-SHA256 signature for AliExpress API"""
    # Sort parameters by key and concatenate
    sorted_params = sorted(params.items())
    param_string = ''.join([f"{k}{v}" for k, v in sorted_params])
    
    # Generate HMAC-SHA256 signature
    signature = hmac.new(
        secret_key.encode('utf-8'),
        param_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return signature

def generate_hmac_signature_upper(params, secret_key):
    """Generate HMAC-SHA256 signature in uppercase"""
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

def generate_md5_signature(params, secret_key):
    """Generate MD5 signature for legacy API compatibility"""
    # Sort parameters by key and concatenate
    sorted_params = sorted(params.items())
    param_string = ''.join([f"{k}{v}" for k, v in sorted_params])
    param_string += secret_key
    return hashlib.md5(param_string.encode('utf-8')).hexdigest()

def generate_md5_signature_upper(params, secret_key):
    """Generate MD5 signature in uppercase"""
    # Sort parameters by key and concatenate
    sorted_params = sorted(params.items())
    param_string = ''.join([f"{k}{v}" for k, v in sorted_params])
    param_string += secret_key
    return hashlib.md5(param_string.encode('utf-8')).hexdigest().upper()

def generate_signature_without_sign(params, secret_key):
    """Generate signature without including 'sign' parameter"""
    # Remove 'sign' parameter if present
    params_copy = {k: v for k, v in params.items() if k != 'sign'}
    
    # Sort parameters by key and concatenate
    sorted_params = sorted(params_copy.items())
    param_string = ''.join([f"{k}{v}" for k, v in sorted_params])
    param_string += secret_key
    
    return hashlib.md5(param_string.encode('utf-8')).hexdigest().upper()

def test_api_endpoint(api_url, params, endpoint_name):
    """Test a specific API endpoint"""
    print(f"\n🔍 Testing: {endpoint_name}")
    print(f"URL: {api_url}")
    print(f"Params: {params}")
    
    try:
        response = requests.get(api_url, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:500]}...")
        
        if response.status_code == 200:
            data = response.json()
            if 'error_response' in data:
                print(f"❌ API Error: {data['error_response']}")
                return False
            elif 'result' in data:
                print(f"✅ Success! Result: {data['result']}")
                return True
            else:
                print(f"⚠️ Unexpected response format: {data}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    print("🧪 Testing AliExpress Affiliate API Endpoints")
    print("=" * 50)
    
    # Test product URL
    test_url = "https://www.aliexpress.com/item/1005004842197456.html"
    
    # Extract product ID
    parsed_url = urlparse(test_url)
    product_id_match = re.search(r'/item/(\d+)', parsed_url.path)
    product_id = product_id_match.group(1) if product_id_match else "1005004842197456"
    
    print(f"Testing with product ID: {product_id}")
    print(f"API Key: {API_KEY}")
    print(f"Secret Key: {SECRET_KEY[:10]}...")
    print(f"Tracking ID: {TRACKING_ID}")
    
    # Test different endpoints
    endpoints_to_test = [
        {
            'name': 'AliExpress API (HMAC-SHA256)',
            'url': 'https://api-sg.aliexpress.com/sync',
            'params': {
                'app_key': API_KEY,
                'method': 'aliexpress.affiliate.link.generate',
                'format': 'json',
                'v': '2.0',
                'sign_method': 'sha256',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
                'product_id': product_id,
                'tracking_id': TRACKING_ID,
                'source_url': test_url
            },
            'signature_method': 'hmac'
        },
        {
            'name': 'AliExpress API (HMAC-SHA256 Upper)',
            'url': 'https://api-sg.aliexpress.com/sync',
            'params': {
                'app_key': API_KEY,
                'method': 'aliexpress.affiliate.link.generate',
                'format': 'json',
                'v': '2.0',
                'sign_method': 'sha256',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
                'product_id': product_id,
                'tracking_id': TRACKING_ID,
                'source_url': test_url
            },
            'signature_method': 'hmac_upper'
        },
        {
            'name': 'AliExpress API (MD5)',
            'url': 'https://api-sg.aliexpress.com/sync',
            'params': {
                'app_key': API_KEY,
                'method': 'aliexpress.affiliate.link.generate',
                'format': 'json',
                'v': '2.0',
                'sign_method': 'md5',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
                'product_id': product_id,
                'tracking_id': TRACKING_ID,
                'source_url': test_url
            },
            'signature_method': 'md5'
        },
        {
            'name': 'AliExpress API (MD5 Upper)',
            'url': 'https://api-sg.aliexpress.com/sync',
            'params': {
                'app_key': API_KEY,
                'method': 'aliexpress.affiliate.link.generate',
                'format': 'json',
                'v': '2.0',
                'sign_method': 'md5',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
                'product_id': product_id,
                'tracking_id': TRACKING_ID,
                'source_url': test_url
            },
            'signature_method': 'md5_upper'
        },
        {
            'name': 'AliExpress API (MD5 without sign)',
            'url': 'https://api-sg.aliexpress.com/sync',
            'params': {
                'app_key': API_KEY,
                'method': 'aliexpress.affiliate.link.generate',
                'format': 'json',
                'v': '2.0',
                'sign_method': 'md5',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
                'product_id': product_id,
                'tracking_id': TRACKING_ID,
                'source_url': test_url
            },
            'signature_method': 'md5_without_sign'
        },
        {
            'name': 'Alibaba Legacy API',
            'url': 'http://gw.api.alibaba.com/openapi/param2/2/portals.open/api.getPromotionLinks',
            'params': {
                'appKey': API_KEY,
                'apiName': 'api.getPromotionLinks',
                'fields': 'totalResults,trackingId,publisherId,url,promotionUrl',
                'trackingId': TRACKING_ID,
                'urls': test_url,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
            },
            'signature_method': 'md5'
        }
    ]
    
    working_endpoints = []
    
    for endpoint in endpoints_to_test:
        # Generate signature based on method
        params = endpoint['params'].copy()
        if endpoint['signature_method'] == 'hmac':
            params['sign'] = generate_hmac_signature(params, SECRET_KEY)
        elif endpoint['signature_method'] == 'hmac_upper':
            params['sign'] = generate_hmac_signature_upper(params, SECRET_KEY)
        elif endpoint['signature_method'] == 'md5':
            params['sign'] = generate_md5_signature(params, SECRET_KEY)
        elif endpoint['signature_method'] == 'md5_upper':
            params['sign'] = generate_md5_signature_upper(params, SECRET_KEY)
        elif endpoint['signature_method'] == 'md5_without_sign':
            params['sign'] = generate_signature_without_sign(params, SECRET_KEY)
        
        if test_api_endpoint(endpoint['url'], params, endpoint['name']):
            working_endpoints.append(endpoint['name'])
    
    print("\n" + "=" * 50)
    print("📊 RESULTS SUMMARY")
    print("=" * 50)
    
    if working_endpoints:
        print("✅ Working endpoints:")
        for endpoint in working_endpoints:
            print(f"   • {endpoint}")
    else:
        print("❌ No working endpoints found")
        print("\n💡 Suggestions:")
        print("   1. Check if your API credentials are correct")
        print("   2. Verify your AliExpress affiliate account is active")
        print("   3. Check if the API endpoints have changed")
        print("   4. Contact AliExpress affiliate support")

if __name__ == "__main__":
    main() 