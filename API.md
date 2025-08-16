# Customer Feedback Dashboard API Documentation

## Overview

RESTful API untuk Customer Feedback Dashboard dengan integrasi AI untuk analisis sentimen, topik, dan automasi.

Base URL: `http://localhost:8000`
API Documentation: `http://localhost:8000/docs`

## Authentication

API menggunakan JWT Bearer token untuk autentikasi.

```http
Authorization: Bearer <your-jwt-token>
```

### Demo Accounts

| Role   | Email            | Password      | Access Level  |
| ------ | ---------------- | ------------- | ------------- |
| Demo   | `demo@cfd.app`   | `demo12345`   | Read-only     |
| Member | `member@cfd.app` | `member12345` | Full features |
| Admin  | `admin@cfd.app`  | `admin12345`  | Admin access  |

## Endpoints

### Authentication

#### POST /api/auth/login

Login dengan email dan password.

**Request:**

```json
{
  "email": "member@cfd.app",
  "password": "member12345"
}
```

**Response:**

```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "user": {
      "id": "uuid",
      "email": "member@cfd.app",
      "full_name": "Member User",
      "role": "member"
    }
  }
}
```

#### GET /api/auth/demo-tokens

Mendapatkan token demo untuk testing (development only).

### Projects

#### GET /api/projects

Mendapatkan daftar proyek.

**Query Parameters:**

- `page` (int): Halaman (default: 1)
- `per_page` (int): Item per halaman (default: 10)

**Response:**

```json
{
  "success": true,
  "data": {
    "projects": [
      {
        "id": "uuid",
        "name": "Demo Coffee Shop",
        "description": "Demo project",
        "is_demo": true,
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "pagination": {
      "total": 1,
      "page": 1,
      "per_page": 10,
      "total_pages": 1
    }
  }
}
```

#### POST /api/projects

Membuat proyek baru (Member/Admin only).

**Request:**

```json
{
  "name": "My Project",
  "description": "Project description"
}
```

#### GET /api/projects/:id/summary

Mendapatkan ringkasan analytics proyek.

**Response:**

```json
{
  "success": true,
  "data": {
    "total_feedbacks": 25,
    "sentiment_distribution": {
      "positive": 15,
      "negative": 5,
      "neutral": 5
    },
    "top_topics": [
      { "label": "layanan", "count": 12 },
      { "label": "produk", "count": 8 }
    ],
    "urgency_distribution": {
      "high": 2,
      "medium": 8,
      "low": 15
    }
  }
}
```

### Feedbacks

#### POST /api/feedbacks

Menambah feedback baru.

**Query Parameters:**

- `project_id` (string): ID proyek

**Request:**

```json
{
  "content": "Kopi di sini enak banget!",
  "source": "manual",
  "author_name": "John Doe",
  "language": "id"
}
```

#### POST /api/feedbacks/:id/analyze

Menganalisis feedback dengan AI pipeline.

**Request:**

```json
{
  "feedback_id": "uuid",
  "force_reanalysis": false
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "feedback_id": "uuid",
    "sentiment_label": "positive",
    "sentiment_score": 0.89,
    "sentiment_confidence": 0.92,
    "topics": [{ "label": "produk", "score": 0.85 }],
    "granite_summary": "Customer sangat puas dengan kualitas produk",
    "granite_insights": {
      "urgency": "low",
      "action_recommendation": "Pertahankan kualitas produk"
    }
  }
}
```

#### POST /api/feedbacks/analyze/batch

Menganalisis multiple feedback sekaligus.

**Request:**

```json
{
  "feedback_ids": ["uuid1", "uuid2"],
  "force_reanalysis": false
}
```

### Orchestrate (Automation)

#### GET /api/orchestrate/jobs

Mendapatkan daftar automation jobs.

**Query Parameters:**

- `project_id` (string, optional): Filter by project
- `status_filter` (string, optional): Filter by status
- `page`, `per_page`: Pagination

#### POST /api/orchestrate/jobs/:id/retry

Retry failed automation job.

#### POST /api/orchestrate/trigger/:feedback_id

Trigger manual automation untuk feedback.

**Query Parameters:**

- `job_kind` (string): Jenis job ("ticket", "alert", etc.)

## Rate Limiting

API memiliki rate limiting:

- General: 60 requests per minute per IP
- Analysis endpoints: 20 requests per minute
- Batch operations: 10 requests per minute

## Error Responses

Semua error menggunakan format standar:

```json
{
  "success": false,
  "message": "Error description",
  "errors": ["Detailed error messages"]
}
```

