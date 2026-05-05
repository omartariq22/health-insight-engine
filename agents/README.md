# AI Agents

Multi-agent system for anomaly detection and health coaching.

## Agents

### **Agent A: The Data Analyst (Anomaly Detector)**
**File:** `agent_a.py`

**Purpose:** Identifies users with significant drops in health engagement metrics.

**Detection Logic:**
- **Baseline Period:** Average of days 8-14 from the end (7-day window)
- **Recent Period:** Average of last 3 days
- **Anomaly Threshold:** Recent < Baseline × 0.6 (i.e., 40%+ drop)

**Metrics Tracked:**
- `steps` - Primary engagement indicator
- `sleep_hours` - Secondary health indicator
- `heart_rate` - Stress/health indicator

**Output:** Structured `AnomalyReport` objects containing:
- User ID
- Metric that dropped
- Percentage drop
- Baseline vs recent averages
- Date ranges
- Severity level (moderate: 40-60%, severe: >60%)

**Usage:**
```bash
python agents/agent_a.py
```

**Output Files:**
- `agents/anomalies.json` - JSON file with all detected anomalies

---

### **Agent B: The Health Coach**
**File:** `agent_b.py` *(Coming in Step 7)*

**Purpose:** Generates personalized, scientifically-backed health recommendations using RAG.

**Input:** AnomalyReport from Agent A
**Output:** Personalized health advice with source citations

---

## Data Models

**File:** `models.py`

Pydantic models for type-safe data structures:
- `AnomalyReport` - Output from Agent A
- `HealthRecommendation` - Output from Agent B

These models ensure consistent data structure across agents and database storage.
