#!/usr/bin/env python3
"""
Test new API approach based on the provided scripts
"""

import requests
import time
import hmac
import hashlib
import os
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get credentials
API_KEY = os.getenv('ALIEXPRESS_API_KEY') or os.getenv('AFFILIATE_API_KEY')
SECRET_KEY = os.getenv('ALIEXPRESS_SECRET_KEY') or os.getenv('AFFILIATE_SECRET_KEY')
TRACKING_ID = os.getenv('TRACKING_ID', 'c01b8d720c9941f5bfbef6686e96e90a')

def generate_hmac_signature_upper(params, secret_key):
    """Generate HMAC-SHA256 signature in uppercase"""
    sorted_params = sorted(params.items())
    param_string = ''.join([f'{k}{v}' for k, v in sorted_params])
    signature = hmac.new(
        secret_key.encode('utf-8'),
        param_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest().upper()
    return signature

def extract_product_id_from_url(url):
    """Extract product ID from AliExpress URL"""
    patterns = [
        r'/item/(\d+)\.html',
        r'product_id=(\d+)',
        r'item/(\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def test_new_api_approach(product_url, use_tracking_id=True):
    """Test the new API approach based on the provided scripts"""
    print("🔍 Testing New API Approach")
    print("=" * 50)
    
    product_id = extract_product_id_from_url(product_url)
    if not product_id:
        print(f"❌ Could not extract product ID from: {product_url}")
        return None
    
    print(f"✅ Extracted product ID: {product_id}")
    
    api_url = 'https://api-sg.aliexpress.com/sync'
    
    # Build parameters similar to the working scripts
    params = {
        'app_key': API_KEY,
        'method': 'aliexpress.affiliate.product.query',
        'format': 'json',
        'v': '2.0',
        'sign_method': 'sha256',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
        'fields': 'product_id,product_title,target_sale_price,product_main_image_url,promotion_link,product_detail_url,product_origin,product_shipping,product_weight,product_dimensions,original_price,discount,product_rating,product_review_count,product_sales,product_shop_name,evaluate_rate,lastest_volume',
        'product_ids': product_id,
        'currency': 'ILS',
        'language': 'IL',
        'targetLanguage': 'IL',
        'isMultiLanguage': 'true',
        'locale': 'IL_IL',
        'ship_to_country': 'IL',
        'page_no': '1',
        'page_size': '1'
    }
    
    # Try different tracking_id parameter names
    if use_tracking_id:
        # Try different parameter names for tracking_id
        tracking_params = [
            ('tracking_id', TRACKING_ID),
            ('trackingId', TRACKING_ID),
            ('tracking-id', TRACKING_ID),
            ('trackingid', TRACKING_ID),
        ]
        
        for param_name, param_value in tracking_params:
            print(f"\n🔄 Trying with {param_name}: {param_value}")
            test_params = params.copy()
            test_params[param_name] = param_value
            test_params['sign'] = generate_hmac_signature_upper(test_params, SECRET_KEY)
            
            try:
                response = requests.get(api_url, params=test_params, timeout=15)
                print(f"📊 Response Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"📄 Response Data: {data}")
                    
                    if 'aliexpress_affiliate_product_query_response' in data:
                        resp = data['aliexpress_affiliate_product_query_response']
                        
                        if 'resp_result' in resp:
                            resp_result = resp['resp_result']
                            # Check if resp_code is 0 (success) or 200 (success)
                            if resp_result.get('resp_code') in [0, 200]:  # Success
                                if 'result' in resp_result:
                                    products_data = resp_result['result']['products']
                                    products = products_data['product'] if isinstance(products_data['product'], list) else [products_data['product']]
                                    
                                    if products:
                                        product = products[0]
                                        print("\n" + "="*60)
                                        print("📦 PRODUCT DETAILS")
                                        print("="*60)
                                        print(f"Product ID: {product.get('product_id', 'N/A')}")
                                        print(f"Title: {product.get('product_title', 'N/A')}")
                                        print(f"Shop: {product.get('shop_name', 'N/A')}")
                                        print(f"\n💰 PRICING")
                                        print(f"Sale Price: {product.get('target_sale_price', 'N/A')} {product.get('target_sale_price_currency', 'N/A')}")
                                        print(f"Original Price: {product.get('original_price', 'N/A')} {product.get('original_price_currency', 'N/A')}")
                                        print(f"Discount: {product.get('discount', 'N/A')}")
                                        print(f"\n🔗 LINKS")
                                        print(f"Product URL: {product.get('product_detail_url', 'N/A')}")
                                        print(f"Image URL: {product.get('product_main_image_url', 'N/A')}")
                                        print(f"Promotion Link: {product.get('promotion_link', 'N/A')}")
                                        
                                        promotion_link = product.get('promotion_link')
                                        if promotion_link:
                                            print(f"\n✅ SUCCESS! Got real promotion link from API: {promotion_link}")
                                            return promotion_link
                                        else:
                                            print(f"\n❌ No promotion link in API response")
                                            continue
                                    else:
                                        print("❌ No products found in API response")
                                        continue
                                else:
                                    print("❌ No result in API response")
                                    continue
                            else:
                                print(f"❌ API Error: {resp_result.get('resp_msg', 'Unknown error')}")
                                continue
                        else:
                            print("❌ Invalid API response structure")
                            continue
                    else:
                        print("❌ No aliexpress_affiliate_product_query_response in data")
                        continue
                else:
                    print(f"❌ HTTP Error: {response.status_code}")
                    print(f"Response: {response.text}")
                    continue
                    
            except Exception as e:
                print(f"❌ Error making API request: {e}")
                continue
    
    # If all tracking_id attempts failed, try without tracking_id
    print(f"\n🔄 Trying without tracking_id parameter...")
    params['sign'] = generate_hmac_signature_upper(params, SECRET_KEY)
    
    try:
        response = requests.get(api_url, params=params, timeout=15)
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📄 Response Data: {data}")
            
            if 'aliexpress_affiliate_product_query_response' in data:
                resp = data['aliexpress_affiliate_product_query_response']
                
                if 'resp_result' in resp:
                    resp_result = resp['resp_result']
                    # Check if resp_code is 0 (success) or 200 (success)
                    if resp_result.get('resp_code') in [0, 200]:  # Success
                        if 'result' in resp_result:
                            products_data = resp_result['result']['products']
                            products = products_data['product'] if isinstance(products_data['product'], list) else [products_data['product']]
                            
                            if products:
                                product = products[0]
                                print("\n" + "="*60)
                                print("📦 PRODUCT DETAILS")
                                print("="*60)
                                print(f"Product ID: {product.get('product_id', 'N/A')}")
                                print(f"Title: {product.get('product_title', 'N/A')}")
                                print(f"Shop: {product.get('shop_name', 'N/A')}")
                                print(f"\n💰 PRICING")
                                print(f"Sale Price: {product.get('target_sale_price', 'N/A')} {product.get('target_sale_price_currency', 'N/A')}")
                                print(f"Original Price: {product.get('original_price', 'N/A')} {product.get('original_price_currency', 'N/A')}")
                                print(f"Discount: {product.get('discount', 'N/A')}")
                                print(f"\n🔗 LINKS")
                                print(f"Product URL: {product.get('product_detail_url', 'N/A')}")
                                print(f"Image URL: {product.get('product_main_image_url', 'N/A')}")
                                print(f"Promotion Link: {product.get('promotion_link', 'N/A')}")
                                
                                promotion_link = product.get('promotion_link')
                                if promotion_link:
                                    print(f"\n✅ SUCCESS! Got real promotion link from API: {promotion_link}")
                                    return promotion_link
                                else:
                                    print(f"\n❌ No promotion link in API response")
                                    return None
                            else:
                                print("❌ No products found in API response")
                                return None
                        else:
                            print("❌ No result in API response")
                            return None
                    else:
                        print(f"❌ API Error: {resp_result.get('resp_msg', 'Unknown error')}")
                        return None
                else:
                    print("❌ Invalid API response structure")
                    return None
            else:
                print("❌ No aliexpress_affiliate_product_query_response in data")
                return None
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error making API request: {e}")
        return None

def main():
    """Main function"""
    test_url = "https://he.aliexpress.com/item/1005004896181006.html"
    print(f"🧪 Testing with URL: {test_url}")
    
    result = test_new_api_approach(test_url)
    
    if result:
        print(f"\n🎉 SUCCESS! Real affiliate link from API: {result}")
    else:
        print(f"\n❌ Failed to get real affiliate link from API")

if __name__ == "__main__":
    main() 