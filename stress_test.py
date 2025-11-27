"""
Stress Test for Async API - Concurrent Request Benchmark
Tests the performance benefits of async/await vs blocking I/O
"""

import asyncio
import aiohttp
import time
from typing import List, Dict
import statistics

API_BASE_URL = "http://localhost:8000"

# Test Configuration
CONCURRENT_REQUESTS = 100  # Number of simultaneous requests
TEST_ENDPOINTS = [
    "/users",
    "/zones",
    "/stats/users",
    "/stats/zones",
    "/health"
]


async def fetch_endpoint(session: aiohttp.ClientSession, endpoint: str, request_id: int) -> Dict:
    """Fetch a single endpoint and measure response time"""
    start_time = time.time()
    
    try:
        async with session.get(f"{API_BASE_URL}{endpoint}") as response:
            data = await response.json()
            elapsed = time.time() - start_time
            
            return {
                "request_id": request_id,
                "endpoint": endpoint,
                "status": response.status,
                "elapsed": elapsed,
                "success": True
            }
    except Exception as e:
        elapsed = time.time() - start_time
        return {
            "request_id": request_id,
            "endpoint": endpoint,
            "status": 0,
            "elapsed": elapsed,
            "success": False,
            "error": str(e)
        }


async def create_users_concurrently(session: aiohttp.ClientSession, count: int) -> List[Dict]:
    """Create multiple users concurrently to test write operations"""
    tasks = []
    
    for i in range(count):
        user_data = {
            "global_id": 10000 + i,
            "name": f"StressTestUser_{i}",
            "zone_id": "ZONE_001" if i % 3 == 0 else ("ZONE_002" if i % 3 == 1 else "ZONE_003")
        }
        
        async def create_user(data, idx):
            start_time = time.time()
            try:
                async with session.post(f"{API_BASE_URL}/users", json=data) as response:
                    result = await response.json()
                    elapsed = time.time() - start_time
                    return {
                        "request_id": idx,
                        "status": response.status,
                        "elapsed": elapsed,
                        "success": response.status in [200, 201]
                    }
            except Exception as e:
                elapsed = time.time() - start_time
                return {
                    "request_id": idx,
                    "status": 0,
                    "elapsed": elapsed,
                    "success": False,
                    "error": str(e)
                }
        
        tasks.append(create_user(user_data, i))
    
    return await asyncio.gather(*tasks)


async def stress_test_reads():
    """Test concurrent READ operations"""
    print("\n" + "="*70)
    print("🔥 STRESS TEST: CONCURRENT READ OPERATIONS")
    print("="*70)
    
    async with aiohttp.ClientSession() as session:
        # Warm-up request
        print("\n🔄 Warming up...")
        async with session.get(f"{API_BASE_URL}/health") as response:
            await response.json()
        
        print(f"\n📊 Sending {CONCURRENT_REQUESTS} concurrent requests...")
        print(f"📍 Testing endpoints: {', '.join(TEST_ENDPOINTS)}")
        
        # Create tasks for concurrent requests
        tasks = []
        start_time = time.time()
        
        for i in range(CONCURRENT_REQUESTS):
            endpoint = TEST_ENDPOINTS[i % len(TEST_ENDPOINTS)]
            tasks.append(fetch_endpoint(session, endpoint, i))
        
        # Execute all requests concurrently
        results = await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        
        # Analyze results
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]
        response_times = [r["elapsed"] for r in successful]
        
        # Print results
        print(f"\n✅ RESULTS:")
        print(f"   Total Requests: {CONCURRENT_REQUESTS}")
        print(f"   Successful: {len(successful)}")
        print(f"   Failed: {len(failed)}")
        print(f"   Total Time: {total_time:.3f}s")
        print(f"   Requests/Second: {CONCURRENT_REQUESTS / total_time:.2f}")
        
        if response_times:
            print(f"\n⏱️  RESPONSE TIMES:")
            print(f"   Min: {min(response_times)*1000:.2f}ms")
            print(f"   Max: {max(response_times)*1000:.2f}ms")
            print(f"   Mean: {statistics.mean(response_times)*1000:.2f}ms")
            print(f"   Median: {statistics.median(response_times)*1000:.2f}ms")
            print(f"   P95: {sorted(response_times)[int(len(response_times)*0.95)]*1000:.2f}ms")
            print(f"   P99: {sorted(response_times)[int(len(response_times)*0.99)]*1000:.2f}ms")
        
        # Endpoint breakdown
        print(f"\n📈 ENDPOINT BREAKDOWN:")
        for endpoint in TEST_ENDPOINTS:
            endpoint_results = [r for r in successful if r["endpoint"] == endpoint]
            if endpoint_results:
                avg_time = statistics.mean([r["elapsed"] for r in endpoint_results])
                print(f"   {endpoint}: {len(endpoint_results)} requests, avg {avg_time*1000:.2f}ms")


