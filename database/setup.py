"""
MongoDB database setup script for Healthmov Insight Engine.

Creates the required collections with schema validation and indexes.
Run this once after setting up your MongoDB Atlas cluster.

Usage:
    python database/setup.py
"""

from connection import (
    get_database,
    test_connection,
    close_connection,
    HEALTH_LOGS_COLLECTION,
    HEALTH_ADVICE_COLLECTION,
)


def create_collections(db):
    """Create the required collections with schema validation."""
    existing = db.list_collection_names()

    # --- Collection 1: health_logs ---
    if HEALTH_LOGS_COLLECTION not in existing:
        db.create_collection(
            HEALTH_LOGS_COLLECTION,
            validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["user_id", "age", "date", "steps", "sleep_hours", "heart_rate"],
                    "properties": {
                        "user_id": {"bsonType": "string", "description": "Unique user identifier"},
                        "age": {"bsonType": "int", "description": "User age in years"},
                        "date": {"bsonType": "string", "description": "Date in YYYY-MM-DD format"},
                        "steps": {"bsonType": "int", "description": "Daily step count"},
                        "sleep_hours": {"bsonType": "double", "description": "Hours of sleep"},
                        "heart_rate": {"bsonType": "int", "description": "Average heart rate in bpm"},
                    },
                }
            },
        )
        print(f"  [OK] Created collection: {HEALTH_LOGS_COLLECTION}")
    else:
        print(f"  [SKIP] Collection already exists: {HEALTH_LOGS_COLLECTION}")

    # --- Collection 2: health_advice ---
    if HEALTH_ADVICE_COLLECTION not in existing:
        db.create_collection(
            HEALTH_ADVICE_COLLECTION,
            validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["user_id", "anomaly_report", "recommendation", "created_at"],
                    "properties": {
                        "user_id": {"bsonType": "string", "description": "User this advice is for"},
                        "anomaly_report": {"bsonType": "object", "description": "Anomaly details from Agent A"},
                        "recommendation": {"bsonType": "string", "description": "AI-generated health advice"},
                        "rag_sources": {"bsonType": "array", "description": "Knowledge base sources used"},
                        "created_at": {"bsonType": "string", "description": "ISO timestamp of generation"},
                    },
                }
            },
        )
        print(f"  [OK] Created collection: {HEALTH_ADVICE_COLLECTION}")
    else:
        print(f"  [SKIP] Collection already exists: {HEALTH_ADVICE_COLLECTION}")


def create_indexes(db):
    """Create indexes for efficient querying."""
    # health_logs: compound index on user_id + date for fast lookups
    db[HEALTH_LOGS_COLLECTION].create_index(
        [("user_id", 1), ("date", -1)],
        name="idx_user_date",
        unique=True,
    )
    print(f"  [OK] Created index: idx_user_date on {HEALTH_LOGS_COLLECTION}")

    # health_advice: index on user_id for fast recommendation lookups
    db[HEALTH_ADVICE_COLLECTION].create_index(
        [("user_id", 1), ("created_at", -1)],
        name="idx_user_advice",
    )
    print(f"  [OK] Created index: idx_user_advice on {HEALTH_ADVICE_COLLECTION}")


def setup_database():
    """Run the full database setup."""
    print("=" * 50)
    print("Healthmov Insight Engine - Database Setup")
    print("=" * 50)

    # Step 1: Test connection
    print("\n1. Testing MongoDB connection...")
    result = test_connection()
    if result["status"] != "connected":
        print(f"  [FAIL] {result['error']}")
        print("  Check your MONGODB_URI in .env and try again.")
        return False

    print(f"  [OK] Connected to MongoDB Atlas")
    print(f"  Database: {result['database']}")

    # Step 2: Create collections
    print("\n2. Creating collections...")
    db = get_database()
    create_collections(db)

    # Step 3: Create indexes
    print("\n3. Creating indexes...")
    create_indexes(db)

    # Step 4: Verify
    print("\n4. Verifying setup...")
    collections = db.list_collection_names()
    print(f"  Collections: {collections}")

    for name in [HEALTH_LOGS_COLLECTION, HEALTH_ADVICE_COLLECTION]:
        count = db[name].count_documents({})
        indexes = db[name].index_information()
        print(f"  {name}: {count} documents, {len(indexes)} indexes")

    print("\n" + "=" * 50)
    print("[OK] Database setup complete!")
    print("=" * 50)

    close_connection()
    return True


if __name__ == "__main__":
    setup_database()
