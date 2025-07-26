#!/usr/bin/env python3
"""
Script to verify 1inch API access
Usage: python verify-1inch-api.py
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv('ONEINCH_API_KEY')
BASE_URL = 'https://api.1inch.io/v6.0'

def verify_api_access():
    """Verify 1inch API access by making a test request"""
    if not API_KEY:
        print("❌ Error: ONEINCH_API_KEY not found in environment variables")
        print("Please set your 1inch API key in .env file")
        return False
    
    # Test endpoint - get supported chains
    url = f"{BASE_URL}/chains"
    headers = {
        'Authorization': f'Bearer {API_KEY}'
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            print("✅ 1inch API access verified successfully!")
            print(f"Supported chains: {', '.join(str(chain) for chain in response.json().keys())}")
            return True
        else:
            print(f"❌ API request failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error connecting to 1inch API: {str(e)}")
        return False

if __name__ == "__main__":
    verify_api_access()