#!/usr/bin/env python3
"""
Script to get Render's IP address
"""

import requests
import json

def get_ip_info():
    """Get the current IP address and location info"""
    try:
        # Get IP from multiple services for accuracy
        services = [
            "https://api.ipify.org?format=json",
            "https://httpbin.org/ip",
            "https://ipinfo.io/json"
        ]
        
        print("🔍 Getting Render's IP address...")
        print("=" * 50)
        
        for i, service in enumerate(services, 1):
            try:
                response = requests.get(service, timeout=10)
                data = response.json()
                
                if 'ip' in data:
                    ip = data['ip']
                    print(f"✅ Service {i}: {ip}")
                    
                    # Get additional info if available
                    if 'country' in data:
                        print(f"   Country: {data.get('country', 'Unknown')}")
                    if 'region' in data:
                        print(f"   Region: {data.get('region', 'Unknown')}")
                    if 'city' in data:
                        print(f"   City: {data.get('city', 'Unknown')}")
                    if 'org' in data:
                        print(f"   ISP: {data.get('org', 'Unknown')}")
                        
                elif 'origin' in data:
                    ip = data['origin']
                    print(f"✅ Service {i}: {ip}")
                    
            except Exception as e:
                print(f"❌ Service {i} failed: {e}")
                
        print("\n" + "=" * 50)
        print("💡 Add the IP address above to your AliExpress affiliate dashboard IP whitelist")
        print("💡 You may need to add multiple IPs if Render uses different IPs")
        
    except Exception as e:
        print(f"❌ Error getting IP: {e}")

if __name__ == "__main__":
    get_ip_info() 