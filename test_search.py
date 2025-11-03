#!/usr/bin/env python3
"""
Test script for Scout web search functionality
Tests both Google API and web scraping fallback
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.search_client import SearchClient


async def test_search():
    """Test search functionality"""
    print("=" * 60)
    print("Scout Search Test")
    print("=" * 60)
    print()
    
    client = SearchClient()
    
    # Check configuration
    if client.is_configured():
        print("✓ Google Custom Search API is configured")
        print(f"  API Key: {client.api_key[:10]}...")
        print(f"  CSE ID: {client.cse_id[:10]}...")
        print()
    else:
        print("⚠ Google API not configured - using web scraping fallback")
        print("  This is normal and expected!")
        print()
    
    # Test queries
    test_queries = [
        "Python programming language",
        "weather in New York",
        "current Bitcoin price"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\nTest {i}: '{query}'")
        print("-" * 60)
        
        try:
            results = await client.search(query, num_results=3)
            
            if results:
                print(f"✓ Found {len(results)} results")
                
                for j, result in enumerate(results, 1):
                    print(f"\n  Result {j}:")
                    print(f"    Title: {result['title'][:60]}...")
                    print(f"    Snippet: {result['snippet'][:80]}...")
                    print(f"    Link: {result['link'][:60]}...")
                    print(f"    Source: {result.get('source', 'unknown')}")
                    
                    if result.get('error'):
                        print(f"    ⚠ Error result")
            else:
                print("✗ No results found")
                
        except Exception as e:
            print(f"✗ Error: {str(e)}")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
    print()
    
    if not client.is_configured():
        print("💡 Tip: Configure Google API for better results:")
        print("   1. Get API key from Google Cloud Console")
        print("   2. Create Custom Search Engine")
        print("   3. Add to .env file:")
        print("      GOOGLE_API_KEY=your_key")
        print("      GOOGLE_CSE_ID=your_cse_id")
        print()
    
    print("Web scraping works out of the box - no setup needed!")


if __name__ == "__main__":
    try:
        asyncio.run(test_search())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nTest failed: {str(e)}")
        sys.exit(1)
