# Multi-Agent Pipeline Architecture

## Overview
The Healthmov Insight Engine uses LangGraph to orchestrate a multi-agent system that automatically detects health anomalies and generates personalized recommendations.

## Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    HEALTHMOV PIPELINE                           │
│                  (Orchestrated by LangGraph)                    │
└─────────────────────────────────────────────────────────────────┘

    ┌──────────────────┐
    │  START PIPELINE  │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │  1. INGEST DATA  │  ← Load health_logs.csv into MongoDB
    │                  │    (50 users, 30 days each)
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ 2. DETECT        │  ← Agent A: Anomaly Detector
    │    ANOMALIES     │    - Compare last 3 days vs 7-day baseline
    │    (Agent A)     │    - Detect 40%+ drops in steps/sleep/HR
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ 3. CHECK         │  ← Decision Point
    │    ANOMALIES     │    
    └────────┬─────────┘
             │
        ┌────┴────┐
        │         │
   Anomalies   No Anomalies
    Found       Found
        │         │
        ▼         ▼
    ┌──────┐  ┌─────┐
    │      │  │ END │
    │      │  └─────┘
    │      │
    ▼      │
┌──────────────────┐
│ 4. GENERATE      │  ← Agent B: Health Coach
│    RECOMMENDATIONS│    - Query RAG knowledge base
│    (Agent B)     │    - Generate personalized advice with Ollama
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 5. SAVE RESULTS  │  ← Verify MongoDB storage
│                  │    - Confirm recommendations saved
└────────┬─────────┘
         │
         ▼
    ┌─────┐
    │ END │
    └─────┘
```

## Components

### Node 1: Ingest Data
- **Function**: `ingest_data_node()`
- **Purpose**: Load CSV data into MongoDB
- **Input**: None (reads from `data/health_logs.csv`)
- **Output**: Total user count
- **Next**: Always → Detect Anomalies

### Node 2: Detect Anomalies (Agent A)
- **Function**: `detect_anomalies_node()`
- **Purpose**: Run Agent A to find users with health drops
- **Input**: User count from previous step
- **Output**: List of anomalies
- **Next**: Always → Check Anomalies

### Node 3: Check Anomalies (Decision Point)
- **Function**: `check_anomalies_node()`
- **Purpose**: Decide whether to continue or stop
- **Input**: Anomaly list
- **Output**: Decision (continue/stop)
- **Next**: 
  - If anomalies found → Generate Recommendations
  - If no anomalies → END

### Node 4: Generate Recommendations (Agent B)
- **Function**: `generate_recommendations_node()`
- **Purpose**: Run Agent B to create personalized advice
- **Input**: Anomaly list
- **Output**: List of recommendations
- **Next**: Always → Save Results

### Node 5: Save Results
- **Function**: `save_results_node()`
- **Purpose**: Verify all data is stored in MongoDB
- **Input**: Recommendation list
- **Output**: Confirmation message
- **Next**: Always → END

## State Management

The pipeline uses a shared state object that flows through all nodes:

```python
class PipelineState(TypedDict):
    step: str                # Current step name
    anomalies: list          # List of detected anomalies
    recommendations: list    # List of generated recommendations
    total_users: int         # Total users in dataset
    status: str              # Current status (running/success/error/complete)
    message: str             # Status message
```

## Conditional Logic

The pipeline has one conditional edge at the "Check Anomalies" node:

```python
def should_continue(state: PipelineState) -> Literal["generate_recommendations", "end"]:
    """Decide whether to continue to Agent B or stop."""
    if state.get("status") == "continue":
        return "generate_recommendations"
    else:
        return "end"
```

## Benefits of LangGraph Orchestration

1. **Automated Workflow**: Run entire pipeline with one command
2. **State Management**: Shared state flows through all nodes
3. **Conditional Logic**: Smart decision-making (skip Agent B if no anomalies)
4. **Error Handling**: Each node can report errors to the state
5. **Extensibility**: Easy to add new nodes or modify flow
6. **Visibility**: Clear execution flow and status tracking

## Usage

### Run the Complete Pipeline
```bash
python pipeline.py
```

### Expected Output
```
HEALTHMOV INSIGHT ENGINE - MULTI-AGENT PIPELINE
======================================================================

Pipeline Flow:
  1. Ingest Data → Load health data into MongoDB
  2. Detect Anomalies → Run Agent A
  3. Check Anomalies → Decision point
  4. Generate Recommendations → Run Agent B (if anomalies found)
  5. Save Results → Verify MongoDB storage

Starting pipeline execution...

======================================================================
STEP 1: INGESTING DATA
======================================================================
✓ Data ingestion complete: 50 users loaded

======================================================================
STEP 2: DETECTING ANOMALIES (AGENT A)
======================================================================
✓ Agent A complete: 10 anomalies detected

======================================================================
STEP 3: CHECKING ANOMALIES
======================================================================
✓ 10 anomalies found - continuing to Agent B

======================================================================
STEP 4: GENERATING RECOMMENDATIONS (AGENT B)
======================================================================
✓ Agent B complete: 10 recommendations generated

======================================================================
STEP 5: VERIFYING RESULTS
======================================================================
✓ Verified: 10 recommendations in MongoDB
✓ Pipeline execution successful!

======================================================================
PIPELINE EXECUTION SUMMARY
======================================================================
Status: COMPLETE
Total Users: 50
Anomalies Detected: 10
Recommendations Generated: 10
Message: Pipeline complete: 10 recommendations saved to MongoDB
======================================================================
```

## MongoDB Collections Used

1. **health_logs** - User health data (input)
2. **health_knowledge** - RAG knowledge base (151 chunks)
3. **health_advice** - Generated recommendations (output)

## Next Steps

With the pipeline complete, you can:
- Build a FastAPI backend to expose the pipeline via REST API
- Create a React frontend to trigger the pipeline and display results
- Add scheduling to run the pipeline automatically (e.g., daily)
- Extend the pipeline with additional agents or processing steps
