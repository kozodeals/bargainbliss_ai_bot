#!/usr/bin/env python3
"""
Test script to verify URL validation works with country-specific AliExpress domains
"""

from bargainbliss_ai_bot import is_valid_aliexpress_url, generate_affiliate_link_alternative

def test_url_validation():
    """Test URL validation with various AliExpress URLs"""
    print("🔍 Testing URL validation...")
    
    # Test URLs (including the one from the screenshot)
    test_urls = [
        "https://he.aliexpress.com/item/1005007300955234.html?spm=a2g0o.productlist.main.6.6c074f8dMc9OvN&algo_pvid=0e463815-b3a3-417c-a8de-5d46b408beab&algo_exp_id=0e463815-b3a3-417c-a8de-5d46b408beab-5&pdp_ext_f=%7B%22order%22%3A%22233622%2C%22eval%22%3A%221%22%7D&pdp_npi=4%40dis%21ILS%2192.26%2166.21%21%21%2126.56%2119.066216402140f54217540451891392525e1bf362112000040119474583621sea%21IL%216153981600621ABX&curPageLogUid=GnPjkRxHcbmB&utparam-url=scene%3Asearch%7Cquery_from%3A",
        "https://www.aliexpress.com/item/1234567890.html",
        "https://m.aliexpress.com/item/1234567890.html",
        "https://us.aliexpress.com/item/1234567890.html",
        "https://fr.aliexpress.com/item/1234567890.html",
        "https://invalid.com/item/1234567890.html",  # Should fail
        "https://aliexpress.com/item/1234567890.html"  # Should work
    ]
    
    for i, url in enumerate(test_urls, 1):
        is_valid = is_valid_aliexpress_url(url)
        status = "✅ VALID" if is_valid else "❌ INVALID"
        print(f"{i}. {status}: {url[:80]}...")
        
        if is_valid:
            # Test affiliate link generation
            affiliate_link = generate_affiliate_link_alternative(url)
            if affiliate_link:
                print(f"   🔗 Generated: {affiliate_link[:80]}...")
            else:
                print("   ❌ Failed to generate affiliate link")
    
    print("\n" + "="*60)
    print("📊 VALIDATION TEST SUMMARY")
    print("="*60)
    
    # Test the specific URL from the screenshot
    screenshot_url = "https://he.aliexpress.com/item/1005007300955234.html?spm=a2g0o.productlist.main.6.6c074f8dMc9OvN&algo_pvid=0e463815-b3a3-417c-a8de-5d46b408beab&algo_exp_id=0e463815-b3a3-417c-a8de-5d46b408beab-5&pdp_ext_f=%7B%22order%22%3A%22233622%2C%22eval%22%3A%221%22%7D&pdp_npi=4%40dis%21ILS%2192.26%2166.21%21%21%2126.56%2119.066216402140f54217540451891392525e1bf362112000040119474583621sea%21IL%216153981600621ABX&curPageLogUid=GnPjkRxHcbmB&utparam-url=scene%3Asearch%7Cquery_from%3A"
    
    if is_valid_aliexpress_url(screenshot_url):
        print("✅ Screenshot URL is now VALID")
        affiliate_link = generate_affiliate_link_alternative(screenshot_url)
        if affiliate_link:
            print(f"✅ Generated affiliate link: {affiliate_link}")
        else:
            print("❌ Failed to generate affiliate link")
    else:
        print("❌ Screenshot URL is still INVALID")

if __name__ == "__main__":
    test_url_validation() 