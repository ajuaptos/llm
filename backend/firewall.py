"""
AI Firewall for content filtering and safety using AIM Security API
"""
import httpx
from typing import Dict, Tuple, Optional, List
from backend.config import get_settings
from backend.database import get_database


class AIFirewall:
    """AI-powered content filtering and safety system using AIM Security API"""
    
    def __init__(self):
        self.settings = get_settings()
        self.enabled = self.settings.FIREWALL_ENABLED
        self.db = get_database()
        
        # AIM Firewall API configuration
        self.aim_api_url = "https://api.aim.security/fw/v1/analyze"
        self.aim_api_key = "aim-demo_cato_america-e5ea8b5c1b138b70288af3aee7ce8c1ca36d7597b58d1230"
        self.aim_user_email = "fidel@aimsec.cloud"
        
        # Message history for context (max 10 messages)
        self.conversation_history: List[Dict[str, str]] = []
    
    def _add_to_history(self, role: str, content: str):
        """Add message to conversation history"""
        self.conversation_history.append({
            "role": role,
            "content": content
        })
        # Keep only last 10 messages
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
    
    async def check_content(
        self,
        content: str,
        context: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if content should be blocked using AIM Firewall API
        
        Args:
            content: Content to check (user message)
            context: Optional context for better judgment
        
        Returns:
            Tuple of (is_safe, reason_if_blocked)
        """
        if not self.enabled:
            return True, None
        
        try:
            # Build messages array with conversation history + new message
            messages = self.conversation_history.copy()
            messages.append({
                "role": "user",
                "content": content
            })
            
            # Call AIM Firewall API
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.aim_api_url,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.aim_api_key}",
                        "x-aim-user-email": self.aim_user_email
                    },
                    json={"messages": messages}
                )
                
                response.raise_for_status()
                result = response.json()
                
                # Check if AIM Firewall blocked the content
                # Adjust based on actual API response structure
                is_safe = result.get("safe", True)
                threat_detected = result.get("threat_detected", False)
                reason = result.get("reason") or result.get("threat_type")
                
                if threat_detected or not is_safe:
                    blocked_reason = reason or "Content blocked by AIM Firewall"
                    self._log_check(content, blocked=True, reason=blocked_reason)
                    return False, blocked_reason
                
                # Content is safe
                self._log_check(content, blocked=False, reason=None)
                
                # Add user message to history if safe
                self._add_to_history("user", content)
                
                return True, None
        
        except httpx.HTTPStatusError as e:
            # API returned error status
            print(f"AIM Firewall API error: {e.response.status_code} - {e.response.text}")
            # Fail open on API errors (allow content but log error)
            return True, None
        
        except Exception as e:
            # Network or other error
            print(f"AIM Firewall check failed: {e}")
            # Fail open on errors (allow content but log error)
            return True, None
    
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
        Filter LLM response before sending to user using AIM Firewall API
        
        Args:
            response: LLM generated response
        
        Returns:
            Tuple of (is_safe, filtered_response)
        """
        if not self.enabled:
            return True, response
        
        try:
            # Build messages array with conversation history + assistant response
            messages = self.conversation_history.copy()
            messages.append({
                "role": "assistant",
                "content": response
            })
            
            # Call AIM Firewall API
            async with httpx.AsyncClient(timeout=10.0) as client:
                api_response = await client.post(
                    self.aim_api_url,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.aim_api_key}",
                        "x-aim-user-email": self.aim_user_email
                    },
                    json={"messages": messages}
                )
                
                api_response.raise_for_status()
                result = api_response.json()
                
                # Check if AIM Firewall blocked the response
                is_safe = result.get("safe", True)
                threat_detected = result.get("threat_detected", False)
                
                if threat_detected or not is_safe:
                    filtered = (
                        "I apologize, but I cannot provide that response as it may contain "
                        "inappropriate or harmful content. Please rephrase your question."
                    )
                    return False, filtered
                
                # Response is safe, add to history
                self._add_to_history("assistant", response)
                return True, response
        
        except Exception as e:
            print(f"AIM Firewall response check failed: {e}")
            # Fail open on errors
            return True, response
    
    def get_stats(self) -> Dict:
        """Get firewall statistics"""
        stats = self.db.get_stats()
        return {
            "enabled": self.enabled,
            "total_blocks": stats.get("firewall_blocks", 0),
            "aim_api_configured": bool(self.aim_api_key),
            "conversation_history_size": len(self.conversation_history)
        }
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []


# Global firewall instance
_firewall_instance = None

def get_firewall() -> AIFirewall:
    """Get or create firewall instance"""
    global _firewall_instance
    if _firewall_instance is None:
        _firewall_instance = AIFirewall()
    return _firewall_instance
