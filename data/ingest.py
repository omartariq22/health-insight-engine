"""
Data Ingestion Pipeline for Healthmov Insight Engine.

Reads the generated CSV, pre-processes it using Pandas,
stores records into MongoDB, and saves a metadata summary for LLM context.

Usage:
    python data/ingest.py
"""

import sys
import os
import io

# Add project root to path so we can import the database package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
from datetime import datetime
from database.connection import (
    get_collection,
    test_connection,
    close_connection,
    HEALTH_LOGS_COLLECTION,
)


# ──────────────────────────────────────────────
# 1. Load & Validate CSV
# ──────────────────────────────────────────────

def load_csv(filepath):
    """Load the CSV file and return a Pandas DataFrame."""
    if not os.path.exists(filepath):
        print(f"  [FAIL] File not found: {filepath}")
        sys.exit(1)

    df = pd.read_csv(filepath)
    print(f"  [OK] Loaded {len(df)} records from {filepath}")
    return df


def validate_dataframe(df):
    """Validate the DataFrame structure and data quality."""
    expected_columns = ["user_id", "age", "date", "steps", "sleep_hours", "heart_rate"]
    errors = []

    # Check columns exist
    missing = [col for col in expected_columns if col not in df.columns]
    if missing:
        errors.append(f"Missing columns: {missing}")

    # Check for nulls
    null_counts = df.isnull().sum()
    if null_counts.any():
        errors.append(f"Null values found:\n{null_counts[null_counts > 0]}")

    # Check data types are reasonable
    if df["steps"].dtype not in ["int64", "int32", "float64"]:
        errors.append(f"Unexpected dtype for steps: {df['steps'].dtype}")
    if df["heart_rate"].dtype not in ["int64", "int32", "float64"]:
        errors.append(f"Unexpected dtype for heart_rate: {df['heart_rate'].dtype}")
    if df["age"].dtype not in ["int64", "int32", "float64"]:
        errors.append(f"Unexpected dtype for age: {df['age'].dtype}")

    # Check value ranges
    if (df["steps"] < 0).any():
        errors.append("Negative step counts found")
    if (df["sleep_hours"] < 0).any():
        errors.append("Negative sleep hours found")
    if (df["heart_rate"] < 30).any() or (df["heart_rate"] > 220).any():
        errors.append("Heart rate values outside realistic range (30-220 bpm)")
    if (df["age"] < 0).any() or (df["age"] > 120).any():
        errors.append("Age values outside realistic range (0-120 years)")

    if errors:
        print("  [WARN] Validation issues:")
        for err in errors:
            print(f"         - {err}")
    else:
        print("  [OK] All validation checks passed")

    return len(errors) == 0


def preprocess_dataframe(df):
    """Pre-process the DataFrame: enforce types and clean data."""
    # Ensure correct types for MongoDB compatibility
    df["steps"] = df["steps"].astype(int)
    df["heart_rate"] = df["heart_rate"].astype(int)
    df["age"] = df["age"].astype(int)
    df["sleep_hours"] = df["sleep_hours"].astype(float)
    df["user_id"] = df["user_id"].astype(str)
    df["date"] = df["date"].astype(str)

    print(f"  [OK] Pre-processed {len(df)} records (types enforced)")
    return df


# ──────────────────────────────────────────────
# 2. Print DataFrame Summary (for developer insight)
# ──────────────────────────────────────────────

def print_summary(df):
    """Print a concise summary of the DataFrame."""
    print("\n  --- DataFrame Info ---")

    # Capture df.info() output as string
    buf = io.StringIO()
    df.info(buf=buf)
    info_str = buf.getvalue()
    for line in info_str.strip().split("\n"):
        print(f"  {line}")

    print("\n  --- Descriptive Statistics ---")
    stats = df.describe().to_string()
    for line in stats.split("\n"):
        print(f"  {line}")

    print(f"\n  Unique users: {df['user_id'].nunique()}")
    print(f"  Date range:   {df['date'].min()} to {df['date'].max()}")


# ──────────────────────────────────────────────
# 3. Upload to MongoDB
# ──────────────────────────────────────────────

def upload_to_mongodb(df):
    """Insert all records into the MongoDB health_logs collection."""
    collection = get_collection(HEALTH_LOGS_COLLECTION)

    # Convert DataFrame rows to list of dicts (native Python types for MongoDB)
    records = df.to_dict(orient="records")

    # Ensure native Python types (pandas int64/float64 -> int/float)
    for record in records:
        record["steps"] = int(record["steps"])
        record["heart_rate"] = int(record["heart_rate"])
        record["age"] = int(record["age"])
        record["sleep_hours"] = float(record["sleep_hours"])

    # Clear existing data to avoid duplicates on re-run
    existing_count = collection.count_documents({})
    if existing_count > 0:
        print(f"  [INFO] Clearing {existing_count} existing records before insert...")
        collection.delete_many({})

    # Bulk insert
    result = collection.insert_many(records)
    print(f"  [OK] Inserted {len(result.inserted_ids)} records into '{HEALTH_LOGS_COLLECTION}'")

    # Verify
    final_count = collection.count_documents({})
    print(f"  [OK] Verified: {final_count} total records in collection")

    return len(result.inserted_ids)


