"""
Regenerate health data with:
1. User names instead of user_001, user_002, etc.
2. 5 random anomalies between users 1-30
3. Diverse anomaly types (steps, sleep, heart_rate)
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
ANOMALY_USER_IDS = [5, 12, 15, 23, 28]  # 5 random users between 1-30
ANOMALY_METRICS = ["steps", "sleep_hours", "steps", "heart_rate", "sleep_hours"]  # Diverse metrics

# User names (50 realistic names)
USER_NAMES = [
    "Sarah Johnson", "Michael Chen", "Emily Rodriguez", "David Kim", "Jessica Martinez",
    "James Wilson", "Ashley Brown", "Christopher Lee", "Amanda Taylor", "Daniel Anderson",
    "Jennifer Thomas", "Matthew Jackson", "Lauren White", "Andrew Harris", "Stephanie Martin",
    "Joshua Thompson", "Nicole Garcia", "Ryan Martinez", "Megan Robinson", "Kevin Clark",
    "Rachel Lewis", "Brandon Walker", "Samantha Hall", "Justin Allen", "Brittany Young",
    "Tyler Hernandez", "Kayla King", "Eric Wright", "Amber Lopez", "Jonathan Hill",
    "Melissa Scott", "Nicholas Green", "Rebecca Adams", "Jacob Baker", "Michelle Nelson",
    "Alexander Carter", "Laura Mitchell", "Zachary Perez", "Hannah Roberts", "Nathan Turner",
    "Olivia Phillips", "Ethan Campbell", "Sophia Parker", "William Evans", "Isabella Edwards",
    "Benjamin Collins", "Ava Stewart", "Lucas Sanchez", "Mia Morris", "Mason Rogers"
]

# Age ranges
AGE_MIN = 18
AGE_MAX = 75

# Realistic baseline ranges
STEPS_MEAN = 8000
STEPS_STD = 2000
SLEEP_MEAN = 7.5
SLEEP_STD = 1.0
HEART_RATE_MEAN = 72
HEART_RATE_STD = 8


def get_age_adjusted_baselines(age):
    """Adjust health baselines based on age group."""
    if age <= 30:
        steps_multiplier = 1.15
        hr_adjustment = -3
        sleep_adjustment = -0.2
    elif age <= 50:
        steps_multiplier = 1.0
        hr_adjustment = 0
        sleep_adjustment = 0
    elif age <= 65:
        steps_multiplier = 0.85
        hr_adjustment = 2
        sleep_adjustment = 0.1
    else:
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


def generate_normal_user_data(user_id, user_name, age, start_date, num_days):
    """Generate normal health data for a user without anomalies."""
    data = []
    baselines = get_age_adjusted_baselines(age)
    
    for day in range(num_days):
        date = start_date + timedelta(days=day)
        is_weekend = date.weekday() >= 5
        steps_modifier = 0.7 if is_weekend else 1.0
        
        steps = max(0, int(np.random.normal(baselines['steps_mean'] * steps_modifier, baselines['steps_std'])))
        sleep_hours = max(4, min(12, np.random.normal(baselines['sleep_mean'], baselines['sleep_std'])))
        heart_rate = max(50, min(100, int(np.random.normal(baselines['heart_rate_mean'], baselines['heart_rate_std']))))
        
        data.append({
            'user_id': user_id,
            'user_name': user_name,
            'age': age,
            'date': date.strftime('%Y-%m-%d'),
            'steps': steps,
            'sleep_hours': round(sleep_hours, 1),
            'heart_rate': heart_rate
        })
    
    return data


def generate_anomaly_user_data(user_id, user_name, age, start_date, num_days, anomaly_metric):
    """Generate health data with intentional drop in specified metric."""
    data = []
    baselines = get_age_adjusted_baselines(age)
    
    # Drop occurs in last 3 days
    drop_start_day = num_days - 3
    drop_duration = 3
    
    for day in range(num_days):
        date = start_date + timedelta(days=day)
        is_weekend = date.weekday() >= 5
        steps_modifier = 0.7 if is_weekend else 1.0
        
        # Check if we're in the anomaly period
        if drop_start_day <= day < drop_start_day + drop_duration:
            drop_percentage = random.uniform(0.50, 0.80)
            
            if anomaly_metric == "steps":
                steps_modifier *= (1 - drop_percentage)
                sleep_modifier = 1.0
                heart_rate_modifier = 1.0
            elif anomaly_metric == "sleep_hours":
                steps_modifier *= 1.0
                sleep_modifier = (1 - drop_percentage)
                heart_rate_modifier = 1.0
            elif anomaly_metric == "heart_rate":
                steps_modifier *= 1.0
                sleep_modifier = 1.0
                heart_rate_modifier = (1 + drop_percentage)  # Increase for heart rate
        else:
            sleep_modifier = 1.0
            heart_rate_modifier = 1.0
        
        # Generate values
        steps = max(0, int(np.random.normal(baselines['steps_mean'] * steps_modifier, baselines['steps_std'])))
        sleep_hours = max(4, min(12, np.random.normal(baselines['sleep_mean'] * sleep_modifier, baselines['sleep_std'])))
        heart_rate = max(50, min(100, int(np.random.normal(baselines['heart_rate_mean'] * heart_rate_modifier, baselines['heart_rate_std']))))
        
        data.append({
            'user_id': user_id,
            'user_name': user_name,
            'age': age,
            'date': date.strftime('%Y-%m-%d'),
            'steps': steps,
            'sleep_hours': round(sleep_hours, 1),
            'heart_rate': heart_rate
        })
    
    return data


def generate_dataset():
    """Generate complete dataset with normal and anomaly users."""
    print("Regenerating health data with user names and diverse anomalies...")
    
    start_date = datetime(2026, 4, 1)
    all_data = []
    
    # Generate ages for all users
    user_ages = {}
    for user_id in range(1, NUM_USERS + 1):
        age_group = random.choice([
            random.randint(18, 30),
            random.randint(31, 50),
            random.randint(31, 50),
            random.randint(51, 75),
        ])
        user_ages[user_id] = age_group
    
    # Generate data for all users
    for user_id in range(1, NUM_USERS + 1):
        user_id_str = f"user_{user_id:03d}"
        user_name = USER_NAMES[user_id - 1]
        age = user_ages[user_id]
        
        # Check if this user should have an anomaly
        if user_id in ANOMALY_USER_IDS:
            anomaly_index = ANOMALY_USER_IDS.index(user_id)
            anomaly_metric = ANOMALY_METRICS[anomaly_index]
            print(f"  Generating anomaly user: {user_id_str} ({user_name}, age {age}) - {anomaly_metric} anomaly")
            user_data = generate_anomaly_user_data(user_id_str, user_name, age, start_date, NUM_DAYS, anomaly_metric)
        else:
            print(f"  Generating normal user: {user_id_str} ({user_name}, age {age})")
            user_data = generate_normal_user_data(user_id_str, user_name, age, start_date, NUM_DAYS)
        
        all_data.extend(user_data)
    
    # Create DataFrame
    df = pd.DataFrame(all_data)
    
    # Save to CSV
    output_file = 'data/health_logs.csv'
    df.to_csv(output_file, index=False)
    print(f"\n✓ Dataset saved to {output_file}")
    print(f"  Total records: {len(df)}")
    print(f"  Total users: {NUM_USERS}")
    print(f"  Users with anomalies: {len(ANOMALY_USER_IDS)}")
    print(f"  Anomaly users: {ANOMALY_USER_IDS}")
    print(f"  Anomaly metrics: {ANOMALY_METRICS}")
    
    return df


if __name__ == "__main__":
    df = generate_dataset()
    print("\n✓ Data regeneration complete!")
    print("\nSample data (first 10 rows):")
    print(df.head(10).to_string(index=False))
