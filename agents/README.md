# Agents - Step 7 Complete ✓

## Overview
The multi-agent system for Healthmov Insight Engine is now fully operational with both Agent A (Data Analyst) and Agent B (Health Coach) working together.

## Agent A: Data Analyst (Anomaly Detector)
**File**: `agent_a.py`

**What it does**:
- Queries MongoDB for all user health data
- Compares recent activity (last 3 days) vs baseline (7-day window)
- Detects 40%+ drops in steps, sleep, or heart rate
- Classifies severity: MODERATE (40-60%) or SEVERE (60%+)
- Saves anomaly reports to `anomalies.json`

**Current Results**:
- 10 anomalies detected out of 50 users (20%)
- 6 SEVERE, 4 MODERATE
- Drop range: 47.6% to 78.0%

## Agent B: Health Coach (Recommendation Generator)
**File**: `agent_b.py`

**What it does**:
1. **Reads anomalies** from Agent A's output (`anomalies.json`)
2. **Queries RAG knowledge base** using vector search to find relevant health advice
3. **Generates personalized recommendations** using Ollama (llama3.2 local LLM)
4. **Saves to MongoDB** in the `health_advice` collection

**Key Features**:
- ✅ **Personalized**: Addresses user by ID, references specific metrics and drop percentages
- ✅ **Evidence-based**: Uses RAG to retrieve scientifically-backed health knowledge
- ✅ **Motivational**: Warm, compassionate tone with actionable advice
- ✅ **Free**: Uses local Ollama LLM (no API costs)

**Technical Details**:
- **LLM**: Ollama llama3.2 (2B parameters, runs locally)
- **Embedding model**: sentence-transformers/all-MiniLM-L6-v2
- **RAG retrieval**: Top 3 most relevant chunks per anomaly
- **Average recommendation length**: ~1,600 characters (3-4 paragraphs)

## Current Results

### Agent B Output Summary
- ✅ **10 recommendations generated** (one per anomaly)
- ✅ **All saved to MongoDB** `health_advice` collection
- ✅ **RAG sources included** for transparency
- ✅ **Personalized content** with specific metrics and actionable advice

### Sample Recommendation (user_001)
**Anomaly**: Steps dropped 62.1% (SEVERE)
**RAG Sources**: Physical Activity Guidelines for Americans 2nd Edition

**Recommendation**:
> Dear user_001,
> 
> I want to start by acknowledging the challenges you're facing right now. The recent drop in your daily steps from 6880.9 to 2607.3 is concerning, and I'm here to support you in getting back on track. A 62.1% decline is a significant decrease, but please know that it's not too late to make a positive change.
> 
> According to the Physical Activity Guidelines for Americans 2nd Edition, even small increases in moderate-intensity physical activity provide health benefits. I encourage you to start by setting realistic goals and gradually increasing your daily step count. Perhaps begin with short walks of 5-10 minutes each day, aiming to increase the duration and frequency over time...
> 
> I'm here to support you in this journey, user_001. Let's work together to get your daily steps back on track and set you up for success. I encourage you to take small steps today (pun intended!) and see how it goes from there. You got this!

## Files
- `agent_a.py` - Anomaly detection agent
- `agent_b.py` - Health coach recommendation generator
- `models.py` - Data models (AnomalyReport, HealthRecommendation)
- `anomalies.json` - Agent A output (10 anomalies)
- `view_recommendations.py` - Utility to view all recommendations

## MongoDB Collections Used
1. **health_logs** - User health data (input)
2. **health_knowledge** - RAG knowledge base (151 chunks)
3. **health_advice** - Generated recommendations (output)

## How to Run

### Run Agent A (Anomaly Detection)
```bash
python agents/agent_a.py
```

### Run Agent B (Generate Recommendations)
```bash
python agents/agent_b.py
```

### View All Recommendations
```bash
python agents/view_recommendations.py
```

## Next Steps
The multi-agent system is ready for:
- **Step 8**: Build FastAPI backend to expose these agents via REST API
- **Step 9**: Build React frontend to display recommendations to users
- **Step 10**: Deploy to production

## Status
✅ **COMPLETE** - Both agents operational, 10 personalized recommendations generated and stored