# ──────────────────────────────────────────────
# 4. Save Enhanced Metadata for LLM Context
# ──────────────────────────────────────────────

def save_metadata(df, output_path):
    """Save an enhanced metadata summary for LLM context."""
    # Per-user stats
    user_stats = df.groupby("user_id").agg(
        age=("age", "first"),
        avg_steps=("steps", "mean"),
        avg_sleep=("sleep_hours", "mean"),
        avg_hr=("heart_rate", "mean"),
        min_steps=("steps", "min"),
        max_steps=("steps", "max"),
    ).round(1)

    metadata = f"""Dataset: Healthmov Health Logs
Ingested: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Source: data/health_logs.csv

STRUCTURE:
-----------
Total Records: {len(df)}
Total Users: {df['user_id'].nunique()}
Date Range: {df['date'].min()} to {df['date'].max()}
Days per User: {len(df) // df['user_id'].nunique()}

COLUMNS:
-----------
1. user_id (string): Unique user identifier (format: user_XXX)
2. age (integer): User age in years (18-75)
3. date (string): Date in YYYY-MM-DD format
4. steps (integer): Daily step count
5. sleep_hours (float): Hours of sleep (rounded to 1 decimal)
6. heart_rate (integer): Average heart rate in beats per minute (bpm)

GLOBAL STATISTICS:
-----------
Age:
  Mean: {df['age'].mean():.0f}
  Min:  {df['age'].min()}
  Max:  {df['age'].max()}

Steps:
  Mean: {df['steps'].mean():.0f}
  Std:  {df['steps'].std():.0f}
  Min:  {df['steps'].min()}
  Max:  {df['steps'].max()}

Sleep Hours:
  Mean: {df['sleep_hours'].mean():.1f}
  Std:  {df['sleep_hours'].std():.1f}
  Min:  {df['sleep_hours'].min()}
  Max:  {df['sleep_hours'].max()}

Heart Rate:
  Mean: {df['heart_rate'].mean():.0f}
  Std:  {df['heart_rate'].std():.0f}
  Min:  {df['heart_rate'].min()}
  Max:  {df['heart_rate'].max()}

PER-USER AVERAGES (summary):
-----------
Avg Steps Range:  {user_stats['avg_steps'].min():.0f} - {user_stats['avg_steps'].max():.0f}
Avg Sleep Range:  {user_stats['avg_sleep'].min():.1f} - {user_stats['avg_sleep'].max():.1f}
Avg HR Range:     {user_stats['avg_hr'].min():.0f} - {user_stats['avg_hr'].max():.0f}

ANOMALIES:
-----------
10 users have intentional 40%+ activity drops for testing anomaly detection.
These drops occur in the last 3-7 days to match the detection window.
Anomaly users: user_001, user_002, user_003, user_004, user_005, user_006, user_007, user_008, user_009, user_010

NOTES:
-----------
- Age-adjusted baselines: Younger users have higher activity, older users have lower activity
- Weekend activity is ~30% lower than weekdays (built into simulation)
- Anomaly users also show reduced sleep and elevated heart rate during drop periods
- Data is suitable for rolling-window anomaly detection (compare last 3 days vs previous 7-day avg)
"""

    with open(output_path, "w") as f:
        f.write(metadata.strip())

    print(f"  [OK] Metadata saved to {output_path}")


# ──────────────────────────────────────────────
# Main Pipeline
# ──────────────────────────────────────────────

def run_pipeline():
    """Run the full data ingestion pipeline."""
    print("=" * 55)
    print("Healthmov Insight Engine - Data Ingestion Pipeline")
    print("=" * 55)

    csv_path = os.path.join(os.path.dirname(__file__), "health_logs.csv")
    metadata_path = os.path.join(os.path.dirname(__file__), "metadata.txt")

    # Step 1: Test MongoDB connection
    print("\n1. Testing MongoDB connection...")
    result = test_connection()
    if result["status"] != "connected":
        print(f"  [FAIL] {result['error']}")
        sys.exit(1)
    print(f"  [OK] Connected to MongoDB Atlas")

    # Step 2: Load CSV
    print("\n2. Loading CSV...")
    df = load_csv(csv_path)

    # Step 3: Validate
    print("\n3. Validating data...")
    validate_dataframe(df)

    # Step 4: Pre-process
    print("\n4. Pre-processing...")
    df = preprocess_dataframe(df)

    # Step 5: Print summary
    print("\n5. DataFrame summary:")
    print_summary(df)

    # Step 6: Upload to MongoDB
    print("\n6. Uploading to MongoDB...")
    inserted = upload_to_mongodb(df)

    # Step 7: Save metadata
    print("\n7. Saving metadata for LLM context...")
    save_metadata(df, metadata_path)

    # Done
    print("\n" + "=" * 55)
    print(f"[OK] Pipeline complete: {inserted} records ingested into MongoDB")
    print("=" * 55)

    close_connection()


if __name__ == "__main__":
    run_pipeline()
