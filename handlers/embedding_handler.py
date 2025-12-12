"""
Embedding Handler - Semantic similarity, embeddings, and RAG tasks.
"""
import requests
import json
import re
from typing import Optional, List, Dict, Any
import logging
import os

from .base import BaseHandler, TaskContext

logger = logging.getLogger(__name__)


class EmbeddingHandler(BaseHandler):
    """Handler for embedding and RAG tasks."""
    
    priority = 40
    
    def can_handle(self, task_type: str, context: TaskContext) -> bool:
        page_lower = context.page_text.lower()
        return (
            'embed' in page_lower or
            'rag' in page_lower or
            'retrieval' in page_lower or
            'similarity' in page_lower or
            'semantic' in page_lower or
            'vector' in page_lower or
            task_type in ['embedding', 'rag']
        )
    
    async def handle(self, context: TaskContext) -> str:
        logger.info("Processing embedding/RAG task")
        
        page_lower = context.page_text.lower()
        
        if 'similarity' in page_lower:
            return await self._calculate_similarity(context)
        elif 'rag' in page_lower or 'retrieval' in page_lower:
            return await self._rag_query(context)
        else:
            return await self._generate_embeddings(context)
    
    async def _calculate_similarity(self, context: TaskContext) -> str:
        """Calculate semantic similarity between texts."""
        try:
            from sentence_transformers import SentenceTransformer
            from sklearn.metrics.pairwise import cosine_similarity
            import numpy as np
            
            # Extract texts to compare
            texts = self._extract_texts(context)
            
            if len(texts) < 2:
                raise ValueError("Need at least 2 texts to compare similarity")
            
            # Load model
            model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Generate embeddings
            embeddings = model.encode(texts)
            
            # Calculate similarity
            similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
            
            return str(round(float(similarity), 4))
            
        except ImportError:
            logger.warning("sentence-transformers not available, using API fallback")
            return await self._similarity_api_fallback(context)
    
    async def _rag_query(self, context: TaskContext) -> str:
        """Perform RAG (Retrieval Augmented Generation)."""
        try:
            from sentence_transformers import SentenceTransformer
            from sklearn.metrics.pairwise import cosine_similarity
            import numpy as np
            
            # Download documents
            data_url = context.extract_file_url()
            if data_url:
                r = requests.get(data_url)
                if '.json' in data_url:
                    documents = r.json()
                    if isinstance(documents, list):
                        doc_texts = [str(d) for d in documents]
                    else:
                        doc_texts = [str(documents)]
                else:
                    doc_texts = r.text.split('\n')
            else:
                doc_texts = [context.page_text]
            
            # Extract query
            query = self._extract_query(context)
            
            # Load model
            model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Encode documents and query
            doc_embeddings = model.encode(doc_texts)
            query_embedding = model.encode([query])
            
            # Find most relevant document
            similarities = cosine_similarity(query_embedding, doc_embeddings)[0]
            best_idx = np.argmax(similarities)
            
            return doc_texts[best_idx]
            
        except ImportError:
            logger.error("sentence-transformers not available")
            return "skip"
    
    async def _generate_embeddings(self, context: TaskContext) -> str:
        """Generate embeddings for text."""
        try:
            from sentence_transformers import SentenceTransformer
            
            texts = self._extract_texts(context)
            
            model = SentenceTransformer('all-MiniLM-L6-v2')
            embeddings = model.encode(texts)
            
            # Return as JSON
            return json.dumps(embeddings.tolist())
            
        except ImportError:
            logger.error("sentence-transformers not available")
            return "skip"
    
    async def _similarity_api_fallback(self, context: TaskContext) -> str:
        """Fallback using Gemini API for similarity."""
        try:
            import google.generativeai as genai
            
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                return "skip"
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.0-flash')
            
            texts = self._extract_texts(context)
            
            prompt = f"""Calculate the semantic similarity between these two texts on a scale of 0 to 1.
            
Text 1: {texts[0]}
Text 2: {texts[1]}

Return ONLY a number between 0 and 1 (e.g., 0.85). No other text."""
            
            response = model.generate_content(prompt)
            result = response.text.strip()
            
            # Extract number
            match = re.search(r'(\d+\.?\d*)', result)
            if match:
                return match.group(1)
            return result
            
        except Exception as e:
            logger.error(f"Similarity API fallback failed: {e}")
            return "skip"
    
    def _extract_texts(self, context: TaskContext) -> List[str]:
        """Extract texts to compare from context."""
        texts = []
        
        # Look for quoted strings
        matches = re.findall(r'["\']([^"\']+)["\']', context.page_text)
        texts.extend(matches)
        
        # If not enough, try numbered items
        if len(texts) < 2:
            numbered = re.findall(r'\d+\.\s*(.+?)(?=\d+\.|$)', context.page_text, re.DOTALL)
            texts.extend([t.strip() for t in numbered if t.strip()])
        
        return texts[:2] if len(texts) >= 2 else texts
    
    def _extract_query(self, context: TaskContext) -> str:
        """Extract query for RAG from context."""
        # Look for query pattern
        match = re.search(r'query[:\s]+["\']?(.+?)["\']?(?:\n|$)', context.page_text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Look for question
        match = re.search(r'question[:\s]+["\']?(.+?)["\']?(?:\n|$)', context.page_text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        return "What is the answer?"
