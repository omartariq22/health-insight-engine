"""
RAG Validation Test — run a few queries to confirm retrieval quality
before connecting to Agent B.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sentence_transformers import SentenceTransformer
from database.connection import get_collection

KNOWLEDGE_BASE_COLLECTION = "health_knowledge"
model = SentenceTransformer("all-MiniLM-L6-v2")


def query_knowledge_base(query: str, top_k: int = 3):
    """Query the vector store and return top matching chunks."""
    collection = get_collection(KNOWLEDGE_BASE_COLLECTION)
    embedding = model.encode(query).tolist()

    results = collection.aggregate([
        {
            "$vectorSearch": {
                "index": "vector_index",
                "path": "embedding",
                "queryVector": embedding,
                "numCandidates": 50,
                "limit": top_k
            }
        },
        {
            "$project": {
                "title": 1,
                "category": 1,
                "text": 1,
                "score": {"$meta": "vectorSearchScore"}
            }
        }
    ])

    return list(results)


def run_validation():
    test_queries = [
        "What should I do if I stopped exercising for several days?",
        "How many hours of sleep does an adult need?",
        "What is a healthy resting heart rate?",
        "How can I get motivated to be more physically active?"
    ]

    print("=" * 60)
    print("RAG Validation Test")
    print("=" * 60)

    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 40)
        results = query_knowledge_base(query)

        if not results:
            print("  [FAIL] No results returned")
        else:
            for i, r in enumerate(results, 1):
                print(f"  {i}. [{r['category']}] {r['title']}")
                print(f"     Score: {r['score']:.4f}")
                print(f"     Text: {r['text'][:150]}...")
                print()


if __name__ == "__main__":
    run_validation()
