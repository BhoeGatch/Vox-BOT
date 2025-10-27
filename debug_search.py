#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(__file__))

from ingestion import load_documents
from search_fast import FastSearchEngine

def test_search():
    print("Testing search functionality...")
    
    # Load documents
    data_folder = 'data'
    print(f"Loading documents from {data_folder}...")
    documents = load_documents(data_folder)
    
    print(f"Found {len(documents)} documents:")
    for i, doc in enumerate(documents):
        print(f"{i+1}. {doc['filename']} ({len(doc['content'])} chars)")
        print(f"   First 100 chars: {doc['content'][:100]}...")
        print()
    
    if not documents:
        print("No documents found!")
        return
    
    # Create search engine
    print("Creating search engine...")
    search_engine = FastSearchEngine(documents, method='tfidf')
    
    # Test queries
    test_queries = [
        "WNS services",
        "finance and accounting", 
        "customer experience",
        "technology innovation",
        "what does WNS do"
    ]
    
    for query in test_queries:
        print(f"\n--- Testing query: '{query}' ---")
        results = search_engine.search(query, top_k=5)
        
        if results:
            for i, result in enumerate(results):
                sim = result.get('similarity', 0)
                filename = result.get('filename', 'Unknown')
                content_preview = result.get('content', '')[:200]
                print(f"{i+1}. {filename} (similarity: {sim:.4f})")
                print(f"   Content: {content_preview}...")
                print()
        else:
            print("No results found!")

if __name__ == "__main__":
    test_search()