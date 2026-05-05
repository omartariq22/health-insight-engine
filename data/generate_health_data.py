"""
Generate simulated health data for Healthmov Insight Engine.

This script creates realistic user health logs including:
- Daily step counts
- Sleep duration (hours)
- Average heart rate (bpm)

Some users will have intentional 40%+ activity drops to test anomaly detection.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

# Configuration
NUM_USERS = 50
NUM_DAYS = 30
ANOMALY_USER_COUNT = 10  # Number of users with intentional activity drops

# Realistic baseline ranges
STEPS_MEAN = 8000
STEPS_STD = 2000
SLEEP_MEAN = 7.5
SLEEP_STD = 1.0
HEART_RATE_MEAN = 72
HEART_RATE_STD = 8


def generate_normal_user_data(user_id, start_date, num_days):
    """Generate normal health data for a user without anomalies."""
    data = []
    
    for day in range(num_days):
        date = start_date + timedelta(days=day)
        
        # Add some weekly patterns (lower activity on weekends)
        is_weekend = date.weekday() >= 5
        steps_modifier = 0.7 if is_weekend else 1.0
        
        # Generate realistic values with some daily variation
        steps = max(0, int(np.random.normal(STEPS_MEAN * steps_modifier, STEPS_STD)))
        sleep_hours = max(4, min(12, np.random.normal(SLEEP_MEAN, SLEEP_STD)))
        heart_rate = max(50, min(100, int(np.random.normal(HEART_RATE_MEAN, HEART_RATE_STD))))
        
        data.append({
            'user_id': user_id,
            'date': date.strftime('%Y-%m-%d'),
            'steps': steps,
            'sleep_hours': round(sleep_hours, 1),
            'heart_rate': heart_rate
        })
    
    return data


def generate_anomaly_user_data(user_id, start_date, num_days):
    """Generate health data with intentional 40%+ activity drop."""
    data = []
    
    # Choose when the drop occurs (between day 10 and day 20)
    drop_start_day = random.randint(10, 20)
    drop_duration = random.randint(3, 7)  # Drop lasts 3-7 days
    
    for day in range(num_days):
        date = start_date + timedelta(days=day)
        is_weekend = date.weekday() >= 5
        steps_modifier = 0.7 if is_weekend else 1.0
        
        # Check if we're in the anomaly period
        if drop_start_day <= day < drop_start_day + drop_duration:
            # Apply 40-60% drop in activity
            drop_percentage = random.uniform(0.4, 0.6)
            steps_modifier *= (1 - drop_percentage)
            
            # Also reduce sleep slightly and increase heart rate (stress indicator)
            sleep_modifier = 0.85
            heart_rate_modifier = 1.1
        else:
            sleep_modifier = 1.0
            heart_rate_modifier = 1.0
        
        # Generate values
        steps = max(0, int(np.random.normal(STEPS_MEAN * steps_modifier, STEPS_STD)))
        sleep_hours = max(4, min(12, np.random.normal(SLEEP_MEAN * sleep_modifier, SLEEP_STD)))
        heart_rate = max(50, min(100, int(np.random.normal(HEART_RATE_MEAN * heart_rate_modifier, HEART_RATE_STD))))
        
        data.append({
            'user_id': user_id,
            'date': date.strftime('%Y-%m-%d'),
            'steps': steps,
            'sleep_hours': round(sleep_hours, 1),
            'heart_rate': heart_rate
        })
    
    return data


def generate_dataset():
    """Generate complete dataset with normal and anomaly users."""
    print("Generating simulated health data...")
    
    start_date = datetime.now() - timedelta(days=NUM_DAYS)
    all_data = []
    
    # Generate data for all users
    for user_id in range(1, NUM_USERS + 1):
        user_name = f"user_{user_id:03d}"
        
        # First ANOMALY_USER_COUNT users will have anomalies
        if user_id <= ANOMALY_USER_COUNT:
            print(f"  Generating anomaly user: {user_name}")
            user_data = generate_anomaly_user_data(user_name, start_date, NUM_DAYS)
        else:
            print(f"  Generating normal user: {user_name}")
            user_data = generate_normal_user_data(user_name, start_date, NUM_DAYS)
        
        all_data.extend(user_data)
    
    # Create DataFrame
    df = pd.DataFrame(all_data)
    
    # Save to CSV
    output_file = 'data/health_logs.csv'
    df.to_csv(output_file, index=False)
    print(f"\n✓ Dataset saved to {output_file}")
    print(f"  Total records: {len(df)}")
    print(f"  Total users: {NUM_USERS}")
    print(f"  Users with anomalies: {ANOMALY_USER_COUNT}")
    print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
    
    # Generate metadata file
    generate_metadata(df)
    
    return df


def generate_metadata(df):
    """Generate metadata summary for LLM context."""
    metadata = f"""
Dataset: Healthmov Health Logs
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

STRUCTURE:
-----------
Total Records: {len(df)}
Total Users: {df['user_id'].nunique()}
Date Range: {df['date'].min()} to {df['date'].max()}
Days per User: {NUM_DAYS}

COLUMNS:
-----------
1. user_id (string): Unique user identifier (format: user_XXX)
2. date (string): Date in YYYY-MM-DD format
3. steps (integer): Daily step count
4. sleep_hours (float): Hours of sleep (rounded to 1 decimal)
5. heart_rate (integer): Average heart rate in beats per minute (bpm)

STATISTICS:
-----------
Steps:
  Mean: {df['steps'].mean():.0f}
  Std: {df['steps'].std():.0f}
  Min: {df['steps'].min()}
  Max: {df['steps'].max()}

Sleep Hours:
  Mean: {df['sleep_hours'].mean():.1f}
  Std: {df['sleep_hours'].std():.1f}
  Min: {df['sleep_hours'].min()}
  Max: {df['sleep_hours'].max()}

Heart Rate:
  Mean: {df['heart_rate'].mean():.0f}
  Std: {df['heart_rate'].std():.0f}
  Min: {df['heart_rate'].min()}
  Max: {df['heart_rate'].max()}

ANOMALIES:
-----------
{ANOMALY_USER_COUNT} users have intentional 40%+ activity drops for testing anomaly detection.
These drops occur randomly between day 10-20 and last 3-7 days.
Anomaly users: {', '.join([f'user_{i:03d}' for i in range(1, ANOMALY_USER_COUNT + 1)])}
"""
    
    metadata_file = 'data/metadata.txt'
    with open(metadata_file, 'w') as f:
        f.write(metadata.strip())
    
    print(f"✓ Metadata saved to {metadata_file}")


if __name__ == "__main__":
    df = generate_dataset()
    
    # Display sample data
    print("\nSample data (first 10 rows):")
    print(df.head(10).to_string(index=False))
    
    print("\n✓ Step 2 complete: Simulated health data generated successfully!")
