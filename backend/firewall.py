"""
AI Firewall for content filtering and safety
"""
import re
from typing import Dict, Tuple, Optional, List
from backend.config import get_settings
from backend.llm_client import get_ollama_client
from backend.database import get_database


class AIFirewall:
    """AI-powered content filtering and safety system"""
    
    def __init__(self):
        self.settings = get_settings()
        self.enabled = self.settings.FIREWALL_ENABLED
        self.llm = get_ollama_client()
        self.db = get_database()
        
        # Pattern-based filters (fast pre-check)
        self.blocked_patterns = [
            r'\b(hack|exploit|vulnerability)\s+(tutorial|guide)\b',
            r'\bhow\s+to\s+(hack|steal|break\s+into)\b',
            r'\b(phishing|malware|ransomware)\s+(tutorial|guide)\b',
            r'\b(illegal|unlawful)\s+(drugs|weapons|activity)\b',
        ]
        
        # Sensitive topics that require LLM review
        self.sensitive_keywords = [
            'violence', 'weapon', 'drug', 'illegal', 'hack', 'exploit',
            'hate', 'racist', 'sexist', 'harm', 'kill', 'suicide'
        ]
    
    async def check_content(
        self,
        content: str,
        context: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if content should be blocked
        
        Args:
            content: Content to check
            context: Optional context for better judgment
        
        Returns:
            Tuple of (is_safe, reason_if_blocked)
        """
        if not self.enabled:
            return True, None
        
        # Fast pattern-based check
        is_safe_pattern, pattern_reason = self._check_patterns(content)
        if not is_safe_pattern:
            self._log_check(content, blocked=True, reason=pattern_reason)
            return False, pattern_reason
        
        # Check for sensitive keywords
        if self._contains_sensitive_keywords(content):
            # Use LLM for nuanced judgment
            is_safe_llm, llm_reason = await self._llm_safety_check(content, context)
            self._log_check(content, blocked=not is_safe_llm, reason=llm_reason)
            return is_safe_llm, llm_reason
        
        # Content is safe
        self._log_check(content, blocked=False, reason=None)
        return True, None
    
    def _check_patterns(self, content: str) -> Tuple[bool, Optional[str]]:
        """Check content against blocked patterns"""
        content_lower = content.lower()
        
        for pattern in self.blocked_patterns:
            if re.search(pattern, content_lower, re.IGNORECASE):
                return False, f"Content matches blocked pattern: {pattern}"
        
        return True, None
    
    def _contains_sensitive_keywords(self, content: str) -> bool:
        """Check if content contains sensitive keywords"""
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in self.sensitive_keywords)
    
    async def _llm_safety_check(
        self,
        content: str,
        context: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Use LLM to make nuanced safety judgment
        
        Args:
            content: Content to check
            context: Optional context
        
        Returns:
            Tuple of (is_safe, reason_if_unsafe)
        """
        system_prompt = """You are a content safety classifier. Analyze the given content and determine if it:
1. Promotes illegal activities
2. Contains hate speech or discriminatory content
3. Encourages violence or harm
4. Contains explicit harmful instructions
5. Violates ethical guidelines

Respond with ONLY one of these:
SAFE - Content is acceptable
UNSAFE: [brief reason] - Content should be blocked

Be balanced - allow educational, news, or fictional content that mentions sensitive topics."""

        prompt = f"Content to analyze:\n{content}"
        if context:
            prompt += f"\n\nContext:\n{context}"
        
        try:
            response = await self.llm.generate(
                prompt=prompt,
                system=system_prompt,
                model=self.settings.OLLAMA_SCOUT_MODEL,  # Use smaller model for speed
                temperature=0.1,  # Low temperature for consistent judgment
                max_tokens=100
            )
            
            response = response.strip()
            
            if response.startswith("SAFE"):
                return True, None
            elif response.startswith("UNSAFE:"):
                reason = response.replace("UNSAFE:", "").strip()
                return False, reason or "Content flagged as unsafe by AI firewall"
            else:
                # Default to safe if response is unclear
                return True, None
        
        except Exception as e:
            # If LLM check fails, err on the side of caution for sensitive content
            return False, f"Unable to verify content safety: {str(e)}"
    
    def _log_check(self, content: str, blocked: bool, reason: Optional[str]):
        """Log firewall check to database"""
        try:
            self.db.log_firewall_check(
                content=content[:500],  # Truncate for storage
                blocked=blocked,
                reason=reason
            )
        except Exception as e:
            print(f"Failed to log firewall check: {e}")
    
    async def filter_response(self, response: str) -> Tuple[bool, str]:
        """
        Filter LLM response before sending to user
        
        Args:
            response: LLM generated response
        
        Returns:
            Tuple of (is_safe, filtered_response)
        """
        is_safe, reason = await self.check_content(response)
        
        if not is_safe:
            filtered = (
                "I apologize, but I cannot provide that response as it may contain "
                "inappropriate or harmful content. Please rephrase your question."
            )
            return False, filtered
        
        return True, response
    
    def get_stats(self) -> Dict:
        """Get firewall statistics"""
        stats = self.db.get_stats()
        return {
            "enabled": self.enabled,
            "total_blocks": stats.get("firewall_blocks", 0),
            "patterns_count": len(self.blocked_patterns),
            "sensitive_keywords_count": len(self.sensitive_keywords)
        }


# Global firewall instance
_firewall_instance = None

def get_firewall() -> AIFirewall:
    """Get or create firewall instance"""
    global _firewall_instance
    if _firewall_instance is None:
        _firewall_instance = AIFirewall()
    return _firewall_instance
