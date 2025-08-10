#!/usr/bin/env python3
"""
Comprehensive test of the bot functionality
"""

import os
from dotenv import load_dotenv
from bargainbliss_ai_bot import generate_affiliate_link, is_valid_aliexpress_url

# Load environment variables
load_dotenv()

def test_bot_comprehensive():
    print("🔍 Comprehensive Bot Test")
    print("=" * 50)
    
    # Test different types of URLs
    test_cases = [
        {
            'name': 'User\'s Product (Real API)',
            'url': 'https://www.aliexpress.com/item/1005007300678312.html',
            'expected': 'Real affiliate link'
        },
        {
            'name': 'Hebrew Domain Product',
            'url': 'https://he.aliexpress.com/item/1005009632752847.html',
            'expected': 'Real affiliate link'
        },
        {
            'name': 'Shortened Affiliate Link',
            'url': 'https://s.click.aliexpress.com/e/_opegQu9rmat',
            'expected': 'Tracking-enhanced link'
        },
        {
            'name': 'Invalid URL',
            'url': 'https://www.amazon.com/item/123.html',
            'expected': 'Should be rejected'
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*20} Test {i}: {test_case['name']} {'='*20}")
        print(f"URL: {test_case['url']}")
        
        # Test URL validation
        is_valid = is_valid_aliexpress_url(test_case['url'])
        print(f"URL Valid: {is_valid}")
        
        if is_valid:
            # Test affiliate link generation
            print("🔄 Generating affiliate link...")
            affiliate_link = generate_affiliate_link(test_case['url'])
            
            if affiliate_link:
                print(f"✅ Generated: {affiliate_link}")
                
                # Analyze the generated link
                if affiliate_link.startswith('https://s.click.aliexpress.com/'):
                    print(f"✅ REAL AFFILIATE LINK - This will track to your account!")
                elif 'aff_fcid=' in affiliate_link and 'terminal_id=' in affiliate_link:
                    print(f"✅ TRACKING-ENHANCED LINK - Uses your affiliate parameters")
                else:
                    print(f"⚠️ UNKNOWN LINK FORMAT")
            else:
                print("❌ Failed to generate affiliate link")
        else:
            print("❌ URL rejected (as expected)")
    
    print(f"\n{'='*50}")
    print("📊 SUMMARY:")
    print("✅ Bot should generate real affiliate links for valid AliExpress URLs")
    print("✅ Bot should handle shortened links with tracking parameters")
    print("✅ Bot should reject invalid URLs")
    print("✅ All links should track to your affiliate account")

if __name__ == "__main__":
    test_bot_comprehensive() 