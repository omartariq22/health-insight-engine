# Data

Contains simulated health data and data generation scripts for the Healthmov Insight Engine.

## Files

### `generate_health_data.py`
Script to generate realistic simulated user health logs over 30 days.

**Features:**
- Generates data for 50 users (10 with anomalies, 40 normal)
- Includes realistic weekly patterns (lower activity on weekends)
- Intentionally creates 40-60% activity drops in anomaly users
- Outputs both CSV data and metadata summary

**Usage:**
```bash
python data/generate_health_data.py
```

### `health_logs.csv`
Generated dataset containing 1,500 records (50 users × 30 days).

**Columns:**
- `user_id`: Unique identifier (format: user_XXX)
- `date`: Date in YYYY-MM-DD format
- `steps`: Daily step count (integer)
- `sleep_hours`: Hours of sleep (float, 1 decimal)
- `heart_rate`: Average heart rate in bpm (integer)

**Statistics:**
- Steps: Mean ~8000, Range 0-15000
- Sleep: Mean ~7.5 hours, Range 4-12 hours
- Heart Rate: Mean ~72 bpm, Range 50-100 bpm

### `metadata.txt`
Auto-generated summary of dataset structure and statistics for LLM context.

## Anomaly Users
The first 10 users (`user_001` through `user_010`) have intentional activity drops:
- Drop occurs randomly between day 10-20
- Lasts 3-7 days
- Activity reduced by 40-60%
- Used to test Agent A's anomaly detection logic
