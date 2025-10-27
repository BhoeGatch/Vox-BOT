from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class SearchEngine:
    def __init__(self, documents):
        self.documents = documents or []
        self.vectorizer = None
        self.tfidf_matrix = None
        corpus = [doc.get('content', '') for doc in self.documents]
        try:
            if corpus and any(c.strip() for c in corpus):
                self.vectorizer = TfidfVectorizer(stop_words='english')
                self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
        except ValueError:
            # Handles empty vocabulary or all-stopwords docs
            self.vectorizer = None
            self.tfidf_matrix = None

    def search(self, query, top_k=3):
        query = (query or '').strip()
        if not query:
            return []
        # If no TF-IDF index is available, fall back to simple keyword search
        if not self.vectorizer or self.tfidf_matrix is None:
            return self._keyword_fallback(query, top_k)
        try:
            query_vec = self.vectorizer.transform([query])
            similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
            if similarities.size == 0:
                return self._keyword_fallback(query, top_k)
            # If everything is zero, try keyword fallback
            if float(similarities.max()) == 0.0:
                return self._keyword_fallback(query, top_k)
            top_indices = similarities.argsort()[-top_k:][::-1]
            results = []
            for idx in top_indices:
                results.append({
                    'filename': self.documents[idx]['filename'],
                    'content': self.documents[idx]['content'],
                    'similarity': float(similarities[idx])
                })
            return results
        except Exception:
            return self._keyword_fallback(query, top_k)

    def _keyword_fallback(self, query, top_k=3):
        # Very simple bag-of-words count fallback
        tokens = [t.lower() for t in query.split() if len(t) > 2]
        if not tokens:
            return []
        scores = []
        for i, doc in enumerate(self.documents):
            text = (doc.get('content') or '').lower()
            score = sum(text.count(t) for t in tokens)
            if score > 0:
                scores.append((i, float(score)))
        scores.sort(key=lambda x: x[1], reverse=True)
        results = []
        for idx, s in scores[:top_k]:
            results.append({
                'filename': self.documents[idx]['filename'],
                'content': self.documents[idx]['content'],
                'similarity': s
            })
        return results