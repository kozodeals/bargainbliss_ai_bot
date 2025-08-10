#!/usr/bin/env python3
"""
Test script to check IP whitelist issues
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

def test_ip_whitelist():
    print("🔍 Testing IP Whitelist Issues")
    print("=" * 50)
    
    # Test a simple API call to see if IP is blocked
    api_url = 'https://api-sg.aliexpress.com/sync'
    
    # Simple product query to test connectivity
    params = {
        'app_key': API_KEY,
        'method': 'aliexpress.affiliate.product.query',
        'format': 'json',
        'v': '2.0',
        'sign_method': 'sha256',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
        'keywords': 'phone',  # Simple keyword
        'tracking_id': TRACKING_ID
    }
    
    params['sign'] = generate_hmac_signature_upper(params, SECRET_KEY)
    
    print(f"Testing API connectivity...")
    print(f"API Key: {API_KEY}")
    print(f"Secret Key: {SECRET_KEY[:10]}...")
    
    try:
        response = requests.get(api_url, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:500]}...")
        
        if response.status_code == 200:
            data = response.json()
            if 'error_response' in data:
                error_msg = data['error_response'].get('msg', '')
                if 'AppWhiteIpLimit' in error_msg:
                    print("❌ IP WHITELIST ISSUE DETECTED!")
                    print("💡 Your IP address is not in the AliExpress affiliate whitelist")
                    print("💡 You need to add your IP to the whitelist in your affiliate dashboard")
                else:
                    print(f"❌ Other API Error: {data['error_response']}")
            else:
                print("✅ API connection successful - IP is not the issue")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_ip_whitelist() 