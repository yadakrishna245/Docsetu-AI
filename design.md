# Docsethu-AI — Architecture & Design Decisions

> Living document. Updated as decisions are made or revised.
> Last updated: 2026-07-30

---

## 1. Stack Decision

| Choice | Technology | Justification |
|--------|-----------|---------------|
| Language | Python 3.11 | Mature ML/NLP ecosystem, FastAPI async performance |
| Framework | FastAPI | Auto OpenAPI docs, async, type-safe, Pydantic validation |
| Frontend | React 18 + Vite | Component ecosystem, fast HMR, Tailwind for rapid UI |
| Database (dev) | SQLite | Zero-config, single-file, perfect for local dev |
| Database (prod) | DynamoDB | Serverless, pay-per-request, scales with Lambda |
| OCR | Tesseract 5 | Open-source, Indic script support, community models |
| LLM | OpenAI GPT-4 / Gemini | Best accuracy for document understanding, switchable |
| Payments | Razorpay | Indian standard, UPI support, good docs |
| Deployment | AWS SAM (Lambda) | Zero idle cost, auto-scale, India region (ap-south-1) |
| Bot | whatsapp-web.js | Free, no business API costs for MVP validation |

### Architecture Pattern

**Decision: Monolith-first.**

Single FastAPI service handles all routes. Reason: team of 1-2, faster iteration, simpler debugging. Will decompose only when a specific service becomes a bottleneck (e.g., OCR processing saturating the main event loop).

Decomposition trigger: if any single concern exceeds 40% of total request latency consistently, extract it into a dedicated Lambda or background worker.

---

## 2. API Contract

FastAPI auto-generates OpenAPI 3.0 spec at `/openapi.json`. Swagger UI available at `/docs` in dev.

### Route Groups

| Group | Endpoints | Description |
|-------|-----------|-------------|
| `/api/auth` | 6 | Register, login, refresh, logout, forgot-password, reset-password |
| `/api/documents` | 7 | Upload, list, get, delete, download, status, reprocess |
| `/api/analysis` | 4 | Run analysis, get result, list history, compare versions |
| `/api/compliance` | 4 | Run check, get report, list reports, download PDF |
| `/api/payments` | 5 | Create order, verify, webhook, history, refund |
| `/api/admin` | 4 | Users list, usage stats, system health, toggle features |

### Key Conventions

- All responses wrapped in `{ "success": bool, "data": ..., "error": ... }`
- Pagination: `?page=1&limit=20` (default limit 20, max 100)
- Auth: Bearer token in `Authorization` header
- File uploads: `multipart/form-data`, max 50MB
- Rate limiting: 100 req/min per user (auth routes: 10 req/min)

---

## 3. Data Model (ER Diagram)

### Relationships

```
User 1:N Document
Document 1:N Analysis
Document 1:N ComplianceReport
User 1:N Subscription
User 1:N Payment
Subscription 1:1 Payment
```

### Entity Definitions

```
┌─────────────────────────────────┐
│ User                            │
├─────────────────────────────────┤
│ id          : UUID (PK)        │
│ email       : str (unique)     │
│ password    : str (bcrypt)     │
│ name        : str              │
│ role        : enum(user,admin) │
│ is_active   : bool             │
│ created_at  : datetime         │
│ updated_at  : datetime         │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ Document                        │
├─────────────────────────────────┤
│ id          : UUID (PK)        │
│ user_id     : UUID (FK->User)  │
│ filename    : str              │
│ file_type   : enum(pdf,img,doc)│
│ s3_key      : str              │
│ status      : enum(pending,    │
│               processing,done, │
│               failed)          │
│ ocr_text    : text (encrypted) │
│ page_count  : int              │
│ uploaded_at : datetime         │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ Analysis                        │
├─────────────────────────────────┤
│ id          : UUID (PK)        │
│ document_id : UUID (FK->Doc)   │
│ type        : str              │
│ result_json : JSON             │
│ llm_model   : str             │
│ tokens_used : int              │
│ created_at  : datetime         │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ ComplianceReport                │
├─────────────────────────────────┤
│ id          : UUID (PK)        │
│ document_id : UUID (FK->Doc)   │
│ rule_set    : str              │
│ passed      : bool             │
│ findings    : JSON             │
│ created_at  : datetime         │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ Subscription                    │
├─────────────────────────────────┤
│ id          : UUID (PK)        │
│ user_id     : UUID (FK->User)  │
│ plan        : enum(free,pro,biz)│
│ status      : enum(active,     │
│               cancelled,expired)│
│ starts_at   : datetime         │
│ expires_at  : datetime         │
│ payment_id  : UUID (FK->Pay)   │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ Payment                         │
├─────────────────────────────────┤
│ id          : UUID (PK)        │
│ user_id     : UUID (FK->User)  │
│ razorpay_id : str              │
│ amount      : int (paise)      │
│ currency    : str (INR)        │
│ status      : enum(created,    │
│               captured,failed)  │
│ created_at  : datetime         │
└─────────────────────────────────┘
```

---

## 4. Sequence Diagrams

### a) Document Upload + Async Processing

