"""
Quick API Test Script
Test all new endpoints to verify they work correctly
"""

import asyncio
import aiohttp
from loguru import logger

BASE_URL = "http://localhost:8000"


async def test_endpoint(session: aiohttp.ClientSession, method: str, endpoint: str, **kwargs):
    """Test a single endpoint"""
    url = f"{BASE_URL}{endpoint}"
    try:
        async with session.request(method, url, **kwargs) as response:
            status = response.status
            if status < 400:
                logger.success(f"✅ {method:6} {endpoint:40} → {status}")
                return await response.json()
            else:
                logger.error(f"❌ {method:6} {endpoint:40} → {status}")
                return None
    except Exception as e:
        logger.error(f"❌ {method:6} {endpoint:40} → ERROR: {e}")
        return None


async def main():
    """Run all endpoint tests"""
    logger.info("="*70)
    logger.info("Testing API Endpoints")
    logger.info("="*70)
    
    async with aiohttp.ClientSession() as session:
        # Health check
        logger.info("\n📊 Health & Status")
        await test_endpoint(session, "GET", "/")
        await test_endpoint(session, "GET", "/health")
        
        # User endpoints
        logger.info("\n👥 User Endpoints")
        await test_endpoint(session, "GET", "/users")
        await test_endpoint(session, "GET", "/users/1")
        await test_endpoint(session, "GET", "/users-dict")
        
        # Zone endpoints
        logger.info("\n🗺️  Zone Endpoints")
        zones = await test_endpoint(session, "GET", "/zones")
        await test_endpoint(session, "GET", "/zones/zone_001")
        
        # Users by zone (if zones exist)
        if zones and len(zones) > 0:
            zone_id = zones[0].get('zone_id', 'zone_001')
            await test_endpoint(session, "GET", f"/users/by-zone/{zone_id}")
        
        # Stats endpoints
        logger.info("\n📈 Statistics Endpoints")
        await test_endpoint(session, "GET", "/stats/users")
        await test_endpoint(session, "GET", "/stats/zones")
        
        # Cache endpoints
        logger.info("\n💾 Cache Endpoints")
        await test_endpoint(session, "GET", "/cache/stats")
        
        # Kafka endpoints
        logger.info("\n📨 Kafka Endpoints")
        await test_endpoint(session, "GET", "/messages/recent?limit=10")
        
    logger.info("\n" + "="*70)
    logger.info("✅ All endpoint tests completed!")
    logger.info("="*70)


if __name__ == "__main__":
    asyncio.run(main())