### HTTP Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `429` - Rate Limited
- `500` - Internal Server Error

## AI Services Integration

### Sentiment Analysis

- **Indonesian**: `cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual`
- **English**: `distilbert-base-uncased-finetuned-sst-2-english`
- Confidence threshold: 0.6

### Topic Classification

- Model: `facebook/bart-large-mnli`
- Method: Zero-shot multi-label classification
- Threshold: 0.35
- Categories: harga, layanan, produk, pengiriman, lokasi, kualitas, after-sales

### Entity Extraction

- Service: IBM Watson NLU
- Features: entities, keywords, categories
- Language support: 12+ languages

### Insights & Recommendations

- Model: IBM Granite 3.3-8B Instruct (via Replicate)
- Output: Summary, refined topics, urgency level, action recommendations

## Webhook Events

Sistem dapat mengirim webhook untuk events berikut:

### feedback.analyzed

Dipicu ketika analisis feedback selesai.

```json
{
  "event": "feedback.analyzed",
  "data": {
    "feedback_id": "uuid",
    "project_id": "uuid",
    "sentiment": "positive",
    "urgency": "medium"
  }
}
```

### automation.triggered

Dipicu ketika automation job dibuat.

```json
{
  "event": "automation.triggered",
  "data": {
    "job_id": "uuid",
    "feedback_id": "uuid",
    "kind": "ticket"
  }
}
```

## SDKs & Examples

### cURL Examples

**Login:**

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "member@cfd.app", "password": "member12345"}'
```

**Create Feedback:**

```bash
curl -X POST "http://localhost:8000/api/feedbacks?project_id=PROJECT_ID" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "Great service!", "source": "manual"}'
```

**Analyze Feedback:**

```bash
curl -X POST http://localhost:8000/api/feedbacks/FEEDBACK_ID/analyze \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"feedback_id": "FEEDBACK_ID"}'
```

### Python Example

```python
import requests

# Login
login_response = requests.post(
    "http://localhost:8000/api/auth/login",
    json={"email": "member@cfd.app", "password": "member12345"}
)
token = login_response.json()["data"]["access_token"]

# Headers with auth
headers = {"Authorization": f"Bearer {token}"}

# Create feedback
feedback_response = requests.post(
    "http://localhost:8000/api/feedbacks",
    params={"project_id": "PROJECT_ID"},
    headers=headers,
    json={
        "content": "Pelayanan sangat memuaskan!",
        "source": "manual",
        "language": "id"
    }
)

feedback_id = feedback_response.json()["data"]["id"]

# Analyze feedback
analysis_response = requests.post(
    f"http://localhost:8000/api/feedbacks/{feedback_id}/analyze",
    headers=headers,
    json={"feedback_id": feedback_id}
)

print(analysis_response.json())
```

### JavaScript/Node.js Example

```javascript
const API_BASE = "http://localhost:8000";

// Login function
async function login(email, password) {
  const response = await fetch(`${API_BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  const data = await response.json();
  return data.data.access_token;
}

// Create and analyze feedback
async function createAndAnalyzeFeedback(token, projectId, content) {
  // Create feedback
  const feedbackResponse = await fetch(
    `${API_BASE}/api/feedbacks?project_id=${projectId}`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        content,
        source: "api",
        language: "auto",
      }),
    }
  );

  const feedback = await feedbackResponse.json();
  const feedbackId = feedback.data.id;

  // Analyze feedback
  const analysisResponse = await fetch(
    `${API_BASE}/api/feedbacks/${feedbackId}/analyze`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ feedback_id: feedbackId }),
    }
  );

  return await analysisResponse.json();
}

// Usage
(async () => {
  const token = await login("member@cfd.app", "member12345");
  const result = await createAndAnalyzeFeedback(
    token,
    "PROJECT_ID",
    "The coffee here is amazing!"
  );
  console.log(result);
})();
```

## Monitoring & Observability

### Health Check

```bash
curl http://localhost:8000/health
```

### Metrics Endpoints

- `/metrics` - Prometheus metrics
- `/api/stats` - API usage statistics

### Logging

Logs tersedia via Docker:

```bash
docker-compose logs -f backend
```

## Security

### Headers

API menerapkan security headers:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security`
- `Content-Security-Policy`

### Input Validation

- Semua input divalidasi dengan Pydantic
- XSS protection
- SQL injection prevention via ORM

### Rate Limiting

Implementasi rate limiting per IP dan per user untuk mencegah abuse.

---

Untuk informasi lebih lanjut, kunjungi dokumentasi interaktif di `http://localhost:8000/docs`.
