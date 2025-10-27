"""Test script to validate ingestion and search components"""
import os
from ingestion import load_documents
from search import SearchEngine

# Test ingestion
data_folder = 'data'
if os.path.exists(data_folder):
    docs = load_documents(data_folder)
    print(f"Loaded {len(docs)} documents:")
    for doc in docs:
        print(f"  - {doc['filename']}: {len(doc['content'])} chars")
    
    if docs:
        # Test search
        engine = SearchEngine(docs)
        test_query = "password"
        results = engine.search(test_query)
        print(f"\nSearch for '{test_query}':")
        print(f"  Found {len(results)} results")
        for r in results:
            print(f"    - {r['filename']}: similarity={r['similarity']:.3f}")
    else:
        print("No documents to search")
else:
    print(f"Data folder '{data_folder}' does not exist")
