#!/usr/bin/env python3
"""
Test script to simulate browser share scenarios and detect invisible characters
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bargainbliss_ai_bot import validate_aliexpress_url_detailed, try_salvage_url

def test_browser_share_scenarios():
    """Test various browser share scenarios that might cause issues"""
    
    print("🌐 Testing Browser Share Scenarios")
    print("=" * 60)
    
    # Test cases that might simulate browser share issues
    test_cases = [
        # Normal URL
        "https://www.aliexpress.com/item/1005006996620721.html",
        
        # URL with potential invisible characters (common in browser shares)
        "https://www.aliexpress.com/item/1005006996620721.html\u200B",  # Zero-width space
        "https://www.aliexpress.com/item/1005006996620721.html\u200C",  # Zero-width non-joiner
        "https://www.aliexpress.com/item/1005006996620721.html\u200D",  # Zero-width joiner
        "https://www.aliexpress.com/item/1005006996620721.html\uFEFF",  # Byte order mark
        
        # URL with line separators (common in copy-paste from browser)
        "https://www.aliexpress.com/item/1005006996620721.html\u2028",  # Line separator
        "https://www.aliexpress.com/item/1005006996620721.html\u2029",  # Paragraph separator
        
        # URL with mixed invisible characters
        "\u200Bhttps://www.aliexpress.com/item/1005006996620721.html\u200C",
        
        # URL with trailing spaces and invisible characters
        "https://www.aliexpress.com/item/1005006996620721.html \u200B",
        
        # URL with leading invisible characters
        "\uFEFFhttps://www.aliexpress.com/item/1005006996620721.html",
    ]
    
    for i, test_url in enumerate(test_cases, 1):
        print(f"\n{'='*20} Test Case {i} {'='*20}")
        print(f"URL: '{test_url}'")
        print(f"Length: {len(test_url)}")
        print(f"Starts with https://: {test_url.startswith('https://')}")
        
        # Show invisible characters
        invisible_chars = []
        for char in test_url:
            if ord(char) < 32 or ord(char) > 126:
                invisible_chars.append(f"\\u{ord(char):04x}")
        
        if invisible_chars:
            print(f"Invisible characters: {invisible_chars}")
        
        # Test validation
        print("\n🔍 Testing validation...")
        validation_result = validate_aliexpress_url_detailed(test_url)
        print(f"Validation result: {validation_result}")
        
        if not validation_result['is_valid']:
            print(f"❌ Failed: {validation_result['error_message']}")
            
            # Test salvage
            print("\n🔧 Testing salvage...")
            salvaged_url = try_salvage_url(test_url)
            print(f"Salvaged: {salvaged_url}")
            
            if salvaged_url:
                print("🔍 Testing salvaged validation...")
                salvaged_validation = validate_aliexpress_url_detailed(salvaged_url)
                print(f"Salvaged result: {salvaged_validation}")
        else:
            print("✅ Validation passed!")
    
    print("\n" + "="*60)
    print("Test completed!")

if __name__ == "__main__":
    test_browser_share_scenarios() 