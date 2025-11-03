"""
Ollama LLM client for local language model interactions
"""
import httpx
from typing import Dict, List, Optional, AsyncGenerator
from backend.config import get_settings


class OllamaClient:
    """Client for interacting with Ollama API"""
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.OLLAMA_BASE_URL
        self.main_model = self.settings.OLLAMA_MAIN_MODEL
        self.scout_model = self.settings.OLLAMA_SCOUT_MODEL
        self.timeout = self.settings.OLLAMA_TIMEOUT
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> str:
        """
        Generate completion from Ollama
        
        Args:
            prompt: User prompt
            model: Model to use (defaults to main model)
            system: System prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream response
        
        Returns:
            Generated text
        """
        model = model or self.main_model
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        
        if system:
            payload["system"] = system
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Chat with Ollama using conversation history
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        
        Returns:
            Generated response
        """
        model = model or self.main_model
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            return result.get("message", {}).get("content", "")
    
    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat responses from Ollama
        
        Args:
            messages: Conversation messages
            model: Model to use
            temperature: Sampling temperature
        
        Yields:
            Response chunks
        """
        model = model or self.main_model
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature
            }
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        import json
                        try:
                            data = json.loads(line)
                            if "message" in data:
                                content = data["message"].get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
    
    async def embed(
        self,
        text: str,
        model: Optional[str] = None
    ) -> List[float]:
        """
        Get embeddings for text using Ollama
        
        Args:
            text: Text to embed
            model: Embedding model to use
        
        Returns:
            Embedding vector
        """
        model = model or self.settings.OLLAMA_EMBEDDING_MODEL
        
        payload = {
            "model": model,
            "prompt": text
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/embeddings",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            return result.get("embedding", [])
    
    async def list_models(self) -> List[Dict]:
        """List available Ollama models"""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            result = response.json()
            return result.get("models", [])
    
    async def check_health(self) -> bool:
        """Check if Ollama is running and accessible"""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except:
            return False
    
    async def pull_model(self, model: str) -> bool:
        """Pull a model from Ollama registry"""
        try:
            async with httpx.AsyncClient(timeout=600) as client:
                response = await client.post(
                    f"{self.base_url}/api/pull",
                    json={"name": model, "stream": False}
                )
                return response.status_code == 200
        except:
            return False


# Global client instance
_ollama_client = None

def get_ollama_client() -> OllamaClient:
    """Get or create Ollama client instance"""
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    return _ollama_client
