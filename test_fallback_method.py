#!/usr/bin/env python3
"""
Test the fallback method with the problematic product
"""

import os
from dotenv import load_dotenv
from bargainbliss_ai_bot import generate_affiliate_link

# Load environment variables
load_dotenv()

def test_fallback_method():
    print("🔍 Testing Fallback Method with Problematic Product")
    print("=" * 50)
    
    # The problematic product that the API failed with
    test_url = "https://he.aliexpress.com/item/1005007500365472.html?spm=a2g0o.detail.pcDetailTopMoreOtherSeller.3.2c3dcEDrcEDrhr&gps-id=pcDetailTopMoreOtherSeller&scm=1007.40196.439370.0&scm_id=1007.40196.439370.0&scm-url=1007.40196.439370.0&pvid=7fef5fbd-bdad-4783-9485-0191f9913302&_t=gps-id:pcDetailTopMoreOtherSeller,scm-url:1007.40196.439370.0,pvid:7fef5fbd-bdad-4783-9485-0191f9913302,tpp_buckets:668%232846%238110%231995&pdp_ext_f=%7B%22order%22%3A%2216174%22%2C%22eval%22%3A%221%22%2C%22sceneId%22%3A%2230050%22%7D&pdp_npi=4%40dis%21ILS%2140.61%213.44%21%21%2184.40%217.15%21%402141115b17541720116478653ee2d1%2112000049127616703%21rec%21IL%216153981600%21ABXZ&utparam-url=scene%3ApcDetailTopMoreOtherSeller%7Cquery_from%3A"
    
    print(f"Test URL: {test_url}")
    
    # Test affiliate link generation
    print("🔄 Generating affiliate link...")
    affiliate_link = generate_affiliate_link(test_url)
    
    if affiliate_link:
        print(f"✅ Generated: {affiliate_link}")
        
        # Check if it's a direct product link (should contain the correct product ID)
        if '1005007500365472' in affiliate_link:
            print(f"✅ CORRECT PRODUCT ID FOUND!")
        else:
            print(f"⚠️ Product ID not found in generated link")
            
        # Check if it has proper affiliate parameters
        if 'aff_fcid=' in affiliate_link and 'terminal_id=' in affiliate_link:
            print(f"✅ PROPER AFFILIATE PARAMETERS FOUND!")
        else:
            print(f"⚠️ Missing affiliate parameters")
            
        # Check if it's a direct product link (not search result)
        if 'SearchText=' in affiliate_link:
            print(f"❌ WARNING: Link contains SearchText - this is a search result!")
        else:
            print(f"✅ SUCCESS: Direct product link!")
    else:
        print("❌ Failed to generate affiliate link")

if __name__ == "__main__":
    test_fallback_method() 