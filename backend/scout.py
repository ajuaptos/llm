"""
Scout agent for uncertainty detection and web search
"""
import re
from typing import Dict, Optional, Tuple, List
from backend.config import get_settings
from backend.llm_client import get_ollama_client
from backend.search_client import get_search_client
from backend.database import get_database


class Scout:
    """Intelligent scout agent for detecting uncertainty and augmenting with search"""
    
    def __init__(self):
        self.settings = get_settings()
        self.enabled = self.settings.SCOUT_ENABLED
        self.threshold = self.settings.SCOUT_UNCERTAINTY_THRESHOLD
        self.llm = get_ollama_client()
        self.search = get_search_client()
        self.db = get_database()
        
        # Uncertainty indicators
        self.uncertainty_phrases = [
            "i don't know", "i'm not sure", "i don't have", "i cannot confirm",
            "i'm uncertain", "unclear", "not certain", "may not be accurate",
            "i don't have access to", "i don't have information",
            "as of my last update", "i cannot provide real-time",
            "knowledge cutoff", "my training data", "my knowledge", 
            "i'm a large language model", "i'm an ai", "i'm a text-based",
            "i cannot access", "i don't have the ability",
            "suggest some ways", "you can visit", "you can check",
            "i recommend", "i suggest you check"
        ]
        
        # Current/time-sensitive query patterns
        self.current_info_patterns = [
            r'\b(current|latest|recent|today|now|this (year|month|week))\b',
            r'\b(news|updates|happening)\b',
            r'\b\d{4}\b',  # Year mentioned
            r'\b(price|stock|weather|score)\b'
        ]
    
    async def analyze_response(
        self,
        query: str,
        response: str
    ) -> Tuple[bool, float, Optional[str]]:
        """
        Analyze LLM response for uncertainty
        
        Args:
            query: Original user query
            response: LLM response to analyze
        
        Returns:
            Tuple of (needs_search, confidence_score, reason)
        """
        if not self.enabled:
            return False, 1.0, None
        
        # Quick pattern check for uncertainty phrases
        response_lower = response.lower()
        query_lower = query.lower()
        
        # Check for explicit uncertainty
        for phrase in self.uncertainty_phrases:
            if phrase in response_lower:
                return True, 0.3, f"Uncertainty detected: '{phrase}'"
        
        # Check if query requires current/real-time information
        needs_current_info = any(
            re.search(pattern, query_lower, re.IGNORECASE)
            for pattern in self.current_info_patterns
        )
        
        if needs_current_info:
            # For time-sensitive queries, always trigger Scout to get fresh data
            # unless the response is very short and confident (< 100 chars)
            if len(response) > 100:
                return True, 0.5, "Query requires current/real-time information"
            
            # Use LLM to assess if response adequately answers time-sensitive query
            needs_search, confidence = await self._llm_uncertainty_check(query, response)
            if needs_search:
                return True, confidence, "Query requires current information"
        
        # Response seems confident
        return False, 0.9, None
    
    async def _llm_uncertainty_check(
        self,
        query: str,
        response: str
    ) -> Tuple[bool, float]:
        """
        Use LLM to assess response confidence
        
        Args:
            query: Original query
            response: LLM response
        
        Returns:
            Tuple of (needs_search, confidence_score)
        """
        system_prompt = """You are an uncertainty detector. Analyze if the response adequately answers the query or if web search would help.

Consider:
1. Does response directly answer the question?
2. Is response vague or hedged?
3. Does query need current/real-time data?
4. Would web search provide better information?

Respond with ONLY:
CONFIDENT - Response is adequate, no search needed
UNCERTAIN: [confidence 0.0-1.0] - Search would help

Example:
UNCERTAIN: 0.4"""

        prompt = f"""Query: {query}

Response: {response}

Assess if web search would improve this response."""
        
        try:
            result = await self.llm.generate(
                prompt=prompt,
                system=system_prompt,
                model=self.settings.OLLAMA_SCOUT_MODEL,
                temperature=0.1,
                max_tokens=50
            )
            
            result = result.strip()
            
            if result.startswith("CONFIDENT"):
                return False, 0.9
            elif result.startswith("UNCERTAIN"):
                # Extract confidence score
                match = re.search(r'(\d+\.?\d*)', result)
                confidence = float(match.group(1)) if match else 0.5
                return True, confidence
            else:
                return False, 0.7
        
        except Exception as e:
            print(f"Scout LLM check failed: {e}")
            return False, 0.7
    
    async def search_and_augment(
        self,
        query: str,
        original_response: str,
        session_id: Optional[str] = None
    ) -> Dict:
        """
        Perform web search and augment response
        
        Args:
            query: User query
            original_response: Original LLM response
            session_id: Optional session ID for logging
        
        Returns:
            Dict with augmented response and search results
        """
        print(f"[SCOUT] Starting search for query: {query}")
        
        if not self.search.is_configured():
            print("[SCOUT] Search API not configured, using fallback")
        
        # Perform web search
        search_results = await self.search.search(query, num_results=5)
        print(f"[SCOUT] Got {len(search_results)} search results")
        
        if search_results:
            for i, result in enumerate(search_results[:3]):
                print(f"[SCOUT] Result {i+1}: {result.get('title', 'N/A')[:50]}...")
        
        # Log search
        if session_id:
            try:
                self.db.add_search(query, search_results, session_id)
            except Exception as e:
                print(f"Failed to log search: {e}")
        
        # Create augmented response with search context
        augmented_response = await self._create_augmented_response(
            query,
            original_response,
            search_results
        )
        
        return {
            "augmented_response": augmented_response,
            "search_performed": True,
            "search_results": search_results,
            "original_response": original_response
        }
    
    async def _create_augmented_response(
        self,
        query: str,
        original_response: str,
        search_results: List[Dict]
    ) -> str:
        """
        Create augmented response using search results
        
        Args:
            query: User query
            original_response: Original LLM response
            search_results: Web search results
        
        Returns:
            Augmented response
        """
        if not search_results or search_results[0].get("error"):
            return original_response
        
        # Format search results as context
        search_context = "\n\n".join([
            f"Source: {r['title']}\n{r['snippet']}\nURL: {r['link']}"
            for r in search_results[:3]
        ])
        
        system_prompt = """You are a helpful assistant. Using the web search results provided, 
create an improved response that incorporates current, accurate information.

Keep the response natural and cite sources when relevant."""

        prompt = f"""Original Query: {query}

Initial Response: {original_response}

Web Search Results:
{search_context}

Create an improved response that incorporates the search results. Be concise and cite sources."""
        
        try:
            augmented = await self.llm.generate(
                prompt=prompt,
                system=system_prompt,
                temperature=0.7,
                max_tokens=500
            )
            return augmented
        
        except Exception as e:
            print(f"Failed to create augmented response: {e}")
            return original_response
    
    async def enhance_query(
        self,
        query: str,
        response: str,
        session_id: Optional[str] = None
    ) -> Dict:
        """
        Main method to enhance query with scout capabilities
        
        Args:
            query: User query
            response: Initial LLM response
            session_id: Optional session ID
        
        Returns:
            Dict with final response and metadata
        """
        # Analyze if search is needed
        needs_search, confidence, reason = await self.analyze_response(query, response)
        
        result = {
            "response": response,
            "scout_triggered": False,
            "confidence": confidence,
            "search_performed": False,
            "search_results": []
        }
        
        if needs_search and confidence < self.threshold:
            result["scout_triggered"] = True
            
            # Perform search and augmentation
            augmented = await self.search_and_augment(query, response, session_id)
            
            result.update({
                "response": augmented.get("augmented_response", response),
                "search_performed": augmented.get("search_performed", False),
                "search_results": augmented.get("search_results", []),
                "original_response": response
            })
        
        return result
    
    def get_stats(self) -> Dict:
        """Get scout statistics"""
        stats = self.db.get_stats()
        return {
            "enabled": self.enabled,
            "threshold": self.threshold,
            "total_triggers": stats.get("scout_triggers", 0),
            "search_configured": self.search.is_configured()
        }


# Global scout instance
_scout_instance = None

def get_scout() -> Scout:
    """Get or create scout instance"""
    global _scout_instance
    if _scout_instance is None:
        _scout_instance = Scout()
    return _scout_instance
