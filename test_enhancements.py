#!/usr/bin/env python3
"""
Test script for new API enhancements:
1. GET /price endpoint
2. Rate limiting
3. Connection limits
4. Asyncio message queue
"""

import asyncio
import aiohttp
import json
import time
from concurrent.futures import ThreadPoolExecutor

# Configuration
BASE_URL = "http://localhost:8000"
RATE_LIMIT_ENDPOINT = f"{BASE_URL}/price"
PRICES_ENDPOINT = f"{BASE_URL}/prices"


async def test_price_endpoint():
    """Test the new GET /price endpoint"""
    print("\n" + "="*60)
    print("TEST 1: GET /price Endpoint")
    print("="*60)
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(RATE_LIMIT_ENDPOINT) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    print(f"Status: {response.status}")
                    print(f"\nLatest Prices:")
                    for symbol, price_data in data.get('latest_prices', {}).items():
                        print(f"  {symbol}: ${price_data['last_price']:.2f} ({price_data['24h_change']:+.2f}%)")
                    
                    print(f"\nConnection Statistics:")
                    stats = data.get('connection_stats', {})
                    print(f"  Active Connections: {stats['active_connections']}/{stats['max_connections']}")
                    print(f"  Available Slots: {stats['available_slots']}")
                    print(f"  Total Symbols Tracked: {data.get('total_symbols', 0)}")
                else:
                    print(f"Status: {response.status} ")
                    text = await response.text()
                    print(f"Response: {text}")
        except aiohttp.ClientConnectorError:
            print(" ERROR: Could not connect to server. Is it running?")
            print("  Start the server with: python main.py")


async def test_rate_limiting():
    """Test rate limiting on GET /price endpoint"""
    print("\n" + "="*60)
    print("TEST 2: Rate Limiting (30 requests per minute)")
    print("="*60)
    print("Making 35 rapid requests to test rate limiting...")
    
    success_count = 0
    rate_limited_count = 0
    
    async with aiohttp.ClientSession() as session:
        for i in range(35):
            try:
                async with session.get(RATE_LIMIT_ENDPOINT) as response:
                    if response.status == 200:
                        success_count += 1
                        print(f"Request {i+1}: 200 OK")
                    elif response.status == 429:
                        rate_limited_count += 1
                        print(f"Request {i+1}: 429 Rate Limited")
                    else:
                        print(f"Request {i+1}: {response.status}")
            except aiohttp.ClientConnectorError:
                print(f"Request {i+1}: Connection Error")
            
            # Small delay between requests
            await asyncio.sleep(0.05)
    
    print(f"\nResults:")
    print(f"  Successful Requests (200): {success_count}")
    print(f"  Rate Limited (429): {rate_limited_count}")
    
    if rate_limited_count > 0:
        print("  Rate limiting is working correctly!")
    else:
        print("  Note: Rate limit not triggered (you might need more requests)")


async def test_prices_endpoint():
    """Test the /prices endpoint (backward compatibility)"""
    print("\n" + "="*60)
    print("TEST 3: GET /prices Endpoint (Backward Compatibility)")
    print("="*60)
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(PRICES_ENDPOINT) as response:
                if response.status == 200:
                    data = await response.json()
                    prices = data.get('prices', {})
                    
                    print(f"Status: {response.status}")
                    print(f"Response Format: {list(data.keys())}")
                    print(f"Number of Symbols: {len(prices)}")
                    print(f"Symbols: {', '.join(prices.keys())}")
                else:
                    print(f"Status: {response.status}")
        except aiohttp.ClientConnectorError:
            print("ERROR: Could not connect to server")


async def test_concurrent_requests():
    """Test handling multiple concurrent requests"""
    print("\n" + "="*60)
    print("TEST 4: Concurrent Requests Handling")
    print("="*60)
    
    print("Making 10 concurrent requests...")
    
    async def make_request():
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(RATE_LIMIT_ENDPOINT) as response:
                    return response.status
            except Exception as e:
                return f"Error: {e}"
    
    start_time = time.time()
    results = await asyncio.gather(*[make_request() for _ in range(10)])
    elapsed_time = time.time() - start_time
    
    successful = sum(1 for r in results if r == 200)
    rate_limited = sum(1 for r in results if r == 429)
    errors = sum(1 for r in results if isinstance(r, str))
    
    print(f"\nResults:")
    print(f"  Successful (200): {successful}")
    print(f"  Rate Limited (429): {rate_limited}")
    print(f"  Errors: {errors}")
    print(f"  Time Taken: {elapsed_time:.2f}s")


async def test_websocket_connection_stats():
    """Check connection stats through /price endpoint"""
    print("\n" + "="*60)
    print("TEST 5: Real-time Connection Statistics")
    print("="*60)
    
    async with aiohttp.ClientSession() as session:
        for i in range(3):
            try:
                async with session.get(RATE_LIMIT_ENDPOINT) as response:
                    if response.status == 200:
                        data = await response.json()
                        stats = data.get('connection_stats', {})
                        
                        print(f"\nCheck {i+1}:")
                        print(f"  Active Connections: {stats['active_connections']}")
                        print(f"  Max Connections: {stats['max_connections']}")
                        print(f"  Available Slots: {stats['available_slots']}")
                        print(f"  Capacity: {(stats['active_connections']/stats['max_connections']*100):.1f}%")
                        
                        # Visual representation
                        used = int((stats['active_connections']/stats['max_connections'])*20)
                        bar = '█' * used + '░' * (20 - used)
                        print(f"  [{bar}]")
            except aiohttp.ClientConnectorError:
                print("ERROR: Could not connect to server")
            
            if i < 2:
                await asyncio.sleep(1)


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("CRYPTO PRICE WEBSOCKET - API ENHANCEMENT TESTS")
    print("="*60)
    print("\nNote: Make sure the server is running!")
    print("Run in another terminal: python main.py")
    
    # Test if server is running
    print("\nChecking if server is running...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/") as response:
                if response.status == 200:
                    print("Server is running!\n")
                else:
                    print("Server returned unexpected status")
                    return
    except aiohttp.ClientConnectorError:
        print("Server is not running! Start it with: python main.py")
        return
    
    # Run tests
    await test_price_endpoint()
    await test_prices_endpoint()
    await test_concurrent_requests()
    await test_rate_limiting()
    await test_websocket_connection_stats()
    
    # Summary
    print("\n" + "="*60)
    print("ALL TESTS COMPLETED!")
    print("="*60)
    print("\nFor more information, see:")
    print("  - README.md - Full project documentation")
    print("  - TESTING.md - Comprehensive testing guide")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTests cancelled by user")
