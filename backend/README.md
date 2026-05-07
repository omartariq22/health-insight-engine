# Backend - FastAPI REST API

## Overview
FastAPI backend that exposes the Healthmov Insight Engine via REST API endpoints.

## Endpoints

### Health Check
- `GET /` - API health check and endpoint list

### Anomalies
- `GET /anomalies` - Get all detected anomalies
- Returns: List of anomaly reports with user_id, metric, drop_percentage, severity

### Recommendations
- `GET /recommendations` - Get all recommendations
- `GET /recommendations/{user_id}` - Get recommendation for specific user
- Returns: Recommendation document with anomaly_report, recommendation text, RAG sources

### User Health Data
- `GET /users/{user_id}/health` - Get health data for specific user
- Query params: `limit` (default: 30)
- Returns: List of health records sorted by date

### Pipeline Control
- `POST /run-pipeline` - Trigger pipeline execution (background task)
- `GET /pipeline-status` - Get current pipeline status

### Statistics
- `GET /stats` - Get system statistics (users, anomalies, recommendations)

## Running the API

### Start the server
```bash
python -m uvicorn backend.main:app --reload
```

### Access the API
- API Root: http://localhost:8000
- Interactive Docs: http://localhost:8000/docs
- Test Page: Open `backend/test_api.html` in your browser

## Testing

### Using curl
```bash
# Test health check
curl http://localhost:8000/

# Get all anomalies
curl http://localhost:8000/anomalies

# Get recommendation for user_001
curl http://localhost:8000/recommendations/user_001

# Get statistics
curl http://localhost:8000/stats
```

### Using the test page
Open `backend/test_api.html` in your browser to test all endpoints visually.

### Using FastAPI docs
Navigate to http://localhost:8000/docs for interactive API documentation.

## CORS Configuration
The API is configured to accept requests from:
- `http://localhost:3000` (React default port)

## Files
- `main.py` - FastAPI application with all endpoints
- `test_api.html` - Simple HTML test page
- `README.md` - This file
- `__init__.py` - Package initialization
