"""
RAG (Retrieval Augmented Generation) Pipeline
Handles document ingestion, chunking, embedding, retrieval, and augmentation
"""
import uuid
import re
from typing import List, Dict, Optional, Tuple
from backend.config import get_settings
from backend.embeddings_client import get_embeddings_client
from backend.vector_db import get_vector_db
from backend.database import get_database
from backend.llm_client import get_ollama_client


class RAGPipeline:
    """Complete RAG pipeline for document processing and retrieval"""
    
    def __init__(self):
        self.settings = get_settings()
        self.embeddings = get_embeddings_client()
        self.vector_db = get_vector_db()
        self.db = get_database()
        self.llm = get_ollama_client()
        
        self.chunk_size = self.settings.CHUNK_SIZE
        self.chunk_overlap = self.settings.CHUNK_OVERLAP
        self.top_k = self.settings.RAG_TOP_K
        self.similarity_threshold = self.settings.RAG_SIMILARITY_THRESHOLD
    
    def chunk_text(
        self,
        text: str,
        chunk_size: Optional[int] = None,
        overlap: Optional[int] = None
    ) -> List[str]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Text to chunk
            chunk_size: Size of each chunk in characters
            overlap: Overlap between chunks
        
        Returns:
            List of text chunks
        """
        chunk_size = chunk_size or self.chunk_size
        overlap = overlap or self.chunk_overlap
        
        # Clean text
        text = re.sub(r'\s+', ' ', text).strip()
        
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence ending
                sentence_end = max(
                    text.rfind('. ', start, end),
                    text.rfind('! ', start, end),
                    text.rfind('? ', start, end)
                )
                if sentence_end > start:
                    end = sentence_end + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
        
        return chunks
    
    async def ingest_document(
        self,
        content: str,
        title: Optional[str] = None,
        source: Optional[str] = None,
        url: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Ingest a document into the RAG system
        
        Args:
            content: Document content
            title: Document title
            source: Source identifier
            url: Source URL
            metadata: Additional metadata
        
        Returns:
            Dict with ingestion results
        """
        # Generate document ID
        doc_id = str(uuid.uuid4())
        
        # Store document in database
        success = self.db.add_document(
            doc_id=doc_id,
            content=content,
            title=title,
            source=source,
            url=url,
            metadata=metadata
        )
        
        if not success:
            return {
                "success": False,
                "error": "Failed to store document in database"
            }
        
        # Chunk the document
        chunks = self.chunk_text(content)
        
        # Generate embeddings for chunks
        embeddings = await self.embeddings.embed_batch(chunks)
        
        # Create chunk IDs and metadata
        chunk_ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
        chunk_metadatas = [
            {
                "doc_id": doc_id,
                "chunk_index": i,
                "title": title or "",
                "source": source or "",
                "url": url or ""
            }
            for i in range(len(chunks))
        ]
        
        # Store in vector database
        vector_success = self.vector_db.add_documents(
            doc_ids=chunk_ids,
            texts=chunks,
            embeddings=embeddings,
            metadatas=chunk_metadatas
        )
        
        if not vector_success:
            return {
                "success": False,
                "error": "Failed to store embeddings"
            }
        
        return {
            "success": True,
            "doc_id": doc_id,
            "chunks_created": len(chunks),
            "title": title
        }
    
    async def ingest_documents_batch(
        self,
        documents: List[Dict]
    ) -> List[Dict]:
        """
        Ingest multiple documents
        
        Args:
            documents: List of document dicts with content, title, etc.
        
        Returns:
            List of ingestion results
        """
        results = []
        for doc in documents:
            result = await self.ingest_document(
                content=doc.get("content", ""),
                title=doc.get("title"),
                source=doc.get("source"),
                url=doc.get("url"),
                metadata=doc.get("metadata")
            )
            results.append(result)
        
        return results
    
    async def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None
    ) -> List[Dict]:
        """
        Retrieve relevant documents for a query
        
        Args:
            query: Search query
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score
        
        Returns:
            List of retrieved documents with metadata
        """
        top_k = top_k or self.top_k
        similarity_threshold = similarity_threshold or self.similarity_threshold
        
        # Generate query embedding
        query_embedding = await self.embeddings.embed_text(query)
        
        # Search vector database
        doc_ids, distances, metadatas = self.vector_db.search(
            query_embedding=query_embedding,
            top_k=top_k
        )
        
        # Filter by similarity threshold (convert distance to similarity)
        results = []
        for doc_id, distance, metadata in zip(doc_ids, distances, metadatas):
            similarity = 1.0 - distance
            
            if similarity >= similarity_threshold:
                results.append({
                    "doc_id": metadata.get("doc_id", doc_id),
                    "content": metadata.get("content", ""),
                    "title": metadata.get("title", ""),
                    "source": metadata.get("source", ""),
                    "url": metadata.get("url", ""),
                    "similarity": similarity,
                    "chunk_index": metadata.get("chunk_index", 0)
                })
        
        return results
    
    async def generate_with_context(
        self,
        query: str,
        retrieved_docs: List[Dict],
        chat_history: Optional[List[Dict]] = None
    ) -> str:
        """
        Generate response using retrieved context
        
        Args:
            query: User query
            retrieved_docs: Retrieved documents
            chat_history: Optional chat history
        
        Returns:
            Generated response
        """
        # Build context from retrieved documents
        context_parts = []
        for i, doc in enumerate(retrieved_docs[:3], 1):  # Use top 3
            context_parts.append(
                f"[Source {i}] {doc['title']}\n{doc['content']}"
            )
        
        context = "\n\n".join(context_parts)
        
        # Build prompt
        system_prompt = """You are a helpful assistant. Use the provided context to answer the question accurately.
If the context doesn't contain enough information, say so clearly.
Cite sources using [Source 1], [Source 2], etc."""

        prompt = f"""Context:
{context}

Question: {query}

Provide a clear, accurate answer based on the context above."""
        
        # Generate response
        if chat_history:
            # Use chat API with history
            messages = chat_history.copy()
            messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = await self.llm.chat(messages=messages)
        else:
            # Use generate API
            response = await self.llm.generate(
                prompt=prompt,
                system=system_prompt,
                temperature=0.7
            )
        
        return response
    
    async def query(
        self,
        query: str,
        top_k: Optional[int] = None,
        chat_history: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Complete RAG query: retrieve and generate
        
        Args:
            query: User query
            top_k: Number of documents to retrieve
            chat_history: Optional chat history
        
        Returns:
            Dict with response and retrieved documents
        """
        # Retrieve relevant documents
        retrieved_docs = await self.retrieve(query, top_k=top_k)
        
        if not retrieved_docs:
            return {
                "response": "I couldn't find any relevant information in the knowledge base to answer your question.",
                "retrieved_docs": [],
                "rag_used": False
            }
        
        # Generate response with context
        response = await self.generate_with_context(
            query=query,
            retrieved_docs=retrieved_docs,
            chat_history=chat_history
        )
        
        return {
            "response": response,
            "retrieved_docs": retrieved_docs,
            "rag_used": True
        }
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document and its embeddings"""
        # Delete from vector DB
        # Need to find all chunk IDs for this doc
        # For now, delete from SQL DB only
        return self.db.delete_document(doc_id)
    
    def list_documents(self, limit: Optional[int] = None) -> List[Dict]:
        """List all ingested documents"""
        return self.db.list_documents(limit=limit)
    
    def get_stats(self) -> Dict:
        """Get RAG pipeline statistics"""
        db_stats = self.db.get_stats()
        vector_count = self.vector_db.get_document_count()
        
        return {
            "total_documents": db_stats.get("total_documents", 0),
            "total_chunks": vector_count,
            "rag_queries": db_stats.get("rag_usage", 0),
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "top_k": self.top_k
        }


# Global RAG pipeline instance
_rag_pipeline = None

def get_rag_pipeline() -> RAGPipeline:
    """Get or create RAG pipeline instance"""
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline()
    return _rag_pipeline
