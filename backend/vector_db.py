"""
Vector database operations for embeddings storage and retrieval
"""
import uuid
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from backend.config import get_settings

settings = get_settings()

# Conditional imports based on configuration
if settings.VECTOR_DB_TYPE == "chromadb":
    import chromadb
    from chromadb.config import Settings as ChromaSettings


class VectorDB:
    """Vector database interface for embeddings storage"""
    
    def __init__(self):
        self.settings = get_settings()
        self.db_type = self.settings.VECTOR_DB_TYPE
        
        if self.db_type == "chromadb":
            self._init_chromadb()
        else:
            self._init_sqlite_vector()
    
    def _init_chromadb(self):
        """Initialize ChromaDB"""
        self.client = chromadb.PersistentClient(
            path=self.settings.CHROMA_PERSIST_DIRECTORY,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(name="documents")
        except:
            self.collection = self.client.create_collection(
                name="documents",
                metadata={"hnsw:space": "cosine"}
            )
    
    def _init_sqlite_vector(self):
        """Initialize SQLite-based vector storage"""
        import sqlite3
        from pathlib import Path
        
        db_path = Path(self.settings.DATABASE_PATH).parent / "vectors.db"
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        cursor = self.conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vector_embeddings (
                id TEXT PRIMARY KEY,
                doc_id TEXT NOT NULL,
                content TEXT NOT NULL,
                embedding BLOB NOT NULL,
                metadata TEXT
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_doc_id ON vector_embeddings(doc_id)")
        self.conn.commit()
    
    def add_documents(
        self,
        doc_ids: List[str],
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict]] = None
    ) -> bool:
        """Add documents with embeddings to the vector database"""
        try:
            if self.db_type == "chromadb":
                self._add_chromadb(doc_ids, texts, embeddings, metadatas)
            else:
                self._add_sqlite(doc_ids, texts, embeddings, metadatas)
            return True
        except Exception as e:
            print(f"Error adding documents: {e}")
            return False
    
    def _add_chromadb(
        self,
        doc_ids: List[str],
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict]]
    ):
        """Add documents to ChromaDB"""
        self.collection.add(
            ids=doc_ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas
        )
    
    def _add_sqlite(
        self,
        doc_ids: List[str],
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict]]
    ):
        """Add documents to SQLite vector storage"""
        import json
        cursor = self.conn.cursor()
        
        for i, (doc_id, text, embedding) in enumerate(zip(doc_ids, texts, embeddings)):
            embedding_blob = np.array(embedding, dtype=np.float32).tobytes()
            metadata = json.dumps(metadatas[i]) if metadatas and i < len(metadatas) else None
            
            cursor.execute("""
                INSERT OR REPLACE INTO vector_embeddings 
                (id, doc_id, content, embedding, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (str(uuid.uuid4()), doc_id, text, embedding_blob, metadata))
        
        self.conn.commit()
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_dict: Optional[Dict] = None
    ) -> Tuple[List[str], List[float], List[Dict]]:
        """
        Search for similar documents
        
        Returns:
            Tuple of (doc_ids, distances, metadatas)
        """
        if self.db_type == "chromadb":
            return self._search_chromadb(query_embedding, top_k, filter_dict)
        else:
            return self._search_sqlite(query_embedding, top_k)
    
    def _search_chromadb(
        self,
        query_embedding: List[float],
        top_k: int,
        filter_dict: Optional[Dict]
    ) -> Tuple[List[str], List[float], List[Dict]]:
        """Search ChromaDB"""
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter_dict if filter_dict else None
        )
        
        if not results['ids'] or not results['ids'][0]:
            return [], [], []
        
        doc_ids = results['ids'][0]
        distances = results['distances'][0] if 'distances' in results else [0.0] * len(doc_ids)
        metadatas = results['metadatas'][0] if 'metadatas' in results else [{}] * len(doc_ids)
        documents = results['documents'][0] if 'documents' in results else [''] * len(doc_ids)
        
        # Add documents to metadata
        for i, doc in enumerate(documents):
            if metadatas[i] is None:
                metadatas[i] = {}
            metadatas[i]['content'] = doc
        
        return doc_ids, distances, metadatas
    
    def _search_sqlite(
        self,
        query_embedding: List[float],
        top_k: int
    ) -> Tuple[List[str], List[float], List[Dict]]:
        """Search SQLite vector storage using cosine similarity"""
        import json
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT id, doc_id, content, embedding, metadata FROM vector_embeddings")
        rows = cursor.fetchall()
        
        if not rows:
            return [], [], []
        
        query_vec = np.array(query_embedding, dtype=np.float32)
        query_norm = np.linalg.norm(query_vec)
        
        similarities = []
        for row in rows:
            embedding_blob = row[3]
            embedding = np.frombuffer(embedding_blob, dtype=np.float32)
            
            # Cosine similarity
            dot_product = np.dot(query_vec, embedding)
            embedding_norm = np.linalg.norm(embedding)
            similarity = dot_product / (query_norm * embedding_norm + 1e-10)
            
            similarities.append((row, similarity))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        similarities = similarities[:top_k]
        
        doc_ids = []
        distances = []
        metadatas = []
        
        for row, similarity in similarities:
            doc_ids.append(row[1])  # doc_id
            distances.append(1.0 - similarity)  # Convert similarity to distance
            
            metadata = json.loads(row[4]) if row[4] else {}
            metadata['content'] = row[2]  # Add content
            metadatas.append(metadata)
        
        return doc_ids, distances, metadatas
    
    def delete_documents(self, doc_ids: List[str]) -> bool:
        """Delete documents from vector database"""
        try:
            if self.db_type == "chromadb":
                self.collection.delete(ids=doc_ids)
            else:
                cursor = self.conn.cursor()
                cursor.executemany(
                    "DELETE FROM vector_embeddings WHERE doc_id = ?",
                    [(doc_id,) for doc_id in doc_ids]
                )
                self.conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting documents: {e}")
            return False
    
    def get_document_count(self) -> int:
        """Get total number of documents"""
        if self.db_type == "chromadb":
            return self.collection.count()
        else:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(DISTINCT doc_id) FROM vector_embeddings")
            return cursor.fetchone()[0]
    
    def clear_all(self) -> bool:
        """Clear all documents from vector database"""
        try:
            if self.db_type == "chromadb":
                self.client.delete_collection(name="documents")
                self.collection = self.client.create_collection(
                    name="documents",
                    metadata={"hnsw:space": "cosine"}
                )
            else:
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM vector_embeddings")
                self.conn.commit()
            return True
        except Exception as e:
            print(f"Error clearing database: {e}")
            return False


# Global vector DB instance
_vector_db_instance = None

def get_vector_db() -> VectorDB:
    """Get or create vector database instance"""
    global _vector_db_instance
    if _vector_db_instance is None:
        _vector_db_instance = VectorDB()
    return _vector_db_instance
