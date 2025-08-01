import requests
import hashlib
import time
from urllib.parse import urlencode

# Your credentials
API_KEY = '515878'
SECRET_KEY = 'MbbuLsPwmjzA65DPnsK8KDfYIEI9jl1C'
TRACKING_ID = 'bargainbliss_ai_bot'
product_url = 'https://www.aliexpress.com/item/100500721141956.html'

# API parameters
params = {
    'appKey': API_KEY,
    'apiName': 'api.getPromotionLinks',
    'fields': 'totalResults,trackingId,publisherId,url,promotionUrl',
    'trackingId': TRACKING_ID,
    'urls': product_url,
    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
    'sign_method': 'md5'  # Explicitly specify signature method
}

# Generate signature
sorted_params = ''.join(f'{k}{v}' for k, v in sorted(params.items()))
sign_string = sorted_params + SECRET_KEY
params['sign'] = hashlib.md5(sign_string.encode('utf-8')).hexdigest().upper()

# Make API call
api_url = 'http://gw.api.alibaba.com/openapi/param2/2/portals.open/api.getPromotionLinks'
response = requests.get(api_url, params=params)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")