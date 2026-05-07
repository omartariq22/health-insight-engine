"""
View system logs from MongoDB and local file.

Usage:
    python database/view_logs.py [--limit 50] [--level INFO] [--module agent_a]
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import argparse
from database.logger import view_recent_logs
from database.connection import get_collection, SYSTEM_LOGS_COLLECTION


def view_logs_filtered(limit: int = 50, level: str = None, module: str = None):
    """View logs with optional filters."""
    try:
        collection = get_collection(SYSTEM_LOGS_COLLECTION)
        
        # Build query filter
        query = {}
        if level:
            query["level"] = level.upper()
        if module:
            query["module"] = module
        
        # Fetch logs
        logs = collection.find(query).sort("timestamp", -1).limit(limit)
        
        print("=" * 120)
        print(f"SYSTEM LOGS (Last {limit})")
        if level:
            print(f"Filter: Level = {level.upper()}")
        if module:
            print(f"Filter: Module = {module}")
        print("=" * 120)
        
        count = 0
        for log in logs:
            timestamp = log.get("timestamp", "N/A")[:19]  # Trim milliseconds
            level_str = log.get("level", "INFO")
            module_str = log.get("module", "unknown")
            function = log.get("function", "")
            message = log.get("message", "")
            
            # Add extra fields if present
            extras = []
            if "user_id" in log:
                extras.append(f"user={log['user_id']}")
            if "anomaly_type" in log:
                extras.append(f"metric={log['anomaly_type']}")
            if "execution_time" in log:
                extras.append(f"time={log['execution_time']:.3f}s")
            
            extra_str = f" [{', '.join(extras)}]" if extras else ""
            
            print(f"{timestamp} | {level_str:8s} | {module_str:15s} | {function:20s} | {message}{extra_str}")
            count += 1
        
        if count == 0:
            print("No logs found matching the criteria.")
        
        print("=" * 120)
        print(f"Total logs displayed: {count}")
        
    except Exception as e:
        print(f"Error viewing logs: {e}")


def view_log_stats():
    """View log statistics."""
    try:
        collection = get_collection(SYSTEM_LOGS_COLLECTION)
        
        total = collection.count_documents({})
        
        # Count by level
        levels = collection.aggregate([
            {"$group": {"_id": "$level", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ])
        
        # Count by module
        modules = collection.aggregate([
            {"$group": {"_id": "$module", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ])
        
        print("=" * 70)
        print("LOG STATISTICS")
        print("=" * 70)
        print(f"Total Logs: {total}\n")
        
        print("By Level:")
        for level in levels:
            print(f"  {level['_id']:10s}: {level['count']:5d}")
        
        print("\nBy Module:")
        for module in modules:
            print(f"  {module['_id']:15s}: {module['count']:5d}")
        
        print("=" * 70)
        
    except Exception as e:
        print(f"Error viewing log stats: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="View system logs")
    parser.add_argument("--limit", type=int, default=50, help="Number of logs to display")
    parser.add_argument("--level", type=str, help="Filter by log level (DEBUG, INFO, WARNING, ERROR)")
    parser.add_argument("--module", type=str, help="Filter by module name")
    parser.add_argument("--stats", action="store_true", help="Show log statistics")
    
    args = parser.parse_args()
    
    if args.stats:
        view_log_stats()
    else:
        view_logs_filtered(args.limit, args.level, args.module)
