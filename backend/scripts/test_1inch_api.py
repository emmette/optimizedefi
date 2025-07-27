#!/usr/bin/env python3
"""Test script for 1inch API integration."""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.oneinch import OneInchService
from app.core.config import settings
import json


async def test_1inch_api():
    """Test 1inch API functionality."""
    print("🚀 Testing 1inch API Integration")
    print("=" * 50)
    
    # Check if API key is loaded
    if not settings.ONEINCH_API_KEY:
        print("❌ ERROR: ONEINCH_API_KEY not found in environment")
        return
    
    print(f"✅ API Key loaded: {settings.ONEINCH_API_KEY[:8]}...")
    
    async with OneInchService() as service:
        # Test 1: Get token info on Ethereum
        print("\n📋 Test 1: Fetching token info on Ethereum...")
        try:
            tokens = await service.get_tokens_info(chain_id=1)
            if tokens:
                token_count = len(tokens)
                print(f"✅ Found {token_count} tokens on Ethereum")
                
                # Show a few popular tokens
                popular_tokens = ["USDC", "USDT", "DAI", "WETH"]
                print("\nPopular tokens found:")
                for symbol in popular_tokens:
                    token = next((t for t in tokens.values() if t.get("symbol") == symbol), None)
                    if token:
                        print(f"  - {symbol}: {token.get('address')}")
            else:
                print("ℹ️  No tokens returned (this endpoint might require different parameters)")
        except Exception as e:
            print(f"❌ Error fetching tokens: {e}")
        
        # Test 2: Get token prices
        print("\n💰 Test 2: Getting token prices...")
        try:
            # Popular token addresses on Ethereum mainnet
            token_addresses = [
                "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
                "0x6B175474E89094C44Da98b954EedeAC495271d0F",  # DAI
                "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # USDT
            ]
            
            prices = await service.get_token_prices(chain_id=1, token_addresses=token_addresses)
            if prices:
                print("✅ Token prices (USD):")
                # Show only the tokens we requested
                for addr in token_addresses:
                    if addr.lower() in prices:
                        print(f"   {addr[:10]}...: ${prices[addr.lower()]}")
            else:
                print("❌ No prices returned")
        except Exception as e:
            print(f"❌ Error getting prices: {e}")
        
        # Test 3: Get quote for USDC to DAI swap
        print("\n💱 Test 3: Getting swap quote (100 USDC → DAI on Ethereum)...")
        try:
            # USDC and DAI addresses on Ethereum mainnet
            usdc_address = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
            dai_address = "0x6B175474E89094C44Da98b954EedeAC495271d0F"
            amount = "100000000"  # 100 USDC (6 decimals)
            
            # Example wallet address (random address for testing)
            from_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f5b8e7"
            
            quote = await service.get_quote(
                chain_id=1,
                from_token=usdc_address,
                to_token=dai_address,
                amount=amount,
                from_address=from_address
            )
            
            if quote:
                to_amount = int(quote.get("dstAmount", 0))
                to_amount_formatted = to_amount / 10**18  # DAI has 18 decimals
                print(f"✅ Quote received:")
                print(f"   From: 100 USDC")
                print(f"   To: {to_amount_formatted:.2f} DAI")
                print(f"   Gas estimate: {quote.get('gas', 'N/A')}")
            else:
                print("❌ No quote received")
        except Exception as e:
            print(f"❌ Error getting quote: {e}")
        
        # Test 4: Check supported chains
        print("\n🌐 Test 4: Checking supported chains...")
        try:
            supported_chains = list(service.chain_configs.keys())
            print(f"✅ Supported chains: {supported_chains}")
            
            for chain_id, config in service.chain_configs.items():
                print(f"   - {config['name']} (ID: {chain_id}, Native: {config['native']})")
        except Exception as e:
            print(f"❌ Error checking chains: {e}")
    
    print("\n" + "=" * 50)
    print("✅ 1inch API test completed!")


if __name__ == "__main__":
    asyncio.run(test_1inch_api())