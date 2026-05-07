"""
Centralized Logging Module for Healthmov Insight Engine

This module provides dual logging:
1. Local file logging (logs/healthmov.log)
2. MongoDB logging (system_logs collection)

Logs every agent decision, anomaly detection, RAG query, and API call
for debugging, monitoring, and production-readiness.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import logging
from datetime import datetime
from typing import Optional, Dict, Any
from pymongo.collection import Collection

# Import MongoDB connection
from database.connection import get_collection

# Constants
LOGS_COLLECTION = "system_logs"
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "healthmov.log")


# ──────────────────────────────────────────────
# MongoDB Log Handler
# ──────────────────────────────────────────────

class MongoDBHandler(logging.Handler):
    """Custom logging handler that writes logs to MongoDB."""
    
    def __init__(self, collection: Collection):
        super().__init__()
        self.collection = collection
    
    def emit(self, record: logging.LogRecord):
        """Write log record to MongoDB."""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "level": record.levelname,
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
                "message": record.getMessage(),
                "logger_name": record.name,
            }
            
            # Add extra fields if present
            if hasattr(record, "user_id"):
                log_entry["user_id"] = record.user_id
            if hasattr(record, "anomaly_type"):
                log_entry["anomaly_type"] = record.anomaly_type
            if hasattr(record, "rag_query"):
                log_entry["rag_query"] = record.rag_query
            if hasattr(record, "execution_time"):
                log_entry["execution_time"] = record.execution_time
            
            self.collection.insert_one(log_entry)
        except Exception as e:
            # Fallback: print to console if MongoDB logging fails
            print(f"[LOGGING ERROR] Failed to write to MongoDB: {e}")


# ──────────────────────────────────────────────
# Logger Setup
# ──────────────────────────────────────────────

def setup_logger(name: str = "healthmov") -> logging.Logger:
    """
    Set up a logger with both file and MongoDB handlers.
    
    Args:
        name: Logger name (default: "healthmov")
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if logger already exists
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # Create logs directory if it doesn't exist
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # ──────────────────────────────────────────────
    # 1. File Handler (local logging)
    # ──────────────────────────────────────────────
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
    
    file_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(module)-15s | %(funcName)-20s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # ──────────────────────────────────────────────
    # 2. Console Handler (for development)
    # ──────────────────────────────────────────────
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    console_formatter = logging.Formatter(
        fmt="[%(levelname)s] %(module)s.%(funcName)s: %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # ──────────────────────────────────────────────
    # 3. MongoDB Handler (production logging)
    # ──────────────────────────────────────────────
    try:
        collection = get_collection(LOGS_COLLECTION)
        mongo_handler = MongoDBHandler(collection)
        mongo_handler.setLevel(logging.INFO)
        logger.addHandler(mongo_handler)
    except Exception as e:
        logger.warning(f"MongoDB logging disabled: {e}")
    
    return logger


# ──────────────────────────────────────────────
# Convenience Functions
# ──────────────────────────────────────────────

def log_anomaly_detection(logger: logging.Logger, user_id: str, metric: str, 
                         drop_percentage: float, severity: str):
    """Log an anomaly detection event."""
    logger.info(
        f"Anomaly detected: {user_id} - {metric} dropped {drop_percentage:.1f}% ({severity})",
        extra={
            "user_id": user_id,
            "anomaly_type": metric,
        }
    )


def log_rag_query(logger: logging.Logger, query: str, num_results: int, 
                 execution_time: Optional[float] = None):
    """Log a RAG knowledge base query."""
    msg = f"RAG query executed: '{query}' - {num_results} results"
    if execution_time:
        msg += f" ({execution_time:.3f}s)"
    
    logger.info(
        msg,
        extra={
            "rag_query": query,
            "execution_time": execution_time
        }
    )


def log_recommendation_generated(logger: logging.Logger, user_id: str, 
                                recommendation_length: int, execution_time: Optional[float] = None):
    """Log a recommendation generation event."""
    msg = f"Recommendation generated for {user_id} ({recommendation_length} chars)"
    if execution_time:
        msg += f" in {execution_time:.2f}s"
    
    logger.info(
        msg,
        extra={
            "user_id": user_id,
            "execution_time": execution_time
        }
    )


def log_mongodb_operation(logger: logging.Logger, operation: str, collection: str, 
                         count: int, execution_time: Optional[float] = None):
    """Log a MongoDB operation."""
    msg = f"MongoDB {operation}: {count} documents in '{collection}'"
    if execution_time:
        msg += f" ({execution_time:.3f}s)"
    
    logger.debug(msg)


def log_pipeline_start(logger: logging.Logger, pipeline_name: str):
    """Log pipeline execution start."""
    logger.info(f"Pipeline started: {pipeline_name}")


def log_pipeline_complete(logger: logging.Logger, pipeline_name: str, 
                         total_time: float, anomalies: int, recommendations: int):
    """Log pipeline execution completion."""
    logger.info(
        f"Pipeline complete: {pipeline_name} - {anomalies} anomalies, "
        f"{recommendations} recommendations in {total_time:.2f}s"
    )


def log_error(logger: logging.Logger, error: Exception, context: str):
    """Log an error with context."""
    logger.error(f"Error in {context}: {type(error).__name__}: {str(error)}", exc_info=True)


# ──────────────────────────────────────────────
# View Logs Utility
# ──────────────────────────────────────────────

def view_recent_logs(limit: int = 50):
    """View recent logs from MongoDB."""
    try:
        collection = get_collection(LOGS_COLLECTION)
        logs = collection.find().sort("timestamp", -1).limit(limit)
        
        print("=" * 100)
        print(f"RECENT LOGS (Last {limit})")
        print("=" * 100)
        
        for log in logs:
            timestamp = log.get("timestamp", "N/A")
            level = log.get("level", "INFO")
            module = log.get("module", "unknown")
            message = log.get("message", "")
            
            print(f"{timestamp} | {level:8s} | {module:15s} | {message}")
        
        print("=" * 100)
        
    except Exception as e:
        print(f"Error viewing logs: {e}")


# ──────────────────────────────────────────────
# Initialize Default Logger
# ──────────────────────────────────────────────

# Create default logger instance
default_logger = setup_logger()


if __name__ == "__main__":
    # Test logging
    logger = setup_logger("test")
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    # Test convenience functions
    log_anomaly_detection(logger, "user_001", "steps", 62.1, "severe")
    log_rag_query(logger, "how to improve sleep", 3, 0.125)
    log_recommendation_generated(logger, "user_001", 1500, 2.5)
    
    print(f"\nLogs written to: {LOG_FILE}")
    print("Logs also stored in MongoDB 'system_logs' collection")
    
    # View recent logs
    print("\n")
    view_recent_logs(10)