```
Client -> API: POST /api/documents/upload (multipart)
API -> API: Validate file type & size
API -> S3: Upload raw file
API -> DB: Create Document (status=pending)
API -> Client: 202 Accepted { document_id }
API -> BackgroundWorker: Enqueue OCR task
BackgroundWorker -> S3: Download file
BackgroundWorker -> Tesseract: Extract text (+ language detect)
BackgroundWorker -> DB: Update Document (status=done, ocr_text)
BackgroundWorker -> DB: Update page_count
Client -> API: GET /api/documents/{id}/status (polling)
API -> Client: 200 { status: "done" }
```

### b) Compliance Check Flow

```
Client -> API: POST /api/compliance/check { document_id, rule_set }
API -> DB: Fetch Document.ocr_text
API -> LLM: Send text + compliance prompt
LLM -> API: Structured findings JSON
API -> DB: Create ComplianceReport
API -> Client: 200 { report_id, passed, findings[] }
Client -> API: GET /api/compliance/{report_id}/pdf
API -> PDFGenerator: Render report
API -> Client: 200 (PDF stream)
```

### c) Razorpay Payment Flow

```
Client -> API: POST /api/payments/create-order { plan }
API -> Razorpay: Create Order (amount, currency)
Razorpay -> API: { order_id }
API -> DB: Create Payment (status=created)
API -> Client: 200 { order_id, key_id }
Client -> Razorpay: Open checkout (client-side)
User -> Razorpay: Complete payment (UPI/Card)
Razorpay -> Client: { payment_id, signature }
Client -> API: POST /api/payments/verify { payment_id, signature }
API -> API: Verify HMAC signature
API -> DB: Update Payment (status=captured)
API -> DB: Create/Extend Subscription
API -> Client: 200 { subscription active }
Razorpay -> API: POST /api/payments/webhook (async confirmation)
API -> API: Verify webhook signature, reconcile
```

### d) WhatsApp Bot Document Flow

```
User -> WhatsApp: Send document (PDF/image)
WhatsApp -> Bot: Message event (media)
Bot -> Bot: Download media to temp
Bot -> API: POST /api/documents/upload (service auth)
API -> Bot: 202 { document_id }
Bot -> API: Poll GET /api/documents/{id}/status
API -> Bot: 200 { status: "done" }
Bot -> API: POST /api/analysis/run { document_id }
API -> Bot: 200 { summary, key_findings }
Bot -> WhatsApp: Reply with formatted summary
Bot -> Bot: Cleanup temp file
```

---

## 5. Third-Party Dependencies & Fallbacks

| Dependency | Used For | Fallback if Down | Detection |
|-----------|----------|------------------|-----------|
| OpenAI API | LLM analysis | Switch to Gemini (config toggle) | 5xx or timeout > 30s |
| Tesseract | OCR | PyPDF2 text extraction (non-scanned PDFs only) | Process exit code != 0 |
| Razorpay | Payments | Manual invoicing, service continues read-only | Webhook health check |
| SMTP (SES) | Emails | Log to console, queue for retry (max 3 attempts) | Connection refused |
| S3 | File storage | Local filesystem (dev only, not for prod) | AWS SDK exceptions |
| DynamoDB | Persistence | SQLite fallback (dev only) | Connection timeout |

### Retry Policy

- HTTP calls: 3 retries with exponential backoff (1s, 2s, 4s)
- Background tasks: 2 retries, then mark as `failed` and alert admin
- Payments: Never auto-retry charges. Log and notify.

---

## 6. Security Architecture

### Authentication & Authorization

- JWT access tokens: 60-minute expiry, RS256 signing
- Refresh tokens: 7-day expiry, stored hashed in DB, single-use
- Password hashing: bcrypt with cost factor 12
- RBAC: `user` and `admin` roles enforced at route decorator level
- Session invalidation: logout revokes all refresh tokens for user

### File Upload Security

- Allowed types: PDF, PNG, JPG, JPEG, TIFF, DOCX
- Max size: 50MB (enforced at API Gateway + application layer)
- Content-type validation: magic bytes check, not just extension
- Virus scan: ClamAV integration (roadmap, post-MVP)
- Storage: S3 with server-side encryption (AES-256)

### Secrets Management

| Environment | Method |
|-------------|--------|
| Development | `.env` file (gitignored, `.env.example` committed) |
| Production | AWS SSM Parameter Store (SecureString) |

### Network Security

- AWS WAF on API Gateway (prod): rate limiting, SQL injection rules
- CORS: whitelist frontend domain only
- HTTPS enforced (CloudFront + ACM cert)
- No direct DB access from internet (VPC private subnet)

### PII Handling

- Document OCR text stored encrypted at rest (S3 SSE + DynamoDB encryption)
- Aadhaar numbers: always masked in API responses (`XXXX-XXXX-1234`)
- PAN numbers: masked except last 4 characters
- Logs: PII fields redacted before writing to CloudWatch
- Data retention: documents auto-deleted after 90 days (configurable per plan)

---

## 7. Open Questions / Decisions Pending

- [ ] Cold start optimization: Lambda SnapStart vs provisioned concurrency?
- [ ] Multi-language OCR: Tamil/Hindi models — custom trained or community?
- [ ] WhatsApp Business API migration timeline (post-MVP, when > 100 users)
- [ ] Caching strategy: Redis vs DynamoDB DAX for frequent reads?

---

*This document is the source of truth for architecture decisions. Update it before or immediately after making changes.*
