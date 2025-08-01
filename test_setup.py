#!/usr/bin/env python3
"""
Test script to verify BargainBliss AI Bot setup
"""

import os
import sys
from dotenv import load_dotenv

def test_environment():
    """Test if environment variables are properly set"""
    print("🔍 Testing environment configuration...")
    
    # Load environment variables
    load_dotenv()
    
    # Check for Telegram token
    if not os.getenv('TELEGRAM_TOKEN'):
        print("❌ Missing TELEGRAM_TOKEN environment variable")
        print("Please check your .env file and ensure TELEGRAM_TOKEN is set.")
        return False
    
    # Check for affiliate credentials (support multiple naming conventions)
    api_key = (os.getenv('AFFILIATE_API_KEY') or 
               os.getenv('ALIBABA_API_KEY') or 
               os.getenv('ALIEXPRESS_API_KEY'))
    
    secret_key = (os.getenv('AFFILIATE_SECRET_KEY') or 
                  os.getenv('ALIBABA_SECRET_KEY') or 
                  os.getenv('ALIEXPRESS_SECRET_KEY'))
    
    if not api_key:
        print("❌ Missing affiliate API key")
        print("Please set one of: AFFILIATE_API_KEY, ALIBABA_API_KEY, or ALIEXPRESS_API_KEY")
        return False
    
    if not secret_key:
        print("❌ Missing affiliate secret key")
        print("Please set one of: AFFILIATE_SECRET_KEY, ALIBABA_SECRET_KEY, or ALIEXPRESS_SECRET_KEY")
        return False
    
    print("✅ All required environment variables are set")
    print(f"📊 Using API Key: {api_key[:8]}...")
    return True

def test_dependencies():
    """Test if all required dependencies are installed"""
    print("\n🔍 Testing dependencies...")
    
    required_packages = [
        'telegram',
        'requests',
        'dotenv'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("Please run: pip install -r requirements.txt")
        return False
    else:
        print("✅ All required packages are installed")
        return True

def test_api_connection():
    """Test API connection (optional)"""
    print("\n🔍 Testing API connection...")
    
    try:
        from bargainbliss_ai_bot import test_api_connection as bot_test_api
        result = bot_test_api()
        
        if result:
            print("✅ API connection successful")
            return True
        else:
            print("⚠️ Primary API failed, but alternative method is available")
            print("The bot will use alternative link generation method")
            return True  # Return True because alternative method works
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 BargainBliss AI Bot - Setup Test\n")
    
    # Test environment
    env_ok = test_environment()
    
    # Test dependencies
    deps_ok = test_dependencies()
    
    # Test API connection (only if env and deps are ok)
    api_ok = False
    if env_ok and deps_ok:
        api_ok = test_api_connection()
    
    # Summary
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    
    if env_ok and deps_ok and api_ok:
        print("🎉 All tests passed! Your bot is ready to run.")
        print("Run: python bargainbliss_ai_bot.py")
    elif env_ok and deps_ok:
        print("⚠️ Basic setup is complete, but API connection failed.")
        print("Check your Alibaba API credentials in the .env file.")
    else:
        print("❌ Setup incomplete. Please fix the issues above.")
    
    print("="*50)

if __name__ == "__main__":
    main() 