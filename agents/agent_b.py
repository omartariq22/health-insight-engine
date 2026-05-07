"""
Agent B: The Health Coach

Receives anomaly reports from Agent A, queries the RAG knowledge base
for relevant health advice, and generates personalized recommendations
using a local LLM (Ollama llama3.2).
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
import requests
import time
from datetime import datetime
from database.connection import get_collection, HEALTH_ADVICE_COLLECTION
from agents.models import AnomalyReport, HealthRecommendation
from sentence_transformers import SentenceTransformer
from database.logger import setup_logger, log_rag_query, log_recommendation_generated, log_error

# Initialize logger
logger = setup_logger("agent_b")

KNOWLEDGE_BASE_COLLECTION = "health_knowledge"
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2"

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


# ──────────────────────────────────────────────
# 1. Query RAG Knowledge Base
# ──────────────────────────────────────────────

def build_rag_query(anomaly: AnomalyReport) -> str:
    """Build a search query based on the anomaly."""
    if anomaly.metric == "steps":
        return "how to get motivated to exercise after a period of inactivity and low physical activity"
    elif anomaly.metric == "sleep_hours":
        return "how to improve sleep quality and duration for better health"
    elif anomaly.metric == "heart_rate":
        return "elevated resting heart rate causes and how to reduce it through lifestyle changes"
    return "general health and wellness improvement tips"


def query_knowledge_base(query: str, top_k: int = 3) -> list:
    """Query MongoDB vector search for relevant health knowledge."""
    logger.debug(f"Querying RAG knowledge base: '{query}'")
    start_time = time.time()
    
    collection = get_collection(KNOWLEDGE_BASE_COLLECTION)
    
    embedding = embedding_model.encode(query).tolist()
    
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
                "source_url": 1,
                "score": {"$meta": "vectorSearchScore"}
            }
        }
    ])
    
    results_list = list(results)
    execution_time = time.time() - start_time
    
    # Log the RAG query
    log_rag_query(logger, query, len(results_list), execution_time)
    
    return results_list


# ──────────────────────────────────────────────
# 2. Generate Recommendation with Ollama
# ──────────────────────────────────────────────

def build_prompt(anomaly: AnomalyReport, rag_chunks: list) -> str:
    """Build the prompt for the LLM."""
    rag_context = "\n\n".join([
        f"Source: {chunk['title']}\n{chunk['text']}"
        for chunk in rag_chunks
    ])
    
    metric_label = {
        "steps": "daily steps",
        "sleep_hours": "sleep duration",
        "heart_rate": "resting heart rate"
    }.get(anomaly.metric, anomaly.metric)
    
    prompt = f"""You are a compassionate and motivational health coach working for Healthmov, a health and wellness app.

A user named {anomaly.user_id} has shown a concerning drop in their health activity that suggests they may be disengaging from their wellness journey.

USER SITUATION:
- Metric affected: {metric_label}
- Previous average: {anomaly.baseline_avg} ({anomaly.baseline_period})
- Recent average: {anomaly.recent_avg} ({anomaly.recent_period})
- Drop: {anomaly.drop_percentage:.1f}% ({anomaly.severity} level)

RELEVANT HEALTH KNOWLEDGE:
{rag_context}

YOUR TASK:
Write a warm, personalized, and motivational health recommendation for {anomaly.user_id}. 

- Address them directly and acknowledge their situation
- Reference their specific metric and the drop you observed
- Use the health knowledge provided to give scientifically-backed advice
- Keep it concise (3-4 paragraphs)
- End with an encouraging call to action
- Do NOT be generic — make it feel like it was written specifically for this person

