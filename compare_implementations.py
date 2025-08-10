#!/usr/bin/env python3
"""
Test script to compare both AliExpress API implementations
"""

import os
import json
import logging
import time
import hmac
import hashlib
import requests
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Load credentials
API_KEY = os.getenv('AFFILIATE_API_KEY') or os.getenv('ALIBABA_API_KEY') or os.getenv('ALIEXPRESS_API_KEY')
SECRET_KEY = os.getenv('AFFILIATE_SECRET_KEY') or os.getenv('ALIBABA_SECRET_KEY') or os.getenv('ALIEXPRESS_SECRET_KEY')
TRACKING_ID = os.getenv('TRACKING_ID', 'c01b8d720c9941f5bfbef6686e96e90a')

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

def test_current_implementation(product_url):
    """Test our current implementation"""
    logger.info("\n=== Testing Current Implementation ===")
    
    base_url = product_url.split('?')[0] if '?' in product_url else product_url
    api_url = 'https://api-sg.aliexpress.com/sync'
    
    params = {
        'app_key': API_KEY,
        'method': 'aliexpress.affiliate.link.generate',
        'format': 'json',
        'v': '2.0',
        'sign_method': 'sha256',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
        'source_values': base_url,
        'tracking_id': TRACKING_ID,
        'promotion_link_type': '1',
        'target_currency': 'ILS',
        'target_language': 'IL'
    }
    
    params['sign'] = generate_hmac_signature_upper(params, SECRET_KEY)
    
    logger.info(f"Request URL: {api_url}")
    logger.info(f"Parameters: {json.dumps(params, indent=2)}")
    
    response = requests.get(api_url, params=params, timeout=15)
    logger.info(f"Response Status: {response.status_code}")
    logger.info(f"Response Data: {json.dumps(response.json(), indent=2)}")
    
    return response.json()

def test_working_implementation(product_url):
    """Test the working implementation from bot_queue.py"""
    logger.info("\n=== Testing Working Implementation ===")
    
    base_url = product_url.split('?')[0] if '?' in product_url else product_url
    api_url = 'https://api-sg.aliexpress.com/sync'
    
    params = {
        'app_key': API_KEY,
        'method': 'aliexpress.affiliate.link.generate',
        'format': 'json',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
        'sign_method': 'sha256',
        'v': '2.0',
        'source_values': base_url,
        'tracking_id': TRACKING_ID,
        'promotion_link_type': '1'
    }
    
    params['sign'] = generate_hmac_signature_upper(params, SECRET_KEY)
    
    logger.info(f"Request URL: {api_url}")
    logger.info(f"Parameters: {json.dumps(params, indent=2)}")
    
    response = requests.get(api_url, params=params, timeout=15)
    logger.info(f"Response Status: {response.status_code}")
    logger.info(f"Response Data: {json.dumps(response.json(), indent=2)}")
    
    return response.json()

def main():
    """Main test function"""
    # Test URL (use a real AliExpress product URL)
    test_url = "https://he.aliexpress.com/item/1005009533140539.html"
    
    logger.info("Starting comparison test...")
    logger.info(f"Testing with URL: {test_url}")
    logger.info(f"Using API Key: {API_KEY[:8]}...")
    logger.info(f"Using Tracking ID: {TRACKING_ID}")
    
    # Test both implementations
    current_result = test_current_implementation(test_url)
    logger.info("\n" + "="*50 + "\n")
    working_result = test_working_implementation(test_url)
    
    # Compare results
    logger.info("\n=== Comparison Results ===")
    if current_result != working_result:
        logger.info("Implementations produced different results!")
        
        # Compare response structures
        if 'aliexpress_affiliate_link_generate_response' in current_result:
            logger.info("Current implementation response has correct structure")
        else:
            logger.info("Current implementation response missing expected structure")
            
        if 'aliexpress_affiliate_link_generate_response' in working_result:
            logger.info("Working implementation response has correct structure")
        else:
            logger.info("Working implementation response missing expected structure")
    else:
        logger.info("Both implementations produced identical results")

if __name__ == "__main__":
    main() 