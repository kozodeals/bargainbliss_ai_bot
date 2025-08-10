#!/usr/bin/env python3
"""
Test the new fallback method with correct tracking ID
"""

import os
from dotenv import load_dotenv
from bargainbliss_ai_bot import generate_affiliate_link_fallback, generate_affiliate_link

# Load environment variables
load_dotenv()

def test_fallback_method():
    print("🔍 Testing New Fallback Method with Correct Tracking ID")
    print("=" * 60)
    
    # Get the actual tracking ID from environment
    TRACKING_ID = os.getenv('TRACKING_ID', 'c01b8d720c9941f5bfbef6686e96e90a')
    print(f"Using tracking ID: {TRACKING_ID}")
    
    # Test URLs
    test_urls = [
        "https://he.aliexpress.com/item/1005007500365472.html",
        "https://www.aliexpress.com/item/1005001234567890.html",
        "https://us.aliexpress.com/item/1005009876543210.html"
    ]
    
    for i, test_url in enumerate(test_urls, 1):
        print(f"\n{'='*20} Test {i} {'='*20}")
        print(f"Input URL: {test_url}")
        
        # Test fallback method directly
        print("\n🔄 Testing Fallback Method...")
        fallback_result = generate_affiliate_link_fallback(test_url)
        
        if fallback_result:
            print(f"✅ Fallback Result: {fallback_result}")
            
            # Check if it has the correct tracking ID
            if f'terminal_id={TRACKING_ID}' in fallback_result:
                print("✅ CORRECT TRACKING ID FOUND!")
            else:
                print("❌ WRONG TRACKING ID!")
                
            # Check if it has all required parameters
            required_params = ['aff_fcid=', 'tt=CPS_NORMAL', 'aff_fsk=', 'aff_platform=shareComponent-detail', 'terminal_id=']
            missing_params = [param for param in required_params if param not in fallback_result]
            
            if not missing_params:
                print("✅ ALL REQUIRED PARAMETERS FOUND!")
            else:
                print(f"❌ MISSING PARAMETERS: {missing_params}")
        else:
            print("❌ Fallback method failed")
        
        # Test the main method (which will use fallback if API fails)
        print("\n🔄 Testing Main Method...")
        main_result = generate_affiliate_link(test_url)
        
        if main_result:
            print(f"✅ Main Result: {main_result}")
            
            # Check if it has the correct tracking ID
            if f'terminal_id={TRACKING_ID}' in main_result:
                print("✅ CORRECT TRACKING ID FOUND!")
            else:
                print("❌ WRONG TRACKING ID!")
        else:
            print("❌ Main method failed")

if __name__ == "__main__":
    test_fallback_method() 