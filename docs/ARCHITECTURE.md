# Docsethu-AI — Architecture Documentation

> Last updated: 2026-07-30

This document describes the **actual** architecture of Docsethu-AI as built and deployed.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python 3.11) — single monolithic service |
| Database | SQLite (local dev) / DynamoDB (AWS Lambda prod) |
| Frontend | React 18 + Vite + Tailwind CSS |
| WhatsApp Bot | Node.js + whatsapp-web.js (separate service) |
| OCR | Tesseract 5 (eng, hin, tam, tel, kan) + PyPDF2 |
| LLM | OpenAI GPT-4 OR Google Gemini (configurable) |
| Vector Store | ChromaDB (local persistence) |
| Background Tasks | FastAPI BackgroundTasks |
| PDF Generation | ReportLab |
| Payments | Razorpay |
| Email | aiosmtplib (async SMTP) |
| Auth | JWT (python-jose) + bcrypt |
| Deployment | Docker Compose (dev) / AWS SAM Lambda (prod) |
| CI/CD | GitHub Actions |
| Caching | Redis (Docker) — session store in Docker setup |

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                                 │
│                                                                     │
│   ┌─────────────────────┐       ┌─────────────────────────────┐    │
│   │   React SPA          │       │   WhatsApp Bot (Node.js)    │    │
│   │   Vite + Tailwind    │       │   whatsapp-web.js           │    │
│   └─────────┬───────────┘       └──────────────┬──────────────┘    │
└─────────────┼──────────────────────────────────┼────────────────────┘
              │ HTTP/REST                         │ HTTP/REST
              ▼                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         API LAYER                                    │
