"""
Healthmov Insight Engine - FastAPI Backend

Provides REST API endpoints for the dashboard to:
1. Get all detected anomalies
2. Get recommendations for specific users
3. Trigger the pipeline execution

Run with: uvicorn backend.main:app --reload
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

# Import our modules
from database.connection import get_collection, HEALTH_ADVICE_COLLECTION, HEALTH_LOGS_COLLECTION
from pipeline import run_pipeline
from database.logger import setup_logger

# Initialize logger
logger = setup_logger("api")

# Initialize FastAPI app
app = FastAPI(
    title="Healthmov Insight Engine API",
    description="Multi-agent system for health anomaly detection and personalized recommendations",
    version="1.0.0"
)

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variable to track pipeline status
pipeline_status = {
    "running": False,
    "last_run": None,
    "last_result": None,
    "error": None
}


# ──────────────────────────────────────────────
# Health Check Endpoint
# ──────────────────────────────────────────────

@app.get("/")
def root():
    """Root endpoint - API health check."""
    return {
        "status": "healthy",
        "service": "Healthmov Insight Engine API",
        "version": "1.0.0",
        "endpoints": {
            "anomalies": "/anomalies",
            "recommendations": "/recommendations/{user_id}",
            "run_pipeline": "/run-pipeline",
            "pipeline_status": "/pipeline-status",
            "docs": "/docs"
        }
    }


# ──────────────────────────────────────────────
# Endpoint 1: Get All Anomalies
# ──────────────────────────────────────────────

@app.get("/anomalies")
def get_anomalies():
    """
    Get all detected anomalies.
    
    Returns:
        List of anomaly reports with user_id, metric, drop_percentage, severity
    """
    try:
        logger.info("GET /anomalies - Fetching all anomalies")
        
        # Read from anomalies.json file
        anomalies_path = os.path.join(os.path.dirname(__file__), "..", "agents", "anomalies.json")
        
        if not os.path.exists(anomalies_path):
            logger.warning("anomalies.json not found")
            return {
                "total": 0,
                "anomalies": [],
                "message": "No anomalies detected yet. Run the pipeline first."
            }
        
        with open(anomalies_path, "r") as f:
            data = json.load(f)
        
        anomalies = data.get("anomalies", [])
        
        logger.info(f"Returning {len(anomalies)} anomalies")
        
        return {
            "total": len(anomalies),
            "detection_time": data.get("detection_time"),
            "total_users": data.get("total_users"),
            "anomalies": anomalies
        }
        
    except Exception as e:
        logger.error(f"Error fetching anomalies: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching anomalies: {str(e)}")


# ──────────────────────────────────────────────
# Endpoint 2: Get Recommendation for User
# ──────────────────────────────────────────────

@app.get("/recommendations/{user_id}")
def get_recommendation(user_id: str):
    """
    Get the AI-generated recommendation for a specific user.
    
    Args:
        user_id: User identifier (e.g., "user_001")
    
    Returns:
        Recommendation document with anomaly_report, recommendation text, and RAG sources
    """
    try:
        logger.info(f"GET /recommendations/{user_id} - Fetching recommendation")
        
        collection = get_collection(HEALTH_ADVICE_COLLECTION)
        
        # Find recommendation for this user
        recommendation = collection.find_one({"user_id": user_id}, {"_id": 0})
        
        if not recommendation:
            logger.warning(f"No recommendation found for {user_id}")
            raise HTTPException(
                status_code=404,
                detail=f"No recommendation found for user {user_id}. User may not have any detected anomalies."
            )
        
        logger.info(f"Returning recommendation for {user_id}")
        
        return recommendation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching recommendation for {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching recommendation: {str(e)}")


# ──────────────────────────────────────────────
# Endpoint 3: Get All Recommendations
# ──────────────────────────────────────────────

@app.get("/recommendations")
def get_all_recommendations():
    """
    Get all AI-generated recommendations.
    
    Returns:
        List of all recommendations
    """
    try:
        logger.info("GET /recommendations - Fetching all recommendations")
        
        collection = get_collection(HEALTH_ADVICE_COLLECTION)
        
        # Find all recommendations
        recommendations = list(collection.find({}, {"_id": 0}))
        
        logger.info(f"Returning {len(recommendations)} recommendations")
        
        return {
            "total": len(recommendations),
            "recommendations": recommendations
        }
        
    except Exception as e:
        logger.error(f"Error fetching recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching recommendations: {str(e)}")


# ──────────────────────────────────────────────
# Endpoint 4: Get User Health Data
# ──────────────────────────────────────────────

@app.get("/users/{user_id}/health")
def get_user_health(user_id: str, limit: Optional[int] = 30):
    """
    Get health data for a specific user.
    
    Args:
        user_id: User identifier (e.g., "user_001")
        limit: Number of recent records to return (default: 30)
    
    Returns:
        List of health records sorted by date
    """
    try:
        logger.info(f"GET /users/{user_id}/health - Fetching health data")
        
        collection = get_collection(HEALTH_LOGS_COLLECTION)
        
        # Find health records for this user
        health_data = list(
            collection.find({"user_id": user_id}, {"_id": 0})
            .sort("date", -1)
            .limit(limit)
        )
        
        if not health_data:
            raise HTTPException(
                status_code=404,
                detail=f"No health data found for user {user_id}"
            )
        
        # Reverse to get chronological order
        health_data.reverse()
        
        logger.info(f"Returning {len(health_data)} health records for {user_id}")
        
        return {
            "user_id": user_id,
            "total_records": len(health_data),
            "health_data": health_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching health data for {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching health data: {str(e)}")


# ──────────────────────────────────────────────
# Endpoint 5: Run Pipeline (Background Task)
# ──────────────────────────────────────────────

def run_pipeline_background():
    """Background task to run the pipeline."""
    global pipeline_status
    
    try:
        logger.info("Starting pipeline execution in background")
        pipeline_status["running"] = True
        pipeline_status["error"] = None
        
        # Run the pipeline
        result = run_pipeline()
        
        # Update status
        pipeline_status["running"] = False
        pipeline_status["last_run"] = datetime.now().isoformat()
        pipeline_status["last_result"] = {
            "status": result.get("status"),
            "total_users": result.get("total_users"),
            "anomalies_detected": len(result.get("anomalies", [])),
            "recommendations_generated": len(result.get("recommendations", []))
        }
        
        logger.info("Pipeline execution completed successfully")
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}")
        pipeline_status["running"] = False
        pipeline_status["error"] = str(e)


@app.post("/run-pipeline")
def trigger_pipeline(background_tasks: BackgroundTasks):
    """
    Trigger the full LangGraph pipeline execution.
    
    This runs the pipeline in the background and returns immediately.
    Use /pipeline-status to check progress.
    
    Returns:
        Status message indicating pipeline has been triggered
    """
    global pipeline_status
    
    if pipeline_status["running"]:
        raise HTTPException(
            status_code=409,
            detail="Pipeline is already running. Please wait for it to complete."
        )
    
    logger.info("POST /run-pipeline - Triggering pipeline execution")
    
    # Add pipeline execution to background tasks
    background_tasks.add_task(run_pipeline_background)
    
    return {
        "status": "started",
        "message": "Pipeline execution started in background",
        "check_status_at": "/pipeline-status"
    }


# ──────────────────────────────────────────────
# Endpoint 6: Get Pipeline Status
# ──────────────────────────────────────────────

@app.get("/pipeline-status")
def get_pipeline_status():
    """
    Get the current status of the pipeline.
    
    Returns:
        Pipeline execution status and last run results
    """
    return pipeline_status


# ──────────────────────────────────────────────
# Endpoint 7: Get Statistics
# ──────────────────────────────────────────────

@app.get("/stats")
def get_stats():
    """
    Get overall system statistics.
    
    Returns:
        Statistics about users, anomalies, and recommendations
    """
    try:
        logger.info("GET /stats - Fetching system statistics")
        
        # Get counts from MongoDB
        health_logs_count = get_collection(HEALTH_LOGS_COLLECTION).count_documents({})
        recommendations_count = get_collection(HEALTH_ADVICE_COLLECTION).count_documents({})
        
        # Get unique user count
        unique_users = len(get_collection(HEALTH_LOGS_COLLECTION).distinct("user_id"))
        
        # Get anomaly count from file
        anomalies_path = os.path.join(os.path.dirname(__file__), "..", "agents", "anomalies.json")
        anomaly_count = 0
        if os.path.exists(anomalies_path):
            with open(anomalies_path, "r") as f:
                data = json.load(f)
                anomaly_count = len(data.get("anomalies", []))
        
        return {
            "total_users": unique_users,
            "total_health_records": health_logs_count,
            "anomalies_detected": anomaly_count,
            "recommendations_generated": recommendations_count,
            "detection_rate": f"{(anomaly_count / unique_users * 100):.1f}%" if unique_users > 0 else "0%"
        }
        
    except Exception as e:
        logger.error(f"Error fetching stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")


# ──────────────────────────────────────────────
# Run the API
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 70)
    print("Healthmov Insight Engine - FastAPI Backend")
    print("=" * 70)
    print("\nStarting server...")
    print("API Documentation: http://localhost:8000/docs")
    print("API Root: http://localhost:8000")
    print("\nPress CTRL+C to stop the server")
    print("=" * 70 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
