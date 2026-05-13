"""
Healthmov Insight Engine - MCP Server

This MCP server exposes the health anomaly detection and recommendation system
as a tool that external LLM interfaces (like Claude) can use.

Tool: analyze_user(user_id) - Analyzes a specific user and returns their health recommendation
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fastmcp import FastMCP
from agents.agent_a import detect_anomaly_for_user
from agents.agent_b import generate_recommendation
from database.connection import get_collection, HEALTH_ADVICE_COLLECTION, test_connection

# Initialize FastMCP server
mcp = FastMCP("Healthmov Insight Engine")


@mcp.tool()
def analyze_user(user_id: str) -> dict:
    """
    Analyze a specific user's health data and generate a personalized recommendation.
    
    This tool runs the full Healthmov pipeline for a single user:
    1. Detects if the user has any health anomalies (40%+ drops in steps, sleep, or heart rate)
    2. If an anomaly is found, generates a personalized health recommendation using RAG and LLM
    3. Returns the anomaly report and recommendation
    
    Args:
        user_id: User identifier (format: user_XXX, e.g., "user_001")
    
    Returns:
        dict: Contains anomaly_detected (bool), anomaly_report (dict or None), 
              and recommendation (str or None)
    
    Example:
        analyze_user("user_005")
        # Returns: {
        #   "anomaly_detected": True,
        #   "anomaly_report": {...},
        #   "recommendation": "Dear Jessica, I noticed..."
        # }
    """
    try:
        # Test MongoDB connection
        connection_result = test_connection()
        if connection_result["status"] != "connected":
            return {
                "error": f"MongoDB connection failed: {connection_result['error']}",
                "anomaly_detected": False,
                "anomaly_report": None,
                "recommendation": None
            }
        
        # Step 1: Run Agent A to detect anomalies for this user
        anomaly = detect_anomaly_for_user(user_id)
        
        if not anomaly:
            return {
                "anomaly_detected": False,
                "anomaly_report": None,
                "recommendation": None,
                "message": f"No anomalies detected for {user_id}. User has normal health patterns."
            }
        
        # Step 2: Run Agent B to generate recommendation
        recommendation_text = generate_recommendation(anomaly)
        
        # Step 3: Return the results
        return {
            "anomaly_detected": True,
            "anomaly_report": {
                "user_id": anomaly.user_id,
                "user_name": anomaly.user_name,
                "age": anomaly.age,
                "metric": anomaly.metric,
                "baseline_avg": anomaly.baseline_avg,
                "baseline_period": anomaly.baseline_period,
                "recent_avg": anomaly.recent_avg,
                "recent_period": anomaly.recent_period,
                "drop_percentage": anomaly.drop_percentage,
                "severity": anomaly.severity
            },
            "recommendation": recommendation_text,
            "message": f"Anomaly detected for {user_id}. Recommendation generated successfully."
        }
        
    except Exception as e:
        return {
            "error": f"Error analyzing user {user_id}: {str(e)}",
            "anomaly_detected": False,
            "anomaly_report": None,
            "recommendation": None
        }


@mcp.tool()
def get_user_recommendation(user_id: str) -> dict:
    """
    Retrieve an existing recommendation for a user from the database.
    
    This tool fetches a previously generated recommendation without running the analysis again.
    Useful for checking if a user already has a recommendation stored.
    
    Args:
        user_id: User identifier (format: user_XXX, e.g., "user_001")
    
    Returns:
        dict: Contains the stored recommendation or an error message
    """
    try:
        collection = get_collection(HEALTH_ADVICE_COLLECTION)
        recommendation = collection.find_one({"user_id": user_id}, {"_id": 0})
        
        if not recommendation:
            return {
                "found": False,
                "message": f"No recommendation found for {user_id}. User may not have any detected anomalies.",
                "recommendation": None
            }
        
        return {
            "found": True,
            "user_id": recommendation["user_id"],
            "anomaly_report": recommendation["anomaly_report"],
            "recommendation": recommendation["recommendation"],
            "rag_sources": recommendation.get("rag_sources", []),
            "created_at": recommendation.get("created_at")
        }
        
    except Exception as e:
        return {
            "error": f"Error retrieving recommendation for {user_id}: {str(e)}",
            "found": False,
            "recommendation": None
        }


@mcp.tool()
def list_users_with_anomalies() -> dict:
    """
    List all users who currently have detected anomalies and recommendations.
    
    Returns:
        dict: Contains a list of user IDs with anomalies and their basic info
    """
    try:
        collection = get_collection(HEALTH_ADVICE_COLLECTION)
        recommendations = list(collection.find({}, {"_id": 0, "user_id": 1, "anomaly_report": 1}))
        
        users = []
        for rec in recommendations:
            anomaly = rec.get("anomaly_report", {})
            users.append({
                "user_id": rec["user_id"],
                "user_name": anomaly.get("user_name", "Unknown"),
                "age": anomaly.get("age"),
                "metric": anomaly.get("metric"),
                "drop_percentage": anomaly.get("drop_percentage"),
                "severity": anomaly.get("severity")
            })
        
        return {
            "total_users_with_anomalies": len(users),
            "users": users
        }
        
    except Exception as e:
        return {
            "error": f"Error listing users: {str(e)}",
            "total_users_with_anomalies": 0,
            "users": []
        }


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
