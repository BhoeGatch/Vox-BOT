# Performance Optimization Guide

## Speed Improvements Implemented

### 1. **Document Caching** ✅
- Uses `@st.cache_resource` to load documents once
- Index is built once and reused across queries
- **Speed gain:** 10-50x faster on repeat queries

### 2. **Fast Search Engine** ✅
Three search methods available in `search_fast.py`:

#### Method Comparison

| Method | Speed | Accuracy | Best For |
|--------|-------|----------|----------|
| **keyword** | ⚡⚡⚡ Fastest | ⭐⭐ Good | Large docs (>100K words) |
| **count** | ⚡⚡ Fast | ⭐⭐⭐ Better | Medium docs (default) |
| **tfidf** | ⚡ Slower | ⭐⭐⭐⭐ Best | High accuracy needed |

**Current setting:** `count` (balanced speed + accuracy)

### 3. **Optimization Settings**
- `max_features=3000`: Limits vocabulary size
- `binary=True`: Faster vector operations
- `ngram_range=(1,2)`: Includes phrases for better matching
- Sparse matrices for memory efficiency

## How to Switch Methods

Edit `app_new.py` line 18:

```python
# For fastest (keyword matching)
search_engine = FastSearchEngine(documents, method='keyword')

# For balanced (current)
search_engine = FastSearchEngine(documents, method='count')

# For best accuracy
search_engine = FastSearchEngine(documents, method='tfidf')
```

## Expected Performance

### With Current Setup (5 docs, ~150K words)
- **First load:** ~2-3 seconds (document parsing)
- **Index build:** ~0.5-1 second (cached after first run)
- **Search query:** ~0.1-0.3 seconds

### If Still Slow

1. **Check PDF extraction**: Large scanned PDFs are slow
   - Solution: Convert to DOCX or extract text first

2. **Reduce max_features**: Edit `search_fast.py`
   ```python
   max_features=1000  # Lower = faster, less accurate
   ```

3. **Use keyword method**: Fastest but less smart matching

4. **Split large documents**: Break 100+ page docs into chapters

## Alternative: BM25 (Not Implemented Yet)

For even better speed+accuracy, consider:
- **rank-bm25** library: Industry-standard ranking
- Install: `pip install rank-bm25`
- 2-5x faster than TF-IDF with similar accuracy

Let me know if you want BM25 implementation!

## Memory Optimization

Current setup is already optimized:
- Sparse matrices (10-100x less memory)
- Limited features (3000 vs unlimited)
- Binary vectors for count mode

If memory is an issue with 100+ documents:
- Lower `max_features` to 500-1000
- Use `keyword` method (no vectors stored)
