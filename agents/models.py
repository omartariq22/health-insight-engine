"""
Data models for agent outputs.

These dataclasses ensure type safety and provide clear structure
for data passed between agents and stored in MongoDB.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List
from datetime import datetime


@dataclass
class AnomalyReport:
    """
    Structured report of a detected anomaly for a single user.
    
    This is the output of Agent A (Data Analyst) and the input to Agent B (Health Coach).
    """
    user_id: str
    user_name: str = ""  # User's actual name
    age: int = 0  # User age for age-appropriate recommendations
    metric: str = ""  # 'steps', 'sleep_hours', or 'heart_rate'
    
    # Baseline period (7-day average)
    baseline_avg: float = 0.0
    baseline_period: str = ""  # e.g., '2026-04-05 to 2026-04-11'
    
    # Recent period (3-day average)
    recent_avg: float = 0.0
    recent_period: str = ""  # e.g., '2026-05-02 to 2026-05-04'
    
    # Drop analysis
    drop_percentage: float = 0.0  # e.g., 45.2 means 45.2% drop
    severity: str = ""  # 'moderate' (40-60%) or 'severe' (>60%)
    
    # Metadata
    detected_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self):
        """Convert to dictionary for MongoDB storage."""
        return asdict(self)
    
    def to_summary(self):
        """Generate a human-readable summary string."""
        name_display = self.user_name if self.user_name else self.user_id
        return (
            f"User {name_display} (age {self.age}): {self.metric} dropped {self.drop_percentage:.1f}% "
            f"({self.baseline_avg:.1f} -> {self.recent_avg:.1f}) - {self.severity.upper()}"
        )


@dataclass
class HealthRecommendation:
    """
    AI-generated health recommendation from Agent B.
    
    This is stored in MongoDB and displayed in the dashboard.
    """
    user_id: str
    anomaly_report: dict
    recommendation: str
    rag_sources: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self):
        """Convert to dictionary for MongoDB storage."""
        return asdict(self)
