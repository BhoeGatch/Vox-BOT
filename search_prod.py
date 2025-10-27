"""Production-ready search engine with enhanced performance and reliability"""
import time
import re
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from config import config
from production_logger import get_logger, log_search_query
from validation import validate_query, ValidationError
from exception_handler import handle_exceptions, retry_on_failure, SearchError, search_circuit_breaker

logger = get_logger('search_engine')

class FastSearchEngine:
    """Production-ready search engine with comprehensive error handling and monitoring"""
    
    def __init__(self, documents: List[Dict[str, Any]], method: str = 'tfidf'):
        """
        Initialize search engine with production features
        
        Args:
            documents: List of document dictionaries
            method: Search method ('tfidf', 'count', or 'keyword')
        """
        self.documents = documents or []
        self.method = method
        self.vectorizer = None
        self.doc_matrix = None
        self.performance_stats = {
            'total_searches': 0,
            'avg_search_time': 0.0,
            'cache_hits': 0,
            'failed_searches': 0
        }
        
        # Simple query cache for performance
        self._query_cache: Dict[str, Tuple[List[Dict], float]] = {}
        self._cache_max_size = 100
        
        logger.info(f"Initializing search engine with {len(self.documents)} documents using {method} method")
        self._initialize_search_engine()
    
    @handle_exceptions("initialize_search_engine", default_return=None)
    def _initialize_search_engine(self):
        """Initialize the search engine with error handling"""
        if not self.documents:
            logger.warning("No documents provided for search engine initialization")
            return
        
        start_time = time.time()
        
        try:
            # Extract corpus with content validation
            corpus = []
            valid_docs = []
            
            for doc in self.documents:
                content = doc.get('content', '')
                if content and isinstance(content, str) and content.strip():
                    # Security: limit content length per document
                    if len(content) > 1000000:  # 1MB per document
                        content = content[:1000000]
                        logger.warning(f"Content truncated for document {doc.get('filename', 'unknown')}")
                    
                    corpus.append(content)
                    valid_docs.append(doc)
                else:
                    logger.warning(f"Skipping document with empty content: {doc.get('filename', 'unknown')}")
            
            self.documents = valid_docs
            
            if not corpus:
                logger.warning("No valid content found in documents")
                return
            
            # Initialize vectorizer based on method
            if self.method == 'tfidf':
                self._initialize_tfidf(corpus)
            elif self.method == 'count':
                self._initialize_count(corpus)
            elif self.method == 'keyword':
                logger.info("Using keyword-only search method")
                return
            else:
                logger.warning(f"Unknown search method: {self.method}, falling back to keyword search")
                self.method = 'keyword'
                return
            
            initialization_time = time.time() - start_time
            logger.info(f"Search engine initialized successfully in {initialization_time:.2f}s", extra={
                'method': self.method,
                'document_count': len(self.documents),
                'vocabulary_size': len(self.vectorizer.vocabulary_) if self.vectorizer else 0,
                'matrix_shape': self.doc_matrix.shape if self.doc_matrix is not None else None
            })
            
        except Exception as e:
            logger.error(f"Search engine initialization failed: {e}")
            # Fallback to keyword search
            self.method = 'keyword'
            self.vectorizer = None
            self.doc_matrix = None
    
    def _initialize_tfidf(self, corpus: List[str]):
        """Initialize TF-IDF vectorizer with optimized parameters"""
        try:
            self.vectorizer = TfidfVectorizer(
                stop_words='english',
                max_features=min(8000, len(corpus) * 100),  # Scale with corpus size
                ngram_range=(1, 2),  # Unigrams and bigrams
                min_df=max(1, len(corpus) // 100),  # Scale minimum document frequency
                max_df=min(0.75, 1.0 - (10 / len(corpus))),  # Scale maximum document frequency
                sublinear_tf=True,  # Use sublinear term frequency scaling
                use_idf=True,
                norm='l2',
                token_pattern=r'\b[a-zA-Z][a-zA-Z]+\b',  # Only alphabetic tokens
                lowercase=True,
                strip_accents='unicode'
            )
            
            self.doc_matrix = self.vectorizer.fit_transform(corpus)
            logger.info(f"TF-IDF matrix created: {self.doc_matrix.shape}")
            
        except ValueError as e:
            if "empty vocabulary" in str(e).lower():
                logger.warning("Empty vocabulary after TF-IDF processing, falling back to keyword search")
                self.method = 'keyword'
                self.vectorizer = None
                self.doc_matrix = None
            else:
                raise SearchError(f"TF-IDF initialization failed: {e}")
    
    def _initialize_count(self, corpus: List[str]):
        """Initialize Count vectorizer for simpler, faster searches"""
        try:
            self.vectorizer = CountVectorizer(
                stop_words='english',
                max_features=min(3000, len(corpus) * 50),
                binary=True,  # Binary occurrence for speed
                token_pattern=r'\b[a-zA-Z][a-zA-Z]+\b',
                lowercase=True,
                strip_accents='unicode'
            )
            
            self.doc_matrix = self.vectorizer.fit_transform(corpus)
            logger.info(f"Count matrix created: {self.doc_matrix.shape}")
            
        except ValueError as e:
            if "empty vocabulary" in str(e).lower():
                logger.warning("Empty vocabulary after Count processing, falling back to keyword search")
                self.method = 'keyword'
                self.vectorizer = None
                self.doc_matrix = None
            else:
                raise SearchError(f"Count vectorizer initialization failed: {e}")
    
    @handle_exceptions("search", default_return=[])
    def search(self, query: str, top_k: int = 3, session_id: str = None) -> List[Dict[str, Any]]:
        """
        Search for relevant documents with comprehensive error handling
        
        Args:
            query: Search query string
            top_k: Number of results to return
            session_id: Optional session identifier for logging
            
        Returns:
            List of search results with metadata
        """
        start_time = time.time()
        self.performance_stats['total_searches'] += 1
        
        try:
            # Validate inputs
            if not query or not isinstance(query, str):
                raise ValidationError("Query must be a non-empty string")
            
            # Validate and sanitize query
            try:
                validated_query = validate_query(query.strip())
            except ValidationError as e:
                logger.warning(f"Query validation failed: {e}")
                self.performance_stats['failed_searches'] += 1
                return []
            
            if not self.documents:
                logger.warning("No documents available for search")
                return []
            
            # Clamp top_k to reasonable bounds
            top_k = max(1, min(top_k, config.SEARCH_MAX_RESULTS, len(self.documents)))
            
            # Check cache first
            cache_key = f"{self.method}:{validated_query}:{top_k}"
            if cache_key in self._query_cache:
                results, _ = self._query_cache[cache_key]
                self.performance_stats['cache_hits'] += 1
                
                search_time = time.time() - start_time
                logger.info(f"Cache hit for query: '{validated_query[:50]}...'", extra={
                    'query_length': len(validated_query),
                    'results_count': len(results),
                    'search_time': search_time,
                    'session_id': session_id
                })
                
                return results[:top_k]  # Ensure we return correct number
            
            # Perform search based on method
            results = []
            
            if self.method in ['tfidf', 'count'] and self.vectorizer and self.doc_matrix is not None:
                results = search_circuit_breaker.call(self._vector_search, validated_query, top_k)
            else:
                results = self._keyword_search(validated_query, top_k)
            
            search_time = time.time() - start_time
            
            # Update performance statistics
            self._update_performance_stats(search_time)
            
            # Cache results (with size limit)
            if len(self._query_cache) >= self._cache_max_size:
                # Remove oldest entries (simple FIFO)
                oldest_keys = list(self._query_cache.keys())[:self._cache_max_size // 4]
                for key in oldest_keys:
                    del self._query_cache[key]
            
            self._query_cache[cache_key] = (results, search_time)
            
            # Log search performance
            log_search_query(
                query=validated_query,
                results_count=len(results),
                search_time=search_time,
                session_id=session_id
            )
            
            logger.info(f"Search completed for '{validated_query[:50]}...'", extra={
                'method': self.method,
                'query_length': len(validated_query),
                'results_count': len(results),
                'search_time': search_time,
                'session_id': session_id
            })
            
            return results
            
        except Exception as e:
            search_time = time.time() - start_time
            self.performance_stats['failed_searches'] += 1
            
            logger.error(f"Search failed after {search_time:.2f}s: {e}", extra={
                'query': query[:100] if query else 'None',
                'method': self.method,
                'session_id': session_id
            })
            
            # Try fallback to keyword search if vector search fails
            if self.method != 'keyword':
                logger.info("Attempting keyword search fallback")
                try:
                    return self._keyword_search(query, top_k)
                except Exception as fallback_error:
                    logger.error(f"Keyword search fallback also failed: {fallback_error}")
            
            return []
    
    @retry_on_failure(max_retries=2, delay=0.5)
    def _vector_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Perform vector-based search with retry logic"""
        try:
            # Transform query
            query_vec = self.vectorizer.transform([query])
            
            # Calculate similarities
            similarities = cosine_similarity(query_vec, self.doc_matrix, dense_output=False).toarray().flatten()
            
            if similarities.size == 0:
                logger.warning("Empty similarity matrix, falling back to keyword search")
                return self._keyword_search(query, top_k)
            
            # Dynamic threshold based on result quality
            thresholds = [0.02, 0.01, 0.005, 0.001]
            relevant_indices = []
            
            for threshold in thresholds:
                relevant_indices = [(i, similarities[i]) for i in range(len(similarities)) 
                                   if similarities[i] > threshold]
                
                if len(relevant_indices) >= min(2, top_k):
                    break
            
            if not relevant_indices:
                logger.info("No relevant results found with vector search, trying keyword fallback")
                return self._keyword_search(query, top_k)
            
            # Sort by similarity and take top results
            relevant_indices.sort(key=lambda x: x[1], reverse=True)
            
            results = []
            for idx, sim in relevant_indices[:top_k]:
                if idx < len(self.documents):  # Safety check
                    result = {
                        'filename': self.documents[idx].get('filename', f'Document {idx}'),
                        'content': self.documents[idx].get('content', ''),
                        'similarity': float(sim),
                        'search_method': self.method,
                        'rank': len(results) + 1
                    }
                    
                    # Add additional metadata if available
                    if 'original_filename' in self.documents[idx]:
                        result['original_filename'] = self.documents[idx]['original_filename']
                    if 'chunk_index' in self.documents[idx]:
                        result['chunk_index'] = self.documents[idx]['chunk_index']
                    
                    results.append(result)
            
            return results
            
        except Exception as e:
            raise SearchError(f"Vector search failed: {e}", query)
    
    @handle_exceptions("keyword_search", default_return=[])
    def _keyword_search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Fallback keyword-based search with enhanced scoring"""
        logger.info(f"Performing keyword search for: '{query[:50]}...'")
        
        # Tokenize and clean query
        tokens = [t.lower() for t in re.findall(r'\b[a-zA-Z]{3,}\b', query) if len(t) > 2]
        
        if not tokens:
            logger.warning("No valid tokens found in query")
            return []
        
        scores = []
        
        for i, doc in enumerate(self.documents):
            content = (doc.get('content') or '').lower()
            if not content:
                continue
            
            # Calculate various scoring metrics
            exact_matches = sum(content.count(token) for token in tokens)
            word_matches = sum(1 for token in tokens if token in content)
            
            # Position scoring (earlier mentions score higher)
            position_score = 0
            for token in tokens:
                pos = content.find(token)
                if pos >= 0:
                    position_score += max(0, 1000 - pos) / 1000
            
            # Length normalization
            content_length = len(content)
            normalized_score = exact_matches / max(1, content_length / 1000)
            
            # Combined score
            total_score = (
                exact_matches * 3 +  # Exact token matches
                word_matches * 2 +   # Unique token matches
                position_score +     # Position bonus
                normalized_score     # Length-normalized score
            )
            
            if total_score > 0:
                scores.append((i, total_score, exact_matches, word_matches))
        
        if not scores:
            logger.info("No keyword matches found")
            return []
        
        # Sort by combined score
        scores.sort(key=lambda x: (x[1], x[2], x[3]), reverse=True)
        
        results = []
        for idx, total_score, exact_matches, word_matches in scores[:top_k]:
            # Convert score to similarity-like value (0-1 range)
            max_possible_score = len(tokens) * 3 + len(tokens) * 2 + len(tokens) + 1
            similarity = min(1.0, total_score / max_possible_score)
            
            results.append({
                'filename': self.documents[idx].get('filename', f'Document {idx}'),
                'content': self.documents[idx].get('content', ''),
                'similarity': float(similarity),
                'search_method': 'keyword',
                'exact_matches': exact_matches,
                'word_matches': word_matches,
                'rank': len(results) + 1
            })
        
        logger.info(f"Keyword search found {len(results)} results")
        return results
    
    def _update_performance_stats(self, search_time: float):
        """Update performance statistics"""
        # Update average search time
        total_successful = self.performance_stats['total_searches'] - self.performance_stats['failed_searches']
        if total_successful > 0:
            current_avg = self.performance_stats['avg_search_time']
            self.performance_stats['avg_search_time'] = (
                (current_avg * (total_successful - 1) + search_time) / total_successful
            )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get search engine performance statistics"""
        cache_hit_rate = (self.performance_stats['cache_hits'] / 
                         max(1, self.performance_stats['total_searches'])) * 100
        
        error_rate = (self.performance_stats['failed_searches'] / 
                     max(1, self.performance_stats['total_searches'])) * 100
        
        return {
            **self.performance_stats,
            'cache_hit_rate_percent': round(cache_hit_rate, 2),
            'error_rate_percent': round(error_rate, 2),
            'documents_indexed': len(self.documents),
            'search_method': self.method,
            'vectorizer_ready': bool(self.vectorizer),
            'cache_size': len(self._query_cache)
        }
    
    def clear_cache(self):
        """Clear the query cache"""
        self._query_cache.clear()
        logger.info("Search cache cleared")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on search engine"""
        health_status = {
            'status': 'healthy',
            'documents_loaded': len(self.documents),
            'search_method': self.method,
            'vectorizer_initialized': bool(self.vectorizer),
            'matrix_shape': str(self.doc_matrix.shape) if self.doc_matrix is not None else None,
            'cache_size': len(self._query_cache),
            'performance_stats': self.get_performance_stats()
        }
        
        # Check for potential issues
        issues = []
        
        if not self.documents:
            issues.append("No documents loaded")
            health_status['status'] = 'degraded'
        
        if self.method in ['tfidf', 'count'] and not self.vectorizer:
            issues.append(f"Vector search method ({self.method}) selected but vectorizer not initialized")
            health_status['status'] = 'degraded'
        
        error_rate = self.performance_stats['failed_searches'] / max(1, self.performance_stats['total_searches'])
        if error_rate > 0.1:  # More than 10% error rate
            issues.append(f"High error rate: {error_rate:.2%}")
            health_status['status'] = 'degraded'
        
        if issues:
            health_status['issues'] = issues
        
        return health_status

# Alias for backward compatibility
SearchEngine = FastSearchEngine