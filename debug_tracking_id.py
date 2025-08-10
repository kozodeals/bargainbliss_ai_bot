#!/usr/bin/env python3
"""
Debug script to check tracking ID
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get tracking ID
TRACKING_ID = os.getenv('TRACKING_ID', 'c01b8d720c9941f5bfbef6686e96e90a')

print(f"TRACKING_ID from environment: {TRACKING_ID}")

# Test the fallback method
from bargainbliss_ai_bot import generate_affiliate_link_fallback

test_url = "https://he.aliexpress.com/item/1005007500365472.html"
result = generate_affiliate_link_fallback(test_url)

if result:
    print(f"\nGenerated link: {result}")
    
    # Check if it contains the correct tracking ID
    if TRACKING_ID in result:
        print(f"✅ CORRECT TRACKING ID FOUND: {TRACKING_ID}")
    else:
        print(f"❌ WRONG TRACKING ID! Expected: {TRACKING_ID}")
        
    # Extract terminal_id from the result
    import re
    terminal_id_match = re.search(r'terminal_id=([^&]+)', result)
    if terminal_id_match:
        actual_terminal_id = terminal_id_match.group(1)
        print(f"Actual terminal_id in result: {actual_terminal_id}")
        print(f"Expected terminal_id: {TRACKING_ID}")
        print(f"Match: {'✅' if actual_terminal_id == TRACKING_ID else '❌'}")
else:
    print("❌ Failed to generate link") 