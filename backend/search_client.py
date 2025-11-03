"""
Web search client supporting both Google Custom Search API and public web scraping
"""
import httpx
import re
from typing import List, Dict, Optional
from urllib.parse import quote_plus, urljoin
from bs4 import BeautifulSoup
from backend.config import get_settings


class SearchClient:
    """Client for web searches with Google API and fallback scraping"""
    
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.GOOGLE_API_KEY
        self.cse_id = self.settings.GOOGLE_CSE_ID
        self.max_results = self.settings.SEARCH_MAX_RESULTS
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        
        # User agent for web scraping
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }
    
    def is_configured(self) -> bool:
        """Check if search API is properly configured"""
        return bool(self.api_key and self.cse_id and 
                   self.api_key != "your_google_api_key_here")
    
    async def search(
        self,
        query: str,
        num_results: Optional[int] = None
    ) -> List[Dict]:
        """
        Perform web search using Google Custom Search API or fallback to scraping
        
        Args:
            query: Search query
            num_results: Number of results to return
        
        Returns:
            List of search results with title, snippet, and link
        """
        # Try Google API first if configured
        if self.is_configured():
            return await self._search_google_api(query, num_results)
        
        # Fallback to web scraping
        return await self._search_public_web(query, num_results)
    
    async def _search_google_api(
        self,
        query: str,
        num_results: Optional[int] = None
    ) -> List[Dict]:
        """
        Search using Google Custom Search API
        """
        num_results = num_results or self.max_results
        
        params = {
            "key": self.api_key,
            "cx": self.cse_id,
            "q": query,
            "num": min(num_results, 10)  # Google API max is 10 per request
        }
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                results = []
                for item in data.get("items", []):
                    results.append({
                        "title": item.get("title", ""),
                        "snippet": item.get("snippet", ""),
                        "link": item.get("link", ""),
                        "displayLink": item.get("displayLink", ""),
                        "source": "google_api"
                    })
                
                return results
        
        except httpx.HTTPStatusError as e:
            # Fallback to scraping on API error
            return await self._search_public_web(query, num_results)
        except Exception as e:
            # Fallback to scraping on any error
            return await self._search_public_web(query, num_results)
    
    async def _search_public_web(
        self,
        query: str,
        num_results: Optional[int] = None
    ) -> List[Dict]:
        """
        Search public web by scraping search engines (fallback method)
        Uses DuckDuckGo HTML as it doesn't require API keys
        """
        num_results = num_results or self.max_results
        
        try:
            # Use DuckDuckGo HTML search (no API key needed)
            search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            
            async with httpx.AsyncClient(timeout=15, headers=self.headers, follow_redirects=True) as client:
                response = await client.get(search_url)
                response.raise_for_status()
                
                # Parse results
                soup = BeautifulSoup(response.text, 'html.parser')
                results = []
                
                # Find result divs
                result_divs = soup.find_all('div', class_='result')
                
                for div in result_divs[:num_results]:
                    try:
                        # Extract title and link
                        title_tag = div.find('a', class_='result__a')
                        if not title_tag:
                            continue
                        
                        title = title_tag.get_text(strip=True)
                        link = title_tag.get('href', '')
                        
                        # Extract snippet
                        snippet_tag = div.find('a', class_='result__snippet')
                        snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
                        
                        # Extract display link
                        url_tag = div.find('a', class_='result__url')
                        display_link = url_tag.get_text(strip=True) if url_tag else ""
                        
                        if title and link:
                            results.append({
                                "title": title,
                                "snippet": snippet,
                                "link": link,
                                "displayLink": display_link,
                                "source": "duckduckgo"
                            })
                    except Exception as e:
                        continue
                
                if not results:
                    # Try alternative scraping method
                    return await self._search_alternative(query, num_results)
                
                return results
        
        except Exception as e:
            return [{
                "title": "Search Error",
                "snippet": f"Unable to perform web search: {str(e)}. Please configure Google API for better results.",
                "link": "",
                "error": True,
                "source": "error"
            }]
    
    async def _search_alternative(
        self,
        query: str,
        num_results: Optional[int] = None
    ) -> List[Dict]:
        """
        Alternative search method using different approach
        """
        num_results = num_results or self.max_results
        
        try:
            # Use searx.be (public searx instance)
            search_url = f"https://searx.be/search?q={quote_plus(query)}&format=json&engines=duckduckgo,google"
            
            async with httpx.AsyncClient(timeout=15, headers=self.headers) as client:
                response = await client.get(search_url)
                response.raise_for_status()
                data = response.json()
                
                results = []
                for item in data.get("results", [])[:num_results]:
                    results.append({
                        "title": item.get("title", ""),
                        "snippet": item.get("content", ""),
                        "link": item.get("url", ""),
                        "displayLink": item.get("pretty_url", ""),
                        "source": "searx"
                    })
                
                return results if results else self._create_fallback_results(query)
        
        except Exception as e:
            return self._create_fallback_results(query)
    
    def _create_fallback_results(self, query: str) -> List[Dict]:
        """
        Create helpful fallback results when all search methods fail
        """
        return [{
            "title": "Web Search Unavailable",
            "snippet": f"I attempted to search for '{query}' but couldn't access search engines. "
                      f"For better results, please configure Google Custom Search API credentials.",
            "link": "https://programmablesearchengine.google.com/",
            "displayLink": "Setup Guide",
            "error": True,
            "source": "fallback"
        }]
    
    async def search_and_summarize(
        self,
        query: str,
        num_results: Optional[int] = None
    ) -> Dict:
        """
        Search and return formatted results
        
        Args:
            query: Search query
            num_results: Number of results
        
        Returns:
            Dict with query and results
        """
        results = await self.search(query, num_results)
        
        return {
            "query": query,
            "results": results,
            "count": len(results),
            "configured": self.is_configured()
        }


# Global search client instance
_search_client = None

def get_search_client() -> SearchClient:
    """Get or create search client instance"""
    global _search_client
    if _search_client is None:
        _search_client = SearchClient()
    return _search_client
