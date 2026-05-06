"""
Generate simulated health data for Healthmov Insight Engine.

This script creates realistic user health logs including:
- Daily step counts
- Sleep duration (hours)
- Average heart rate (bpm)
- User age (for age-appropriate recommendations)

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
ANOMALY_USER_COUNT = 10  # Number of users with intentional activity drops (20% of users)

# Age ranges for realistic distribution
AGE_MIN = 18
AGE_MAX = 75

# Realistic baseline ranges (will be adjusted by age)
STEPS_MEAN = 8000
STEPS_STD = 2000
SLEEP_MEAN = 7.5
SLEEP_STD = 1.0
HEART_RATE_MEAN = 72
HEART_RATE_STD = 8


def get_age_adjusted_baselines(age):
    """
    Adjust health baselines based on age group.
    
    Age groups:
    - Young adults (18-30): Higher activity, lower resting HR
    - Adults (31-50): Moderate activity, stable HR
    - Middle-aged (51-65): Slightly lower activity, slightly higher HR
    - Seniors (66+): Lower activity, higher resting HR
    """
    if age <= 30:
        # Young adults: most active
        steps_multiplier = 1.15
        hr_adjustment = -3
        sleep_adjustment = -0.2  # Slightly less sleep
    elif age <= 50:
        # Adults: baseline
        steps_multiplier = 1.0
        hr_adjustment = 0
        sleep_adjustment = 0
    elif age <= 65:
        # Middle-aged: slightly less active
        steps_multiplier = 0.85
        hr_adjustment = 2
        sleep_adjustment = 0.1
    else:
        # Seniors: less active, more rest
        steps_multiplier = 0.65
        hr_adjustment = 5
        sleep_adjustment = 0.3
    
    return {
        'steps_mean': STEPS_MEAN * steps_multiplier,
        'steps_std': STEPS_STD * steps_multiplier,
        'sleep_mean': SLEEP_MEAN + sleep_adjustment,
        'sleep_std': SLEEP_STD,
        'heart_rate_mean': HEART_RATE_MEAN + hr_adjustment,
        'heart_rate_std': HEART_RATE_STD,
    }


def generate_normal_user_data(user_id, age, start_date, num_days):
    """Generate normal health data for a user without anomalies."""
    data = []
    
    # Get age-adjusted baselines
    baselines = get_age_adjusted_baselines(age)
    
    for day in range(num_days):
        date = start_date + timedelta(days=day)
        
        # Add some weekly patterns (lower activity on weekends)
        is_weekend = date.weekday() >= 5
        steps_modifier = 0.7 if is_weekend else 1.0
        
        # Generate realistic values with some daily variation
        steps = max(0, int(np.random.normal(baselines['steps_mean'] * steps_modifier, baselines['steps_std'])))
        sleep_hours = max(4, min(12, np.random.normal(baselines['sleep_mean'], baselines['sleep_std'])))
        heart_rate = max(50, min(100, int(np.random.normal(baselines['heart_rate_mean'], baselines['heart_rate_std']))))
        
        data.append({
            'user_id': user_id,
            'age': age,
            'date': date.strftime('%Y-%m-%d'),
            'steps': steps,
            'sleep_hours': round(sleep_hours, 1),
            'heart_rate': heart_rate
        })
    
    return data


def generate_anomaly_user_data(user_id, age, start_date, num_days):
    """Generate health data with intentional 40%+ activity drop."""
    data = []
    
    # Get age-adjusted baselines
    baselines = get_age_adjusted_baselines(age)
    
    # Choose when the drop occurs - MUST be in the last 3 days (the "recent" window)
    # Agent A compares last 3 days (recent) vs days -10 to -3 (baseline)
    # So the drop must happen in the last 3 days to be detected
    drop_start_day = num_days - 3  # Always start at day 27 (last 3 days)
    drop_duration = 3  # Drop lasts exactly 3 days (the entire recent window)
    
    for day in range(num_days):
        date = start_date + timedelta(days=day)
        is_weekend = date.weekday() >= 5
        steps_modifier = 0.7 if is_weekend else 1.0
        
        # Check if we're in the anomaly period
        if drop_start_day <= day < drop_start_day + drop_duration:
            # Apply 50-80% drop in activity (increased from 40-60% for more dramatic detection)
            drop_percentage = random.uniform(0.50, 0.80)
            steps_modifier *= (1 - drop_percentage)
            
            # Also reduce sleep slightly and increase heart rate (stress indicator)
            sleep_modifier = 0.80  # More noticeable sleep reduction
            heart_rate_modifier = 1.15  # More noticeable heart rate increase
        else:
            sleep_modifier = 1.0
            heart_rate_modifier = 1.0
        
        # Generate values
        steps = max(0, int(np.random.normal(baselines['steps_mean'] * steps_modifier, baselines['steps_std'])))
        sleep_hours = max(4, min(12, np.random.normal(baselines['sleep_mean'] * sleep_modifier, baselines['sleep_std'])))
        heart_rate = max(50, min(100, int(np.random.normal(baselines['heart_rate_mean'] * heart_rate_modifier, baselines['heart_rate_std']))))
        
        data.append({
            'user_id': user_id,
            'age': age,
            'date': date.strftime('%Y-%m-%d'),
            'steps': steps,
            'sleep_hours': round(sleep_hours, 1),
            'heart_rate': heart_rate
        })
    
    return data


def generate_dataset():
    """Generate complete dataset with normal and anomaly users."""
    print("Generating simulated health data...")
    
    start_date = datetime(2026, 4, 1)  # Fixed date for full reproducibility
    all_data = []
    
    # Generate ages for all users (diverse distribution)
    user_ages = {}
    for user_id in range(1, NUM_USERS + 1):
        # Create realistic age distribution
        age_group = random.choice([
            random.randint(18, 30),   # 25% young adults
            random.randint(31, 50),   # 25% adults
            random.randint(31, 50),   # 25% adults (weighted)
            random.randint(51, 75),   # 25% middle-aged/seniors
        ])
        user_ages[user_id] = age_group
    
    # Generate data for all users
    for user_id in range(1, NUM_USERS + 1):
        user_name = f"user_{user_id:03d}"
        age = user_ages[user_id]
        
        # First ANOMALY_USER_COUNT users will have anomalies
        if user_id <= ANOMALY_USER_COUNT:
            print(f"  Generating anomaly user: {user_name} (age {age})")
            user_data = generate_anomaly_user_data(user_name, age, start_date, NUM_DAYS)
        else:
            print(f"  Generating normal user: {user_name} (age {age})")
            user_data = generate_normal_user_data(user_name, age, start_date, NUM_DAYS)
        
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
    print(f"  Age range: {df['age'].min()} to {df['age'].max()}")
    print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
    
    # Generate metadata file
    generate_metadata(df)
    
    return df


def generate_metadata(df):
    """Generate metadata summary for LLM context."""
    
    # Age distribution
    age_bins = [18, 30, 50, 65, 75]
    age_labels = ['18-30 (Young Adults)', '31-50 (Adults)', '51-65 (Middle-aged)', '66-75 (Seniors)']
    df['age_group'] = pd.cut(df['age'], bins=age_bins, labels=age_labels, include_lowest=True)
    age_distribution = df.groupby('user_id').first()['age_group'].value_counts().sort_index()
    
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
2. age (integer): User age in years (18-75)
3. date (string): Date in YYYY-MM-DD format
4. steps (integer): Daily step count
5. sleep_hours (float): Hours of sleep (rounded to 1 decimal)
6. heart_rate (integer): Average heart rate in beats per minute (bpm)

AGE DISTRIBUTION:
-----------
{age_distribution.to_string()}

Note: Health baselines are age-adjusted:
- Young adults (18-30): Higher activity (~9,200 steps), lower HR (~69 bpm)
- Adults (31-50): Baseline activity (~8,000 steps), HR (~72 bpm)
- Middle-aged (51-65): Moderate activity (~6,800 steps), HR (~74 bpm)
- Seniors (66+): Lower activity (~5,200 steps), higher HR (~77 bpm)

STATISTICS:
-----------
Age:
  Mean: {df['age'].mean():.0f}
  Min: {df['age'].min()}
  Max: {df['age'].max()}

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
These drops occur in the last 3-7 days to match the detection window.
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