│                                                                     │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │              FastAPI (Single Service)                         │   │
│   │                                                             │   │
│   │   /api/auth/*    /api/documents/*    /api/analysis/*        │   │
│   │   /api/compliance/*   /api/payments/*   /api/admin/*        │   │
│   └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────────┐
              ▼               ▼                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      PROCESSING LAYER                                │
│                                                                     │
│   ┌────────────┐  ┌────────────┐  ┌──────────────────────┐         │
│   │ OCR Service│  │LLM Service │  │ Compliance Engine    │         │
│   │ Tesseract 5│  │ GPT-4 /    │  │ Rules + LLM hybrid  │         │
│   │ + PyPDF2   │  │ Gemini     │  └──────────────────────┘         │
│   └────────────┘  └────────────┘                                    │
│   ┌────────────┐  ┌────────────┐  ┌──────────────────────┐         │
│   │ Validator  │  │PDF Service │  │ Payment Service      │         │
│   │            │  │ ReportLab  │  │ Razorpay             │         │
│   └────────────┘  └────────────┘  └──────────────────────┘         │
│   ┌──────────────────┐                                              │
│   │ Email Service    │                                              │
│   │ aiosmtplib       │                                              │
│   └──────────────────┘                                              │
└─────────────────────────────────────────────────────────────────────┘
              │               │                   │
              ▼               ▼                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                                   │
│                                                                     │
│   ┌────────────────┐  ┌──────────────────┐  ┌────────────────┐     │
│   │ SQLite (dev)   │  │ File Storage     │  │ ChromaDB       │     │
│   │ DynamoDB (prod)│  │ Local / S3       │  │ Vector Store   │     │
│   └────────────────┘  └──────────────────┘  └────────────────┘     │
└─────────────────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      EXTERNAL SERVICES                               │
│                                                                     │
│   ┌────────────────┐  ┌────────────────┐  ┌────────────────┐       │
│   │ OpenAI /       │  │ Razorpay API   │  │ SMTP Server    │       │
│   │ Gemini API     │  │                │  │                │       │
│   └────────────────┘  └────────────────┘  └────────────────┘       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Key Design Decisions

### 1. Monolith-First

Single FastAPI application. No microservices, no service mesh, no API gateway.
One process handles all requests. Simpler to deploy, debug, and reason about.

### 2. SQLite for Dev, DynamoDB for Prod

- **Local dev**: SQLite — zero config, no database server needed, just a file.
- **Production**: DynamoDB — serverless, scales with Lambda, no connection pooling headaches.

### 3. Background Tasks for File Processing

Large documents (multi-page PDFs, scanned images) process asynchronously:
- Upload returns `202 Accepted` immediately
- `FastAPI.BackgroundTasks` handles OCR + text extraction
- Client polls `/api/documents/{id}/status` until `processed`

### 4. Dual LLM Support

OpenAI GPT-4 and Google Gemini are both supported. Configurable via environment variable:
```
LLM_PROVIDER=openai   # or "gemini"
```
Abstraction layer normalizes requests/responses across providers.

### 5. Rule-Based + LLM Hybrid Compliance

- **Fast path**: Regex and rule-based checks catch common violations instantly.
- **Strict mode**: LLM analyzes document context for nuanced compliance issues.
- Cost optimization: LLM calls are expensive, so rules run first.

### 6. Simple RBAC

Three roles with linear hierarchy:
```
admin > analyst > viewer
```
No complex permission matrices. Role checked via decorator on each route.

### 7. File-Based Bot Persistence

WhatsApp bot stores session state in a local JSON file. No Redis dependency for the bot service. Keeps the bot deployable as a standalone container.

---

## Data Models

### User
```
id              UUID (primary key)
email           string (unique)
username        string (unique)
password_hash   string (bcrypt)
role            enum: admin | analyst | viewer
is_active       boolean
is_verified     boolean
org             string (nullable)
created_at      datetime
updated_at      datetime
```

### Document
```
id              UUID (primary key)
filename        string
file_path       string (local path or S3 key)
owner_id        UUID (FK → User)
batch_id        UUID (nullable, for bulk uploads)
status          enum: uploaded | processing | processed | failed
extracted_text  text (nullable)
language        string (detected or specified)
metadata        JSON
created_at      datetime
```

### Analysis
```
id              UUID (primary key)
document_id     UUID (FK → Document)
type            enum: entity_extraction | summarization | qa | comparison
entities        JSON (nullable)
result_json     JSON
status          enum: pending | completed | failed
created_at      datetime
```

### ComplianceReport
```
id              UUID (primary key)
document_id     UUID (FK → Document)
overall_status  enum: compliant | non_compliant | partial
score           float (0.0 – 1.0)
violations      JSON array [{rule, severity, description, location}]
regulations     JSON array (list of regulations checked)
created_at      datetime
```

### Subscription
```
id              UUID (primary key)
user_id         UUID (FK → User)
plan_id         string
razorpay_order_id   string
status          enum: active | expired | cancelled
starts_at       datetime
expires_at      datetime
```

### Payment
```
id              UUID (primary key)
user_id         UUID (FK → User)
razorpay_payment_id   string
amount          integer (paise)
currency        string (default: INR)
status          enum: created | captured | failed | refunded
created_at      datetime
```

---

## Processing Pipeline

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────────┐
│  Upload  │───▶│  Save to │───▶│ Return   │───▶│ Background:  │
│  (POST)  │    │  disk/S3 │    │ 202      │    │ OCR + Extract│
└──────────┘    └──────────┘    └──────────┘    └──────┬───────┘
                                                       │
                                                       ▼
                                                ┌──────────────┐
                                                │ Status:      │
                                                │ "processed"  │
                                                └──────┬───────┘
                                                       │
                         ┌─────────────────────────────┼─────────────────┐
                         ▼              ▼              ▼            ▼     ▼
                  ┌───────────┐  ┌───────────┐  ┌──────────┐  ┌─────┐ ┌─────┐
                  │ Extract   │  │ Compliance│  │ Q&A /    │  │Sum- │ │Export│
                  │ Entities  │  │ Check     │  │ Chat     │  │mary │ │ PDF │
                  └───────────┘  └───────────┘  └──────────┘  └─────┘ └─────┘
```

**Steps:**
1. User uploads document (PDF, image, text)
2. File saved to local storage (dev) or S3 (prod)
3. API returns `202 Accepted` with document ID
4. Background task: Tesseract OCR (for images/scanned PDFs) or PyPDF2 (for digital PDFs)
5. Extracted text stored in database, status updated to `processed`
6. User can then trigger any analysis operation on the processed document

---

## Security

| Concern | Implementation |
|---------|---------------|
| Authentication | JWT tokens via `python-jose`, 60-minute expiry |
| Password Storage | bcrypt hashing (12 rounds) |
| Authorization | RBAC decorator on routes (admin/analyst/viewer) |
| CORS | Configured allowlist (not wildcard in prod) |
| File Validation | Type whitelist + max size (configurable, default 20MB) |
| Payment Webhooks | Razorpay signature verification (HMAC SHA256) |
| Secrets | Environment variables, never committed to repo |
| Rate Limiting | Basic rate limiting on auth endpoints |

---

## Deployment

### Local Development (Docker Compose)
```yaml
services:
  api:        # FastAPI app (port 8000)
  frontend:   # React dev server (port 5173)
  redis:      # Session cache
  bot:        # WhatsApp bot (Node.js)
```

### Production (AWS SAM)
```
API Gateway → Lambda (FastAPI via Mangum)
DynamoDB (data)
S3 (file storage)
CloudWatch (logs)
```

The WhatsApp bot runs as a separate EC2 instance or ECS task (needs persistent browser session for whatsapp-web.js).

---

## What This Project Is NOT

- ❌ Not microservices — it's a monolith
- ❌ No Kubernetes, no Istio, no Kong
- ❌ No PostgreSQL, no MongoDB, no Elasticsearch
- ❌ No blockchain
- ❌ No GraphQL federation
- ❌ No event sourcing or CQRS

It's a straightforward FastAPI app with a React frontend. Simple, honest, functional.
