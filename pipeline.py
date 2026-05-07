"""
Healthmov Insight Engine - Multi-Agent Pipeline

This pipeline orchestrates Agent A (Anomaly Detector) and Agent B (Health Coach)
using LangGraph to create an automated end-to-end workflow.

Pipeline Flow:
1. ingest_data → Load health data into MongoDB
2. detect_anomalies → Run Agent A to find users with health drops
3. check_anomalies → Decide if we should continue (anomalies found) or stop
4. generate_recommendations → Run Agent B to create personalized advice
5. save_results → Confirm everything is stored in MongoDB
"""

import sys
import os
import time
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END

# Import our agents and utilities
from agents.agent_a import detect_all_anomalies, save_anomalies_to_file
from agents.agent_b import generate_recommendation
from agents.models import AnomalyReport
from database.connection import test_connection, get_collection, HEALTH_LOGS_COLLECTION, HEALTH_ADVICE_COLLECTION
from data.ingest import ingest_data
from database.logger import setup_logger, log_pipeline_start, log_pipeline_complete, log_error

# Initialize logger
logger = setup_logger("pipeline")


# ──────────────────────────────────────────────
# State Definition
# ──────────────────────────────────────────────

class PipelineState(TypedDict):
    """State that flows through the pipeline."""
    step: str
    anomalies: list
    recommendations: list
    total_users: int
    status: str
    message: str


# ──────────────────────────────────────────────
# Node Functions
# ──────────────────────────────────────────────

def ingest_data_node(state: PipelineState) -> PipelineState:
    """Node 1: Ingest health data into MongoDB."""
    print("\n" + "="*70)
    print("STEP 1: INGESTING DATA")
    print("="*70)
    
    try:
        # Test connection first
        result = test_connection()
        if result["status"] != "connected":
            state["status"] = "error"
            state["message"] = f"MongoDB connection failed: {result['error']}"
            return state
        
        # Run ingestion
        ingest_data()
        
        # Count total users
        collection = get_collection(HEALTH_LOGS_COLLECTION)
        total_users = len(collection.distinct("user_id"))
        
        state["step"] = "ingest_data"
        state["total_users"] = total_users
        state["status"] = "success"
        state["message"] = f"Successfully ingested data for {total_users} users"
        
        print(f"✓ Data ingestion complete: {total_users} users loaded")
        
    except Exception as e:
        state["status"] = "error"
        state["message"] = f"Data ingestion failed: {str(e)}"
        print(f"✗ Error: {str(e)}")
    
    return state


def detect_anomalies_node(state: PipelineState) -> PipelineState:
    """Node 2: Run Agent A to detect anomalies."""
    print("\n" + "="*70)
    print("STEP 2: DETECTING ANOMALIES (AGENT A)")
    print("="*70)
    
    try:
        # Run Agent A
        anomalies = detect_all_anomalies()
        
        # Save to file for Agent B
        if anomalies:
            save_anomalies_to_file(anomalies)
        
        state["step"] = "detect_anomalies"
        state["anomalies"] = anomalies
        state["status"] = "success"
        state["message"] = f"Detected {len(anomalies)} anomalies out of {state['total_users']} users"
        
        print(f"\n✓ Agent A complete: {len(anomalies)} anomalies detected")
        
    except Exception as e:
        state["status"] = "error"
        state["message"] = f"Anomaly detection failed: {str(e)}"
        print(f"✗ Error: {str(e)}")
    
    return state


def check_anomalies_node(state: PipelineState) -> PipelineState:
    """Node 3: Check if anomalies were found (decision point)."""
    print("\n" + "="*70)
    print("STEP 3: CHECKING ANOMALIES")
    print("="*70)
    
    anomaly_count = len(state.get("anomalies", []))
    
    if anomaly_count > 0:
        state["step"] = "check_anomalies"
        state["status"] = "continue"
        state["message"] = f"Found {anomaly_count} anomalies - proceeding to generate recommendations"
        print(f"✓ {anomaly_count} anomalies found - continuing to Agent B")
    else:
        state["step"] = "check_anomalies"
        state["status"] = "stop"
        state["message"] = "No anomalies detected - pipeline complete"
        print("✓ No anomalies detected - pipeline will stop")
    
    return state


def generate_recommendations_node(state: PipelineState) -> PipelineState:
    """Node 4: Run Agent B to generate personalized recommendations."""
    print("\n" + "="*70)
    print("STEP 4: GENERATING RECOMMENDATIONS (AGENT B)")
    print("="*70)
    
    try:
        recommendations = []
        
        for anomaly in state["anomalies"]:
            # Convert dict to AnomalyReport if needed
            if isinstance(anomaly, dict):
                anomaly = AnomalyReport(
                    user_id=anomaly["user_id"],
                    age=anomaly["age"],
                    metric=anomaly["metric"],
                    baseline_avg=anomaly["baseline_avg"],
                    baseline_period=anomaly["baseline_period"],
                    recent_avg=anomaly["recent_avg"],
                    recent_period=anomaly["recent_period"],
                    drop_percentage=anomaly["drop_percentage"],
                    severity=anomaly["severity"]
                )
            
            # Generate recommendation
            recommendation = generate_recommendation(anomaly)
            recommendations.append({
                "user_id": anomaly.user_id,
                "recommendation": recommendation
            })
        
        state["step"] = "generate_recommendations"
        state["recommendations"] = recommendations
        state["status"] = "success"
        state["message"] = f"Generated {len(recommendations)} personalized recommendations"
        
        print(f"\n✓ Agent B complete: {len(recommendations)} recommendations generated")
        
    except Exception as e:
        state["status"] = "error"
        state["message"] = f"Recommendation generation failed: {str(e)}"
        print(f"✗ Error: {str(e)}")
    
    return state


