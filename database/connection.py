"""
MongoDB connection module for Healthmov Insight Engine.

Provides a reusable database connection singleton that all other modules
will import instead of creating their own connections.
"""

import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB configuration
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "healthmov_insight")

# Singleton client instance
_client = None


def get_client():
    """Get or create the MongoDB client singleton."""
    global _client
    if _client is None:
        if not MONGODB_URI:
            raise ValueError("MONGODB_URI not found in environment variables. Check your .env file.")
        _client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    return _client


def get_database():
    """Get the main application database."""
    client = get_client()
    return client[MONGODB_DB_NAME]


def get_collection(collection_name):
    """Get a specific collection from the database."""
    db = get_database()
    return db[collection_name]


# Collection name constants — use these everywhere to avoid typos
HEALTH_LOGS_COLLECTION = "health_logs"
HEALTH_ADVICE_COLLECTION = "health_advice"


def test_connection():
    """Test the MongoDB connection and return status info."""
    try:
        client = get_client()
        # The ping command forces a round trip to the server
        client.admin.command("ping")
        db = get_database()
        collections = db.list_collection_names()
        return {
            "status": "connected",
            "database": MONGODB_DB_NAME,
            "collections": collections,
            "cluster": client.address
        }
    except ConnectionFailure as e:
        return {"status": "failed", "error": f"Connection failed: {e}"}
    except ServerSelectionTimeoutError as e:
        return {"status": "failed", "error": f"Server selection timeout: {e}"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}


def close_connection():
    """Close the MongoDB connection. Call on application shutdown."""
    global _client
    if _client is not None:
        _client.close()
        _client = None
