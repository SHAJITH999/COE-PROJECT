# REST API Reference — Inventory Balancing Recommender

## Base URL
```
http://localhost:8000
```

## Starting the API
```bash
uvicorn src.api.app:app --reload --port 8000
```

## Endpoints

### `GET /health`
Health check. Returns service status.

**Response:**
```json
{"status": "healthy", "service": "...", "timestamp": "..."}
```

---

### `POST /recommend`
Run transfer + purchase recommendations for a scenario.

**Body:**
```json
{"scenario": "NORMAL"}
```
`scenario` options: `NORMAL` | `DELAY` | `CAPACITY_LOSS` | `URGENT_DEMAND`

**Response:**
```json
{
  "scenario": "NORMAL",
  "total_recommendations": 5375,
  "recommendations": [...],
  "metrics": [...]
}
```

---

### `POST /simulate`
Run baseline vs proposed experiment for a disruption scenario.

**Body:**
```json
{"scenario": "DELAY"}
```

**Response:**
```json
{
  "scenario": "DELAY",
  "experiment_metrics": {...},
  "recommendation_metrics": [...]
}
```

---

### `GET /metrics`
Return stored baseline, recommender, and experiment summary metrics.

---

### `POST /approve`
Approve a recommendation.

**Body:**
```json
{"recommendation_id": "REC00001"}
```

---

### `POST /reject`
Reject a recommendation.

**Body:**
```json
{"recommendation_id": "REC00001"}
```

---

### `POST /override`
Override a recommendation. **Requires a non-empty `override_reason`.**

**Body:**
```json
{"recommendation_id": "REC00001", "override_reason": "Seasonal adjustment"}
```

Returns `400` if `override_reason` is empty.  
Returns `404` if `recommendation_id` does not exist.