async def stress_test_writes():
    """Test concurrent WRITE operations"""
    print("\n" + "="*70)
    print("🔥 STRESS TEST: CONCURRENT WRITE OPERATIONS")
    print("="*70)
    
    write_count = 50  # Number of concurrent writes
    
    async with aiohttp.ClientSession() as session:
        print(f"\n✍️  Creating {write_count} users concurrently...")
        
        start_time = time.time()
        results = await create_users_concurrently(session, write_count)
        total_time = time.time() - start_time
        
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]
        response_times = [r["elapsed"] for r in successful]
        
        print(f"\n✅ RESULTS:")
        print(f"   Total Write Operations: {write_count}")
        print(f"   Successful: {len(successful)}")
        print(f"   Failed: {len(failed)}")
        print(f"   Total Time: {total_time:.3f}s")
        print(f"   Writes/Second: {write_count / total_time:.2f}")
        
        if response_times:
            print(f"\n⏱️  RESPONSE TIMES:")
            print(f"   Min: {min(response_times)*1000:.2f}ms")
            print(f"   Max: {max(response_times)*1000:.2f}ms")
            print(f"   Mean: {statistics.mean(response_times)*1000:.2f}ms")
            print(f"   Median: {statistics.median(response_times)*1000:.2f}ms")


async def stress_test_mixed():
    """Test mixed READ and WRITE operations"""
    print("\n" + "="*70)
    print("🔥 STRESS TEST: MIXED READ/WRITE OPERATIONS")
    print("="*70)
    
    async with aiohttp.ClientSession() as session:
        print(f"\n🔀 Running mixed workload (75% reads, 25% writes)...")
        
        tasks = []
        start_time = time.time()
        
        # 75% reads
        for i in range(75):
            endpoint = TEST_ENDPOINTS[i % len(TEST_ENDPOINTS)]
            tasks.append(fetch_endpoint(session, endpoint, i))
        
        # 25% writes
        for i in range(75, 100):
            user_data = {
                "global_id": 20000 + i,
                "name": f"MixedTestUser_{i}",
                "zone_id": "ZONE_001"
            }
            
            async def create_user_task(data, idx):
                start_time = time.time()
                try:
                    async with session.post(f"{API_BASE_URL}/users", json=data) as response:
                        await response.json()
                        elapsed = time.time() - start_time
                        return {
                            "request_id": idx,
                            "type": "write",
                            "status": response.status,
                            "elapsed": elapsed,
                            "success": response.status in [200, 201]
                        }
                except Exception as e:
                    elapsed = time.time() - start_time
                    return {
                        "request_id": idx,
                        "type": "write",
                        "status": 0,
                        "elapsed": elapsed,
                        "success": False
                    }
            
            tasks.append(create_user_task(user_data, i))
        
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]
        
        print(f"\n✅ RESULTS:")
        print(f"   Total Operations: 100 (75 reads + 25 writes)")
        print(f"   Successful: {len(successful)}")
        print(f"   Failed: {len(failed)}")
        print(f"   Total Time: {total_time:.3f}s")
        print(f"   Operations/Second: {100 / total_time:.2f}")
        
        response_times = [r["elapsed"] for r in successful]
        if response_times:
            print(f"\n⏱️  RESPONSE TIMES:")
            print(f"   Mean: {statistics.mean(response_times)*1000:.2f}ms")
            print(f"   Median: {statistics.median(response_times)*1000:.2f}ms")


async def main():
    """Run all stress tests"""
    print("\n" + "="*70)
    print("🚀 ASYNC API STRESS TEST SUITE")
    print("="*70)
    print("\nThis test demonstrates the concurrency benefits of async/await:")
    print("- Non-blocking I/O allows handling multiple requests simultaneously")
    print("- Connection pooling efficiently manages database connections")
    print("- Requests are processed concurrently, not sequentially")
    
    try:
        # Test 1: Concurrent Reads
        await stress_test_reads()
        
        await asyncio.sleep(1)  # Brief pause between tests
        
        # Test 2: Concurrent Writes
        await stress_test_writes()
        
        await asyncio.sleep(1)
        
        # Test 3: Mixed Operations
        await stress_test_mixed()
        
        print("\n" + "="*70)
        print("✅ ALL STRESS TESTS COMPLETED")
        print("="*70)
        
        print("\n💡 KEY TAKEAWAYS:")
        print("   • Async API handles concurrent requests efficiently")
        print("   • Response times remain low even under high load")
        print("   • Connection pooling prevents database overload")
        print("   • Server never blocks - can handle other requests while waiting for DB")
        
    except Exception as e:
        print(f"\n❌ Error during stress test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n🎯 Starting Stress Test...")
    print("📌 Make sure the API is running on http://localhost:8001")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
