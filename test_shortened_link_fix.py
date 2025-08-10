#!/usr/bin/env python3
"""
Test the shortened link handling fix
"""

import os
from dotenv import load_dotenv
from bargainbliss_ai_bot import generate_affiliate_link, expand_shortened_link

# Load environment variables
load_dotenv()

def test_shortened_link():
    print("🔍 Testing Shortened Link Handling")
    print("=" * 50)
    
    # Test the shortened link that was failing
    shortened_url = "https://s.click.aliexpress.com/e/_o2EgDA2"
    
    print(f"Testing shortened URL: {shortened_url}")
    
    # Test the expansion function
    print("\n🔄 Testing link expansion...")
    expanded_url = expand_shortened_link(shortened_url)
    
    if expanded_url:
        print(f"✅ Successfully expanded to: {expanded_url}")
        
        # Test the full affiliate link generation
        print("\n🔄 Testing affiliate link generation...")
        affiliate_link = generate_affiliate_link(shortened_url)
        
        if affiliate_link:
            print(f"✅ Successfully generated affiliate link: {affiliate_link}")
        else:
            print("❌ Failed to generate affiliate link")
    else:
        print("❌ Failed to expand shortened link")

if __name__ == "__main__":
    test_shortened_link() 