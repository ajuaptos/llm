"""
SQLite database operations for Local-AI-RAG application
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from contextlib import contextmanager
from backend.config import get_settings


class Database:
    """SQLite database manager for chat history and metadata"""
    
    def __init__(self):
        self.settings = get_settings()
        self.db_path = Path(self.settings.DATABASE_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_database(self):
        """Initialize database schema"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Chat sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)
            
            # Chat messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    firewall_passed BOOLEAN DEFAULT 1,
                    scout_triggered BOOLEAN DEFAULT 0,
                    rag_used BOOLEAN DEFAULT 0,
                    metadata TEXT,
                    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id)
                )
            """)
            
            # Documents table for RAG
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doc_id TEXT UNIQUE NOT NULL,
                    title TEXT,
                    content TEXT NOT NULL,
                    source TEXT,
                    url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)
            
            # Search history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    results TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    session_id TEXT
                )
            """)
            
            # Firewall logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS firewall_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    blocked BOOLEAN NOT NULL,
                    reason TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON chat_messages(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_doc_id ON documents(doc_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_search_session ON search_history(session_id)")
    
    # Chat Session Methods
    def create_session(self, session_id: str, metadata: Optional[Dict] = None) -> bool:
        """Create a new chat session"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO chat_sessions (session_id, metadata) VALUES (?, ?)",
                    (session_id, json.dumps(metadata) if metadata else None)
                )
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session details"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM chat_sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    # Chat Message Methods
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        firewall_passed: bool = True,
        scout_triggered: bool = False,
        rag_used: bool = False,
        metadata: Optional[Dict] = None
    ) -> int:
        """Add a chat message"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO chat_messages 
                (session_id, role, content, firewall_passed, scout_triggered, rag_used, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id, role, content, firewall_passed, scout_triggered, rag_used,
                json.dumps(metadata) if metadata else None
            ))
            return cursor.lastrowid
    
    def get_chat_history(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """Get chat history for a session"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM chat_messages WHERE session_id = ? ORDER BY timestamp DESC"
            if limit:
                query += f" LIMIT {limit}"
            cursor.execute(query, (session_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in reversed(rows)]
    
    # Document Methods
    def add_document(
        self,
        doc_id: str,
        content: str,
        title: Optional[str] = None,
        source: Optional[str] = None,
        url: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Add a document for RAG"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO documents (doc_id, title, content, source, url, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    doc_id, title, content, source, url,
                    json.dumps(metadata) if metadata else None
                ))
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_document(self, doc_id: str) -> Optional[Dict]:
        """Get a document by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents WHERE doc_id = ?", (doc_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def list_documents(self, limit: Optional[int] = None) -> List[Dict]:
        """List all documents"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM documents ORDER BY created_at DESC"
            if limit:
                query += f" LIMIT {limit}"
            cursor.execute(query)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
            return cursor.rowcount > 0
    
    # Search History Methods
    def add_search(
        self,
        query: str,
        results: List[Dict],
        session_id: Optional[str] = None
    ) -> int:
        """Add search history entry"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO search_history (query, results, session_id)
                VALUES (?, ?, ?)
            """, (query, json.dumps(results), session_id))
            return cursor.lastrowid
    
    # Firewall Log Methods
    def log_firewall_check(
        self,
        content: str,
        blocked: bool,
        reason: Optional[str] = None
    ) -> int:
        """Log a firewall check"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO firewall_logs (content, blocked, reason)
                VALUES (?, ?, ?)
            """, (content, blocked, reason))
            return cursor.lastrowid
    
    # Statistics Methods
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Total messages
            cursor.execute("SELECT COUNT(*) as count FROM chat_messages")
            stats['total_messages'] = cursor.fetchone()['count']
            
            # Total documents
            cursor.execute("SELECT COUNT(*) as count FROM documents")
            stats['total_documents'] = cursor.fetchone()['count']
            
            # Total sessions
            cursor.execute("SELECT COUNT(*) as count FROM chat_sessions")
            stats['total_sessions'] = cursor.fetchone()['count']
            
            # Firewall blocks
            cursor.execute("SELECT COUNT(*) as count FROM firewall_logs WHERE blocked = 1")
            stats['firewall_blocks'] = cursor.fetchone()['count']
            
            # Scout triggers
            cursor.execute("SELECT COUNT(*) as count FROM chat_messages WHERE scout_triggered = 1")
            stats['scout_triggers'] = cursor.fetchone()['count']
            
            # RAG usage
            cursor.execute("SELECT COUNT(*) as count FROM chat_messages WHERE rag_used = 1")
            stats['rag_usage'] = cursor.fetchone()['count']
            
            return stats


# Global database instance
_db_instance = None

def get_database() -> Database:
    """Get or create database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
