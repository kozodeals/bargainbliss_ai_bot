#!/usr/bin/env python3
"""
Query a specific product by product ID using AliExpress API
"""

import sys
import os
import asyncio
import json
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from src.bot_queue import PostQueueBot

async def query_specific_product(product_id):
    """Query a specific product by its product ID"""
    try:
        # Initialize the bot to get API credentials
        bot = PostQueueBot(account_id="account1")
        
        print(f"🔍 Querying product ID: {product_id}")
        
        # Build the API parameters for product query
        params = {
            "method": "aliexpress.affiliate.product.query",
            "fields": "product_id,product_title,target_sale_price,product_main_image_url,promotion_link,product_detail_url,product_origin,product_weight,product_dimensions,original_price,discount,product_rating,product_review_count,product_sales,product_shop_name,evaluate_rate,lastest_volume",
            "product_ids": product_id,  # Query specific product ID
            "currency": "ILS",
            "language": "IL",
            "targetLanguage": "IL",
            "isMultiLanguage": "true",
            "locale": "IL_IL",
            "ship_to_country": bot.config['aliexpress']['ship_to_country'],
            "tracking_id": bot.credentials['tracking_id']
        }
        
        print("📡 Making API request...")
        response = await bot.aliexpress_api_request(params)
        
        if response and "aliexpress_affiliate_product_query_response" in response:
            products_data = response["aliexpress_affiliate_product_query_response"]["resp_result"]["result"]["products"]
            products = products_data["product"] if isinstance(products_data["product"], list) else [products_data["product"]]
            
            if products:
                product = products[0]  # Get the first (and should be only) product
                
                # Generate short affiliate link
                print("\n🔄 Generating short affiliate link...")
                short_affiliate_link = await bot.generate_affiliate_link(product.get('product_detail_url', ''))
                
                print("\n" + "="*60)
                print("📦 PRODUCT DETAILS")
                print("="*60)
                
                # Basic info
                print(f"Product ID: {product.get('product_id', 'N/A')}")
                print(f"Title: {product.get('product_title', 'N/A')}")
                print(f"Shop: {product.get('shop_name', 'N/A')}")
                
                # Pricing
                print(f"\n💰 PRICING")
                print(f"Sale Price: {product.get('target_sale_price', 'N/A')} {product.get('target_sale_price_currency', 'N/A')}")
                print(f"Original Price: {product.get('original_price', 'N/A')} {product.get('original_price_currency', 'N/A')}")
                print(f"Discount: {product.get('discount', 'N/A')}")
                
                # Ratings and Reviews
                print(f"\n⭐ RATINGS & REVIEWS")
                print(f"Rating: {product.get('evaluate_rate', 'N/A')}")
                print(f"Review Count: {product.get('product_review_count', 'N/A')}")
                print(f"Sales Volume: {product.get('lastest_volume', 'N/A')}")
                
                # Product Details
                print(f"\n📋 PRODUCT DETAILS")
                print(f"Origin: {product.get('product_origin', 'N/A')}")
                print(f"Weight: {product.get('product_weight', 'N/A')}")
                print(f"Dimensions: {product.get('product_dimensions', 'N/A')}")
                
                # URLs
                print(f"\n🔗 LINKS")
                print(f"Product URL: {product.get('product_detail_url', 'N/A')}")
                print(f"Image URL: {product.get('product_main_image_url', 'N/A')}")
                print(f"Long Promotion Link: {product.get('promotion_link', 'N/A')}")
                print(f"Short Affiliate Link: {short_affiliate_link}")
                
                # Calculate discount percentage
                original_price = float(product.get('original_price', 0))
                sale_price = float(product.get('target_sale_price', 0))
                if original_price > 0 and sale_price > 0:
                    discount_percentage = round(((original_price - sale_price) / original_price) * 100, 1)
                    print(f"\n🎯 CALCULATED DISCOUNT: {discount_percentage}%")
                
                print("="*60)
                
                return product
            else:
                print("❌ No product found with that ID")
                return None
        else:
            print("❌ API response error or no products found")
            print(f"Response: {response}")
            return None
            
    except Exception as e:
        print(f"❌ Error querying product: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return None

async def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python query_specific_product.py <product_id>")
        print("Example: python query_specific_product.py 1005009347842089")
        return
    
    product_id = sys.argv[1]
    await query_specific_product(product_id)

if __name__ == "__main__":
    asyncio.run(main()) 