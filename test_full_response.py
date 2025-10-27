#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(__file__))

from ingestion import load_documents
from search_fast import FastSearchEngine

# Import the response generation function
sys.path.append('.')
from app_vox import generate_comprehensive_answer

def test_full_response():
    print("Testing full response generation...")
    
    # Load documents
    data_folder = 'data'
    documents = load_documents(data_folder)
    
    if not documents:
        print("No documents found!")
        return
    
    # Create search engine
    search_engine = FastSearchEngine(documents, method='tfidf')
    
    # Test queries with full response generation
    test_queries = [
        "What services does WNS offer?",
        "Tell me about WNS technology",
        "What is customer experience management at WNS?",
        "Where does WNS operate globally?"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"QUERY: {query}")
        print('='*60)
        
        # Get search results
        results = search_engine.search(query, top_k=10)
        
        if results:
            print(f"Found {len(results)} results")
            for i, result in enumerate(results):
                sim = result.get('similarity', 0)
                print(f"  {i+1}. {result['filename']} (similarity: {sim:.4f})")
            
            # Generate response
            if results[0].get('similarity', 0) > 0.02:
                response = generate_comprehensive_answer(query, results)
                print(f"\nGENERATED RESPONSE:")
                print("-" * 40)
                print(response)
            else:
                print("\nNo strong matches found - similarity too low")
        else:
            print("No results found!")

if __name__ == "__main__":
    test_full_response()