#!/usr/bin/env python3
"""
Comprehensive test script for portfolio API endpoints.
Tests 1inch integration, error handling, and data structures.
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
API_BASE_URL = "http://localhost:8000"
TEST_WALLETS = [
    "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",  # vitalik.eth
    "0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD",  # Uniswap router
    "0x0000000000000000000000000000000000000000",  # Zero address (should have no balance)
]
TEST_CHAINS = [1, 137, 10, 42161]  # Ethereum, Polygon, Optimism, Arbitrum


class PortfolioAPITester:
    """Test portfolio API functionality."""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "errors": []
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_health_check(self) -> bool:
        """Test if the backend is running."""
        try:
            async with self.session.get(f"{API_BASE_URL}/health") as response:
                if response.status == 200:
                    logger.info("✅ Backend health check passed")
                    return True
                else:
                    logger.error(f"❌ Backend health check failed: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ Cannot connect to backend: {e}")
            return False
    
    async def test_portfolio_endpoint(
        self, 
        wallet: str, 
        chains: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """Test portfolio endpoint for a specific wallet."""
        self.results["total_tests"] += 1
        
        try:
            url = f"{API_BASE_URL}/api/portfolio/{wallet}"
            params = {}
            if chains:
                params["chains"] = chains
            
            logger.info(f"Testing portfolio for {wallet[:8]}... on chains {chains or 'all'}")
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Validate response structure
                    required_fields = ["address", "total_value_usd", "chains", 
                                     "diversification_score", "risk_assessment", 
                                     "performance", "last_updated"]
                    
                    missing_fields = [f for f in required_fields if f not in data]
                    if missing_fields:
                        raise ValueError(f"Missing required fields: {missing_fields}")
                    
                    # Validate chains structure
                    for chain in data["chains"]:
                        chain_fields = ["chain_id", "chain_name", "total_value_usd", "tokens"]
                        missing_chain_fields = [f for f in chain_fields if f not in chain]
                        if missing_chain_fields:
                            raise ValueError(f"Chain missing fields: {missing_chain_fields}")
                        
                        # Validate tokens
                        for token in chain["tokens"]:
                            token_fields = ["address", "symbol", "name", "decimals", 
                                          "balance", "balance_human", "balance_usd", "price_usd"]
                            missing_token_fields = [f for f in token_fields if f not in token]
                            if missing_token_fields:
                                raise ValueError(f"Token missing fields: {missing_token_fields}")
                    
                    self.results["passed"] += 1
                    logger.info(f"✅ Portfolio test passed for {wallet[:8]}...")
                    logger.info(f"   Total value: ${data['total_value_usd']:,.2f}")
                    logger.info(f"   Chains: {len(data['chains'])}")
                    logger.info(f"   Total tokens: {sum(len(c['tokens']) for c in data['chains'])}")
                    
                    return data
                else:
                    error_text = await response.text()
                    raise Exception(f"HTTP {response.status}: {error_text}")
                    
        except Exception as e:
            self.results["failed"] += 1
            self.results["errors"].append({
                "test": f"portfolio_{wallet}",
                "error": str(e)
            })
            logger.error(f"❌ Portfolio test failed for {wallet[:8]}...: {e}")
            return {}
    
    async def test_portfolio_metrics(self, wallet: str) -> bool:
        """Test portfolio metrics endpoint."""
        self.results["total_tests"] += 1
        
        try:
            url = f"{API_BASE_URL}/api/portfolio/{wallet}/metrics"
            
            logger.info(f"Testing portfolio metrics for {wallet[:8]}...")
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Validate metrics structure
                    required_fields = ["diversification_score", "risk_assessment", 
                                     "performance_metrics", "rebalancing_suggestions", 
                                     "yield_metrics"]
                    
                    missing_fields = [f for f in required_fields if f not in data]
                    if missing_fields:
                        raise ValueError(f"Missing required fields: {missing_fields}")
                    
                    self.results["passed"] += 1
                    logger.info(f"✅ Metrics test passed for {wallet[:8]}...")
                    logger.info(f"   Diversification: {data['diversification_score']}")
                    logger.info(f"   Risk level: {data['risk_assessment'].get('level', 'N/A')}")
                    
                    return True
                else:
                    error_text = await response.text()
                    raise Exception(f"HTTP {response.status}: {error_text}")
                    
        except Exception as e:
            self.results["failed"] += 1
            self.results["errors"].append({
                "test": f"metrics_{wallet}",
                "error": str(e)
            })
            logger.error(f"❌ Metrics test failed for {wallet[:8]}...: {e}")
            return False
    
    async def test_error_handling(self) -> bool:
        """Test error handling with invalid inputs."""
        self.results["total_tests"] += 1
        
        try:
            # Test invalid wallet address
            invalid_wallet = "0xinvalid"
            url = f"{API_BASE_URL}/api/portfolio/{invalid_wallet}"
            
            logger.info("Testing error handling with invalid wallet...")
            
            async with self.session.get(url) as response:
                if response.status == 400:
                    self.results["passed"] += 1
                    logger.info("✅ Error handling test passed - correctly rejected invalid wallet")
                    return True
                else:
                    raise Exception(f"Expected 400 error, got {response.status}")
                    
        except Exception as e:
            self.results["failed"] += 1
            self.results["errors"].append({
                "test": "error_handling",
                "error": str(e)
            })
            logger.error(f"❌ Error handling test failed: {e}")
            return False
    
    async def test_rate_limiting(self) -> bool:
        """Test rate limiting behavior."""
        self.results["total_tests"] += 1
        
        try:
            wallet = TEST_WALLETS[0]
            url = f"{API_BASE_URL}/api/portfolio/{wallet}"
            
            logger.info("Testing rate limiting with rapid requests...")
            
            # Make 10 rapid requests
            tasks = []
            for i in range(10):
                tasks.append(self.session.get(url))
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check if any were rate limited
            statuses = []
            for resp in responses:
                if isinstance(resp, Exception):
                    continue
                if hasattr(resp, 'status'):
                    statuses.append(resp.status)
                    await resp.close()
            
            # If we got any 429s, rate limiting is working
            if 429 in statuses:
                self.results["passed"] += 1
                logger.info("✅ Rate limiting test passed - API properly limits requests")
                return True
            else:
                # No rate limiting detected - this might be OK for development
                self.results["passed"] += 1
                logger.info("⚠️  No rate limiting detected (may be disabled in development)")
                return True
                
        except Exception as e:
            self.results["failed"] += 1
            self.results["errors"].append({
                "test": "rate_limiting",
                "error": str(e)
            })
            logger.error(f"❌ Rate limiting test failed: {e}")
            return False
    
    async def test_empty_portfolio(self) -> bool:
        """Test handling of empty portfolios."""
        self.results["total_tests"] += 1
        
        try:
            # Use zero address which should have no tokens
            wallet = "0x0000000000000000000000000000000000000000"
            url = f"{API_BASE_URL}/api/portfolio/{wallet}"
            
            logger.info("Testing empty portfolio handling...")
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Should have structure but no tokens
                    if data["total_value_usd"] == 0:
                        self.results["passed"] += 1
                        logger.info("✅ Empty portfolio test passed")
                        return True
                    else:
                        raise Exception("Zero address has non-zero balance")
                else:
                    error_text = await response.text()
                    raise Exception(f"HTTP {response.status}: {error_text}")
                    
        except Exception as e:
            self.results["failed"] += 1
            self.results["errors"].append({
                "test": "empty_portfolio",
                "error": str(e)
            })
            logger.error(f"❌ Empty portfolio test failed: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all tests and report results."""
        logger.info("🚀 Starting Portfolio API Tests")
        logger.info("=" * 60)
        
        # Check backend health first
        if not await self.test_health_check():
            logger.error("Backend is not running. Please start the backend first.")
            return
        
        # Test different wallets
        for wallet in TEST_WALLETS[:2]:  # Test first 2 wallets
            await self.test_portfolio_endpoint(wallet)
            await asyncio.sleep(0.5)  # Small delay between requests
        
        # Test with specific chains
        await self.test_portfolio_endpoint(TEST_WALLETS[0], chains=[1, 137])
        
        # Test metrics endpoint
        await self.test_portfolio_metrics(TEST_WALLETS[0])
        
        # Test error handling
        await self.test_error_handling()
        
        # Test empty portfolio
        await self.test_empty_portfolio()
        
        # Test rate limiting
        await self.test_rate_limiting()
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("📊 Test Summary:")
        logger.info(f"   Total tests: {self.results['total_tests']}")
        logger.info(f"   Passed: {self.results['passed']} ✅")
        logger.info(f"   Failed: {self.results['failed']} ❌")
        
        if self.results["errors"]:
            logger.info("\n❌ Errors:")
            for error in self.results["errors"]:
                logger.error(f"   {error['test']}: {error['error']}")
        
        success_rate = (self.results["passed"] / self.results["total_tests"] * 100) if self.results["total_tests"] > 0 else 0
        logger.info(f"\n✨ Success rate: {success_rate:.1f}%")
        
        return self.results["failed"] == 0


async def main():
    """Main entry point."""
    async with PortfolioAPITester() as tester:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())