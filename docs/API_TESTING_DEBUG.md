# API Testing Debug Report

## Issue Summary

First API call to trigger the stock analysis workflow failed with multiple errors before succeeding.

---

## Attempt Timeline

### Attempt 1: Wrong Endpoint Path

**Request:**
```
POST http://localhost:8000/api/v1/workflows/trigger
Body: {"workflow_name": "stock_analysis", "input": {"ticker": "RELIANCE"}}
```

**Response:**
```json
{"detail": "Not Found"}
```

**Problem:** Endpoint path was incorrect. Used `/workflows/trigger` but the actual route is `/{name}/trigger`.

---

### Attempt 2: Wrong Workflow Name

**Request:**
```
POST http://localhost:8000/api/v1/workflows/stock_analysis/trigger
Body: {"input": {"ticker": "RELIANCE"}}
```

**Response:**
```json
{"detail": "Unknown workflow: stock_analysis"}
```

**Problem:** Workflow name was wrong. Used `stock_analysis` but the registered name is `stock_analyser`.

---

### Attempt 3: Correct Request

**Request:**
```
POST http://localhost:8000/api/v1/workflows/stock_analyser/trigger
Body: {"input": {"index": "NIFTY50"}}
```

**Response:**
```json
{"run_id": "3e46a4d7758f4900897acdce1252a458"}
```

**Result:** Success - workflow triggered.

---

## Root Causes

| Issue | Wrong Value | Correct Value |
|-------|-------------|---------------|
| Endpoint path | `/workflows/trigger` | `/workflows/{name}/trigger` |
| Workflow name | `stock_analysis` | `stock_analyser` |
| Input field | `ticker` | `index` |

---

## How to Find Correct Values

### 1. List All Workflows
```bash
curl http://localhost:8000/api/v1/workflows
```

Returns available workflows with their names and input fields.

### 2. Check OpenAPI Docs
Visit `http://localhost:8000/docs` to see all endpoints.

### 3. Check Route Definition
File: `backend/app/api/v1/workflow_routes.py`
```python
@router.post("/{name}/trigger")
def trigger_workflow(name: str, ...):
```

---

## Lessons Learned

1. Always check `/api/v1/workflows` first to get correct workflow names
2. Use the OpenAPI docs at `/docs` to verify endpoint paths
3. Check `input_fields` in workflow response for correct parameter names
