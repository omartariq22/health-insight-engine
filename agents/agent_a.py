"""
Agent A: The Data Analyst (Anomaly Detector)

This agent queries MongoDB for user health data and identifies engagement anomalies
by comparing recent activity (last 3 days) against a baseline (previous 7 days).

Detection Logic:
- Baseline: Average of days 8-14 from the end (7-day window)
- Recent: Average of last 3 days
- Anomaly: Recent < Baseline * 0.6 (i.e., 40%+ drop)

Metrics Tracked:
- steps (primary indicator)
- sleep_hours (secondary indicator)
- heart_rate (stress indicator - inverse: high HR = potential issue)
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
from typing import List, Optional
from datetime import datetime
from database.connection import get_collection, HEALTH_LOGS_COLLECTION, test_connection
from agents.models import AnomalyReport
from database.logger import setup_logger, log_anomaly_detection, log_mongodb_operation, log_error

# Initialize logger
logger = setup_logger("agent_a")


# ──────────────────────────────────────────────
# 1. Data Retrieval
# ──────────────────────────────────────────────

def get_user_data(user_id: str) -> pd.DataFrame:
    """
    Fetch all health logs for a specific user from MongoDB.
    
    Returns:
        DataFrame with columns: user_id, age, date, steps, sleep_hours, heart_rate
        Sorted by date ascending.
    """
    logger.debug(f"Fetching data for {user_id}")
    collection = get_collection(HEALTH_LOGS_COLLECTION)
    
    # Query MongoDB for this user's data
    cursor = collection.find({"user_id": user_id}).sort("date", 1)  # 1 = ascending
    
    # Convert to DataFrame
    data = list(cursor)
    if not data:
        logger.warning(f"No data found for {user_id}")
        return pd.DataFrame()
    
    df = pd.DataFrame(data)
    
    # Drop MongoDB's _id field
    if "_id" in df.columns:
        df = df.drop(columns=["_id"])
    
    # Ensure date is sorted
    df = df.sort_values("date").reset_index(drop=True)
    
    logger.debug(f"Retrieved {len(df)} records for {user_id}")
    return df


def get_all_users() -> List[str]:
    """
    Get a list of all unique user IDs in the database.
    
    Returns:
        List of user_id strings.
    """
    collection = get_collection(HEALTH_LOGS_COLLECTION)
    user_ids = collection.distinct("user_id")
    return sorted(user_ids)


# ──────────────────────────────────────────────
# 2. Anomaly Detection Logic
# ──────────────────────────────────────────────

def detect_anomaly_for_user(user_id: str, min_days: int = 10) -> Optional[AnomalyReport]:
    """
    Detect if a user has an engagement anomaly.
    
    Logic:
    - Baseline: Average of days 8-14 from the end (7-day window)
    - Recent: Average of last 3 days
    - Anomaly: Recent < Baseline * 0.6 (40%+ drop)
    
    Args:
        user_id: User to analyze
        min_days: Minimum days of data required (default 10 for 7-day baseline + 3-day recent)
    
    Returns:
        AnomalyReport if anomaly detected, None otherwise
    """
    df = get_user_data(user_id)
    
    # Need at least 10 days of data (7 baseline + 3 recent)
    if len(df) < min_days:
        logger.debug(f"{user_id}: Insufficient data ({len(df)} days)")
        return None
    
    # Get user age and name (same for all records)
    user_age = int(df['age'].iloc[0])
    user_name = df['user_name'].iloc[0] if 'user_name' in df.columns else user_id
    
    # Define windows
    recent_window = df.tail(3)  # Last 3 days
    baseline_window = df.iloc[-10:-3]  # Days 8-10 from end (7-day window)
    
    # Calculate averages for each metric
    metrics = ["steps", "sleep_hours", "heart_rate"]
    anomalies = []
    
    for metric in metrics:
        baseline_avg = baseline_window[metric].mean()
        recent_avg = recent_window[metric].mean()
        
        # For heart_rate, we detect INCREASES (higher is worse)
        # For steps and sleep_hours, we detect DECREASES (lower is worse)
        if metric == "heart_rate":
            # Calculate increase percentage
            increase_pct = ((recent_avg - baseline_avg) / baseline_avg) * 100
            
            # Check if increase is significant (40%+)
            if increase_pct >= 40:
                # Determine severity
                severity = "severe" if increase_pct >= 60 else "moderate"
                
                # Create anomaly report
                report = AnomalyReport(
                    user_id=user_id,
                    user_name=user_name,
                    age=user_age,
                    metric=metric,
                    baseline_avg=round(baseline_avg, 1),
                    baseline_period=f"{baseline_window['date'].iloc[0]} to {baseline_window['date'].iloc[-1]}",
                    recent_avg=round(recent_avg, 1),
                    recent_period=f"{recent_window['date'].iloc[0]} to {recent_window['date'].iloc[-1]}",
                    drop_percentage=round(increase_pct, 1),  # Using same field for consistency
                    severity=severity,
                )
                
                # Log the anomaly detection
                log_anomaly_detection(logger, user_id, metric, increase_pct, severity)
                
                anomalies.append((increase_pct, report))
        else:
            # Calculate drop percentage for steps and sleep_hours
            drop_pct = ((baseline_avg - recent_avg) / baseline_avg) * 100
            
            # Check if drop is significant (40%+)
            if drop_pct >= 40:
                # Determine severity
                severity = "severe" if drop_pct >= 60 else "moderate"
                
                # Create anomaly report
                report = AnomalyReport(
                    user_id=user_id,
                    user_name=user_name,
                    age=user_age,
                    metric=metric,
                    baseline_avg=round(baseline_avg, 1),
                    baseline_period=f"{baseline_window['date'].iloc[0]} to {baseline_window['date'].iloc[-1]}",
                    recent_avg=round(recent_avg, 1),
                    recent_period=f"{recent_window['date'].iloc[0]} to {recent_window['date'].iloc[-1]}",
                    drop_percentage=round(drop_pct, 1),
                    severity=severity,
                )
                
                # Log the anomaly detection
                log_anomaly_detection(logger, user_id, metric, drop_pct, severity)
                
                anomalies.append((drop_pct, report))
    
    # Return the most severe anomaly (highest drop percentage)
    if anomalies:
        anomalies.sort(key=lambda x: x[0], reverse=True)
        return anomalies[0][1]  # Return the AnomalyReport
    
    return None


def detect_all_anomalies() -> List[AnomalyReport]:
    """
    Scan all users and detect anomalies.
    
    Returns:
        List of AnomalyReport objects for users with detected anomalies.
    """
    users = get_all_users()
    anomalies = []
    
    print(f"Scanning {len(users)} users for anomalies...")
    
    for user_id in users:
        report = detect_anomaly_for_user(user_id)
        if report:
            anomalies.append(report)
            print(f"  [ANOMALY] {report.to_summary()}")
        else:
            print(f"  [OK] {user_id}: No anomalies detected")
    
    return anomalies


# ──────────────────────────────────────────────
# 3. Reporting & Output
# ──────────────────────────────────────────────

def print_anomaly_report(anomalies: List[AnomalyReport]):
    """Print a formatted summary of all detected anomalies."""
    if not anomalies:
        print("\n[OK] No anomalies detected. All users have normal engagement patterns.")
        return
    
    print(f"\n{'='*70}")
    print(f"ANOMALY DETECTION REPORT")
    print(f"{'='*70}")
    print(f"Total Users Scanned: {len(get_all_users())}")
    print(f"Anomalies Detected: {len(anomalies)}")
    print(f"Detection Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")
    
    for i, report in enumerate(anomalies, 1):
        print(f"{i}. {report.user_id} (age {report.age})")
        print(f"   Metric:       {report.metric}")
        print(f"   Drop:         {report.drop_percentage:.1f}% ({report.severity.upper()})")
        print(f"   Baseline:     {report.baseline_avg:.1f} ({report.baseline_period})")
        print(f"   Recent:       {report.recent_avg:.1f} ({report.recent_period})")
        print()


def save_anomalies_to_file(anomalies: List[AnomalyReport], output_path: str = "agents/anomalies.json"):
    """Save detected anomalies to a JSON file for later use."""
    import json
    
    data = {
        "detection_time": datetime.now().isoformat(),
        "total_users": len(get_all_users()),
        "anomalies_detected": len(anomalies),
        "anomalies": [report.to_dict() for report in anomalies]
    }
    
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"[OK] Anomalies saved to {output_path}")


# ──────────────────────────────────────────────
# Main Execution
# ──────────────────────────────────────────────

def run_agent_a():
    """Run Agent A: Detect all anomalies and generate reports."""
    print("=" * 70)
    print("AGENT A: Data Analyst (Anomaly Detector)")
    print("=" * 70)
    
    logger.info("Agent A started")
    
    # Step 1: Test connection
    print("\n1. Testing MongoDB connection...")
    result = test_connection()
    if result["status"] != "connected":
        print(f"  [FAIL] {result['error']}")
        logger.error(f"MongoDB connection failed: {result['error']}")
        sys.exit(1)
    print(f"  [OK] Connected to MongoDB")
    logger.info("MongoDB connection successful")
    
    # Step 2: Detect anomalies
    print("\n2. Detecting anomalies...")
    anomalies = detect_all_anomalies()
    
    # Step 3: Print report
    print_anomaly_report(anomalies)
    
    # Step 4: Save to file
    if anomalies:
        save_anomalies_to_file(anomalies)
        logger.info(f"Agent A complete: {len(anomalies)} anomalies detected and saved")
    else:
        logger.info("Agent A complete: No anomalies detected")
    
    print(f"\n{'='*70}")
    print(f"[OK] Agent A complete: {len(anomalies)} anomalies detected")
    print(f"{'='*70}\n")
    
    return anomalies


if __name__ == "__main__":
    run_agent_a()
