#!/usr/bin/env python3
"""
Test script for shortened affiliate links
"""

import os
from dotenv import load_dotenv
from bargainbliss_ai_bot import is_valid_aliexpress_url, generate_affiliate_link

# Load environment variables
load_dotenv()

def test_shortened_links():
    print("🧪 Testing Shortened Affiliate Links")
    print("=" * 50)
    
    # Test URLs
    test_urls = [
        "https://s.click.aliexpress.com/e/_opegQu9rmat",
        "https://www.aliexpress.com/item/1005004842197456.html",
        "https://s.click.aliexpress.com/deeplink?aff_short_key=abc123",
        "https://www.aliexpress.com/s/item/1234567890.html"
    ]
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n{'='*20} Test {i} {'='*20}")
        print(f"URL: {url}")
        
        # Test URL validation
        is_valid = is_valid_aliexpress_url(url)
        print(f"✅ URL Valid: {is_valid}")
        
        if is_valid:
            # Test affiliate link generation
            print("🔄 Generating affiliate link...")
            affiliate_link = generate_affiliate_link(url)
            
            if affiliate_link:
                print(f"✅ Generated: {affiliate_link}")
            else:
                print("❌ Failed to generate affiliate link")
        else:
            print("❌ URL not valid, skipping generation")

if __name__ == "__main__":
    test_shortened_links() 