RECOMMENDATION:"""
    
    return prompt


def call_ollama(prompt: str) -> str:
    """Call the local Ollama LLM and return the response."""
    logger.debug("Calling Ollama LLM")
    start_time = time.time()
    
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        
        result = response.json()["response"].strip()
        execution_time = time.time() - start_time
        
        logger.debug(f"Ollama response received ({len(result)} chars in {execution_time:.2f}s)")
        return result
        
    except Exception as e:
        log_error(logger, e, "Ollama LLM call")
        raise


# ──────────────────────────────────────────────
# 3. Save to MongoDB
# ──────────────────────────────────────────────

def save_recommendation(anomaly: AnomalyReport, recommendation: str, rag_sources: list):
    """Save the recommendation to MongoDB health_advice collection."""
    collection = get_collection(HEALTH_ADVICE_COLLECTION)
    
    # Remove existing recommendation for this user
    collection.delete_many({"user_id": anomaly.user_id})
    
    doc = {
        "user_id": anomaly.user_id,
        "anomaly_report": anomaly.to_dict(),
        "recommendation": recommendation,
        "rag_sources": [chunk.get("title", "") for chunk in rag_sources],
        "created_at": datetime.now().isoformat()
    }
    
    collection.insert_one(doc)
    print(f"  [OK] Recommendation saved to MongoDB for {anomaly.user_id}")


# ──────────────────────────────────────────────
# 4. Main Agent B Function
# ──────────────────────────────────────────────

def generate_recommendation(anomaly: AnomalyReport) -> str:
    """Full pipeline: RAG query → LLM generation → save to MongoDB."""
    print(f"\n  Processing {anomaly.user_id} ({anomaly.metric}, {anomaly.drop_percentage:.1f}% drop)")
    logger.info(f"Processing recommendation for {anomaly.user_id}")
    
    start_time = time.time()
    
    try:
        # Step 1: Query RAG
        query = build_rag_query(anomaly)
        rag_chunks = query_knowledge_base(query)
        print(f"  [OK] Retrieved {len(rag_chunks)} RAG chunks")
        
        # Step 2: Build prompt and call LLM
        prompt = build_prompt(anomaly, rag_chunks)
        print(f"  Generating recommendation with Ollama...")
        recommendation = call_ollama(prompt)
        print(f"  [OK] Recommendation generated ({len(recommendation)} chars)")
        
        # Step 3: Save to MongoDB
        save_recommendation(anomaly, recommendation, rag_chunks)
        
        execution_time = time.time() - start_time
        
        # Log the recommendation generation
        log_recommendation_generated(logger, anomaly.user_id, len(recommendation), execution_time)
        
        return recommendation
        
    except Exception as e:
        log_error(logger, e, f"generate_recommendation for {anomaly.user_id}")
        raise


def run_agent_b():
    """Run Agent B on all anomalies detected by Agent A."""
    print("=" * 70)
    print("AGENT B: Health Coach (Recommendation Generator)")
    print("=" * 70)
    
    logger.info("Agent B started")
    
    # Load anomalies from Agent A output
    anomalies_path = os.path.join(os.path.dirname(__file__), "anomalies.json")
    if not os.path.exists(anomalies_path):
        print("[FAIL] anomalies.json not found. Run Agent A first.")
        logger.error("anomalies.json not found")
        sys.exit(1)
    
    with open(anomalies_path, "r") as f:
        data = json.load(f)
    
    anomalies_data = data.get("anomalies", [])
    print(f"\nLoaded {len(anomalies_data)} anomalies from Agent A")
    logger.info(f"Loaded {len(anomalies_data)} anomalies from Agent A")
    
    if not anomalies_data:
        print("No anomalies to process.")
        logger.info("No anomalies to process")
        return
    
    # Process each anomaly
    print("\nGenerating recommendations...")
    results = []
    
    for anomaly_dict in anomalies_data:
        anomaly = AnomalyReport(
            user_id=anomaly_dict["user_id"],
            age=anomaly_dict["age"],
            metric=anomaly_dict["metric"],
            baseline_avg=anomaly_dict["baseline_avg"],
            baseline_period=anomaly_dict["baseline_period"],
            recent_avg=anomaly_dict["recent_avg"],
            recent_period=anomaly_dict["recent_period"],
            drop_percentage=anomaly_dict["drop_percentage"],
            severity=anomaly_dict["severity"]
        )
        
        recommendation = generate_recommendation(anomaly)
        results.append({
            "user_id": anomaly.user_id,
            "recommendation": recommendation
        })
    
    # Print summary
    print(f"\n{'='*70}")
    print(f"AGENT B COMPLETE: {len(results)} recommendations generated")
    print(f"{'='*70}\n")
    
    logger.info(f"Agent B complete: {len(results)} recommendations generated")
    
    for result in results:
        print(f"User: {result['user_id']}")
        print(f"Recommendation preview: {result['recommendation'][:200]}...")
        print()
    
    return results


if __name__ == "__main__":
    run_agent_b()
