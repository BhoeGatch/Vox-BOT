"""Optimized search engine with multiple fast backends"""
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re

class FastSearchEngine:
    """Optimized search engine with multiple backends"""
    
    def __init__(self, documents, method='tfidf'):
        """
        Initialize search engine
        
        Args:
            documents: List of dicts with 'filename' and 'content'
            method: 'tfidf' (default), 'count', or 'keyword'
        """
        self.documents = documents or []
        self.method = method
        self.vectorizer = None
        self.doc_matrix = None
        
        corpus = [doc.get('content', '') for doc in self.documents]
        
        if not corpus or not any(c.strip() for c in corpus):
            return
        
        try:
            if method == 'tfidf':
                # Optimized TF-IDF for precise, relevant matches
                self.vectorizer = TfidfVectorizer(
                    stop_words='english',
                    max_features=8000,  # Balanced feature count
                    ngram_range=(1, 2),  # Focus on unigrams and bigrams for clarity
                    min_df=1,
                    max_df=0.75,  # Filter out overly common terms
                    sublinear_tf=True,  # Better handling of term frequency
                    use_idf=True,
                    token_pattern=r'\b[a-zA-Z][a-zA-Z]+\b'  # Only alphabetic tokens
                )
                self.doc_matrix = self.vectorizer.fit_transform(corpus)
                
            elif method == 'count':
                # Count Vectorizer: Faster, simpler
                self.vectorizer = CountVectorizer(
                    stop_words='english',
                    max_features=3000,
                    binary=True  # Just presence/absence for speed
                )
                self.doc_matrix = self.vectorizer.fit_transform(corpus)
                
            elif method == 'keyword':
                # Pure keyword matching: Fastest
                self.vectorizer = None
                self.doc_matrix = None
                
        except ValueError:
            # Empty vocabulary
            self.vectorizer = None
            self.doc_matrix = None
    
    def search(self, query, top_k=3):
        """
        Search for relevant documents
        
        Args:
            query: Search query string
            top_k: Number of results to return
            
        Returns:
            List of dicts with filename, content, similarity
        """
        query = (query or '').strip()
        if not query or not self.documents:
            return []
        
        # Keyword fallback
        if self.method == 'keyword' or self.vectorizer is None or self.doc_matrix is None:
            return self._keyword_search(query, top_k)
        
        try:
            # Vector-based search
            query_vec = self.vectorizer.transform([query])
            
            # Fast cosine similarity
            similarities = cosine_similarity(query_vec, self.doc_matrix, dense_output=False).toarray().flatten()
            
            if similarities.size == 0:
                return self._keyword_search(query, top_k)
            
            # Balanced thresholds for comprehensive results
            threshold = 0.02  # Reasonable base threshold
            relevant_indices = [(i, similarities[i]) for i in range(len(similarities)) 
                               if similarities[i] > threshold]
            
            # If we don't get enough results, lower threshold
            if len(relevant_indices) < 3:
                threshold = 0.01
                relevant_indices = [(i, similarities[i]) for i in range(len(similarities)) 
                                   if similarities[i] > threshold]
                                   
            if len(relevant_indices) < 1:
                threshold = 0.005
                relevant_indices = [(i, similarities[i]) for i in range(len(similarities)) 
                                   if similarities[i] > threshold]
            
            if not relevant_indices:
                # Try keyword fallback
                return self._keyword_search(query, top_k)
            
            # Sort by similarity and take top_k
            relevant_indices.sort(key=lambda x: x[1], reverse=True)
            
            results = []
            for idx, sim in relevant_indices[:top_k]:
                results.append({
                    'filename': self.documents[idx]['filename'],
                    'content': self.documents[idx]['content'],
                    'similarity': float(sim)
                })
            
            return results
            
        except Exception:
            return self._keyword_search(query, top_k)
    
    def _keyword_search(self, query, top_k=3):
        """Fast keyword-based fallback search"""
        # Tokenize query
        tokens = [t.lower() for t in re.findall(r'\w+', query) if len(t) > 2]
        if not tokens:
            return []
        
        scores = []
        for i, doc in enumerate(self.documents):
            text = (doc.get('content') or '').lower()
            # Count occurrences
            score = sum(text.count(t) for t in tokens)
            if score > 0:
                scores.append((i, score))
        
        # Sort by score
        scores.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for idx, score in scores[:top_k]:
            results.append({
                'filename': self.documents[idx]['filename'],
                'content': self.documents[idx]['content'],
                'similarity': float(score) / 100.0  # Normalize roughly
            })
        
        return results


# Alias for backward compatibility
SearchEngine = FastSearchEngine