def save_results_node(state: PipelineState) -> PipelineState:
    """Node 5: Confirm results are saved in MongoDB."""
    print("\n" + "="*70)
    print("STEP 5: VERIFYING RESULTS")
    print("="*70)
    
    try:
        # Verify recommendations in MongoDB
        collection = get_collection(HEALTH_ADVICE_COLLECTION)
        saved_count = collection.count_documents({})
        
        state["step"] = "save_results"
        state["status"] = "complete"
        state["message"] = f"Pipeline complete: {saved_count} recommendations saved to MongoDB"
        
        print(f"✓ Verified: {saved_count} recommendations in MongoDB")
        print(f"✓ Pipeline execution successful!")
        
    except Exception as e:
        state["status"] = "error"
        state["message"] = f"Result verification failed: {str(e)}"
        print(f"✗ Error: {str(e)}")
    
    return state


# ──────────────────────────────────────────────
# Conditional Edge Function
# ──────────────────────────────────────────────

def should_continue(state: PipelineState) -> Literal["generate_recommendations", "end"]:
    """Decide whether to continue to Agent B or stop."""
    if state.get("status") == "continue":
        return "generate_recommendations"
    else:
        return "end"


# ──────────────────────────────────────────────
# Build the Graph
# ──────────────────────────────────────────────

def build_pipeline() -> StateGraph:
    """Build the LangGraph pipeline."""
    
    # Create the graph
    workflow = StateGraph(PipelineState)
    
    # Add nodes
    workflow.add_node("ingest_data", ingest_data_node)
    workflow.add_node("detect_anomalies", detect_anomalies_node)
    workflow.add_node("check_anomalies", check_anomalies_node)
    workflow.add_node("generate_recommendations", generate_recommendations_node)
    workflow.add_node("save_results", save_results_node)
    
    # Add edges
    workflow.add_edge("ingest_data", "detect_anomalies")
    workflow.add_edge("detect_anomalies", "check_anomalies")
    
    # Conditional edge: continue to Agent B or stop
    workflow.add_conditional_edges(
        "check_anomalies",
        should_continue,
        {
            "generate_recommendations": "generate_recommendations",
            "end": END
        }
    )
    
    workflow.add_edge("generate_recommendations", "save_results")
    workflow.add_edge("save_results", END)
    
    # Set entry point
    workflow.set_entry_point("ingest_data")
    
    return workflow.compile()


# ──────────────────────────────────────────────
# Main Execution
# ──────────────────────────────────────────────

def run_pipeline():
    """Run the complete multi-agent pipeline."""
    print("\n" + "="*70)
    print("HEALTHMOV INSIGHT ENGINE - MULTI-AGENT PIPELINE")
    print("="*70)
    print("\nPipeline Flow:")
    print("  1. Ingest Data -> Load health data into MongoDB")
    print("  2. Detect Anomalies -> Run Agent A")
    print("  3. Check Anomalies -> Decision point")
    print("  4. Generate Recommendations -> Run Agent B (if anomalies found)")
    print("  5. Save Results -> Verify MongoDB storage")
    print("\nStarting pipeline execution...\n")
    
    # Log pipeline start
    log_pipeline_start(logger, "Healthmov Multi-Agent Pipeline")
    start_time = time.time()
    
    try:
        # Build and run the pipeline
        pipeline = build_pipeline()
        
        # Initialize state
        initial_state = PipelineState(
            step="start",
            anomalies=[],
            recommendations=[],
            total_users=0,
            status="running",
            message="Pipeline started"
        )
        
        # Execute the pipeline
        final_state = pipeline.invoke(initial_state)
        
        # Calculate total execution time
        total_time = time.time() - start_time
        
        # Log pipeline completion
        log_pipeline_complete(
            logger,
            "Healthmov Multi-Agent Pipeline",
            total_time,
            len(final_state['anomalies']),
            len(final_state['recommendations'])
        )
        
        # Print final summary
        print("\n" + "="*70)
        print("PIPELINE EXECUTION SUMMARY")
        print("="*70)
        print(f"Status: {final_state['status'].upper()}")
        print(f"Total Users: {final_state['total_users']}")
        print(f"Anomalies Detected: {len(final_state['anomalies'])}")
        print(f"Recommendations Generated: {len(final_state['recommendations'])}")
        print(f"Execution Time: {total_time:.2f}s")
        print(f"Message: {final_state['message']}")
        print("="*70 + "\n")
        
        return final_state
        
    except Exception as e:
        log_error(logger, e, "Pipeline execution")
        raise


if __name__ == "__main__":
    run_pipeline()
