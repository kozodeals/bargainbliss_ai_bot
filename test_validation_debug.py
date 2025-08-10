#!/usr/bin/env python3
"""
Debug script to test URL validation directly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bargainbliss_ai_bot import validate_aliexpress_url_detailed, try_salvage_url

def test_url_validation():
    """Test URL validation with the problematic URL"""
    
    # The URL from the screenshot
    test_url = "https://www.aliexpress.com/item/1005006996620721.html"
    
    print("🧪 Testing URL Validation")
    print("=" * 50)
    print(f"Test URL: {test_url}")
    print(f"URL length: {len(test_url)}")
    print(f"URL starts with https://: {test_url.startswith('https://')}")
    print(f"URL bytes: {test_url.encode('utf-8')}")
    
    print("\n🔍 Running validation...")
    validation_result = validate_aliexpress_url_detailed(test_url)
    
    print(f"Validation result: {validation_result}")
    
    if not validation_result['is_valid']:
        print(f"\n❌ Validation failed: {validation_result['error_message']}")
        
        print("\n🔧 Attempting to salvage...")
        salvaged_url = try_salvage_url(test_url)
        print(f"Salvaged URL: {salvaged_url}")
        
        if salvaged_url:
            print("\n🔍 Testing salvaged URL...")
            salvaged_validation = validate_aliexpress_url_detailed(salvaged_url)
            print(f"Salvaged validation result: {salvaged_validation}")
    else:
        print("\n✅ Validation passed!")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    test_url_validation() 