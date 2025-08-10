#!/usr/bin/env python3
"""
Test script for product ID extraction and matching
"""

import re
from urllib.parse import urlparse
from bargainbliss_ai_bot import generate_affiliate_link

def test_product_extraction():
    print("🧪 Testing Product ID Extraction")
    print("=" * 50)
    
    # Test URLs with different formats
    test_urls = [
        "https://he.aliexpress.com/item/1005007300955234.html?spm=a2g0o.productlist.main.6.6c074f8dMc9OvN",
        "https://www.aliexpress.com/item/1005004842197456.html",
        "https://us.aliexpress.com/item/1234567890.html",
        "https://s.click.aliexpress.com/e/_opegQu9rmat"
    ]
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n{'='*20} Test {i} {'='*20}")
        print(f"URL: {url}")
        
        # Extract product ID
        parsed_url = urlparse(url)
        product_id_match = re.search(r'/item/(\d+)', parsed_url.path)
        
        if product_id_match:
            product_id = product_id_match.group(1)
            print(f"✅ Extracted Product ID: {product_id}")
            print(f"✅ Domain: {parsed_url.netloc}")
            
            # Test affiliate link generation
            print("🔄 Generating affiliate link...")
            affiliate_link = generate_affiliate_link(url)
            
            if affiliate_link:
                print(f"✅ Generated: {affiliate_link}")
                
                # Check if the generated link contains the same product ID
                if product_id in affiliate_link:
                    print(f"✅ Product ID preserved in generated link")
                else:
                    print(f"⚠️ Product ID may not be preserved")
            else:
                print("❌ Failed to generate affiliate link")
        else:
            print("❌ Could not extract product ID")
            print("ℹ️ This might be a shortened link")

if __name__ == "__main__":
    test_product_extraction() 