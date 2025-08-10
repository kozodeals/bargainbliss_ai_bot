#!/usr/bin/env python3
"""
Test the bot with user's specific product ID
"""

import os
from dotenv import load_dotenv
from bargainbliss_ai_bot import generate_affiliate_link

# Load environment variables
load_dotenv()

def test_specific_product():
    print("🔍 Testing Bot with User's Specific Product")
    print("=" * 50)
    
    # User's specific product ID from their affiliate link
    test_urls = [
        "https://www.aliexpress.com/item/1005007300678312.html",  # User's product
        "https://he.aliexpress.com/item/1005009632752847.html",   # Recent test
    ]
    
    for i, product_url in enumerate(test_urls, 1):
        print(f"\n{'='*20} Test {i} {'='*20}")
        print(f"Product URL: {product_url}")
        
        # Test affiliate link generation
        print("🔄 Generating affiliate link...")
        affiliate_link = generate_affiliate_link(product_url)
        
        if affiliate_link:
            print(f"✅ Generated: {affiliate_link}")
            
            # Check if it's a real affiliate link (starts with s.click.aliexpress.com)
            if affiliate_link.startswith('https://s.click.aliexpress.com/'):
                print(f"✅ REAL AFFILIATE LINK DETECTED!")
            else:
                print(f"⚠️ This appears to be a fallback link")
        else:
            print("❌ Failed to generate affiliate link")

if __name__ == "__main__":
    test_specific_product() 