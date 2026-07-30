# DocSethu AI - API Reference

Base URL: `http://localhost:8000` (dev) or your deployed URL. All bodies are JSON unless noted.

---

## Authentication & Authorization

Protected endpoints require: `Authorization: Bearer <jwt_token>`

Tokens expire after **60 minutes**. Public endpoints (no auth): `/health`, `/`, `/api/auth/register`, `/api/auth/login`, `/api/auth/verify-email`, `/api/auth/forgot-password`, `/api/auth/reset-password`, `/api/payments/plans`, `/api/payments/webhook`.

**Roles:** `viewer` (view own docs/reports) · `analyst` (upload, analyze, compliance) · `admin` (full access + user management)

---

## Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/` | API info |

---

## Auth (`/api/auth`)

### POST /api/auth/register

```json
// Request
{ "email": "user@example.com", "username": "jdoe", "password": "SecurePass123!", "full_name": "Jane Doe", "organization": "Acme Corp" }

// Response 201
{ "message": "Registration successful. Please verify your email.", "user_id": "uuid" }
```

### POST /api/auth/login

```json
// Request
{ "email": "user@example.com", "password": "SecurePass123!" }

// Response 200
{ "access_token": "eyJhbG...", "token_type": "bearer", "expires_in": 3600 }
```

### GET /api/auth/me

Returns the authenticated user's profile (user_id, email, username, full_name, organization, role, is_active).

### POST /api/auth/verify-email

```json
{ "token": "verification-token" }
```

### POST /api/auth/forgot-password

```json
{ "email": "user@example.com" }
```

### POST /api/auth/reset-password

```json
{ "token": "reset-token", "new_password": "NewPass456!" }
```

---

## Documents (`/api/documents`)

### POST /api/documents/upload

Upload a single document. **Role:** analyst+. **Content-Type:** `multipart/form-data`

Field: `file` — PDF, PNG, JPG, JPEG, TIFF, or BMP. Max 50MB.

```json
// Response 202
{ "document_id": "uuid", "filename": "invoice.pdf", "status": "processing", "message": "Document accepted for processing." }
```

> Processing is async. Poll `GET /api/documents/{doc_id}/status` for completion.

### POST /api/documents/batch-upload

Upload up to 20 files. **Role:** analyst+. **Content-Type:** `multipart/form-data`

```json
// Response 202
{
  "batch_id": "uuid",
  "accepted": [{ "document_id": "uuid-1", "filename": "doc1.pdf" }],
  "rejected": [{ "filename": "huge.pdf", "reason": "File exceeds 50MB limit" }]
}
```

### GET /api/documents/

List user's documents. **Query params:** `page` (default 1), `page_size` (default 20), `status_filter`.

```json
// Response 200
{ "documents": [{ "document_id": "uuid", "filename": "invoice.pdf", "status": "completed", "uploaded_at": "2026-07-30T08:00:00Z" }], "page": 1, "page_size": 20, "total": 42 }
```

### GET /api/documents/{doc_id}

Get full document details.

### GET /api/documents/{doc_id}/status

```json
// Response 200
{ "document_id": "uuid", "status": "completed", "progress": 100, "started_at": "...", "completed_at": "..." }
```

### GET /api/documents/batch/{batch_id}/status

```json
// Response 200
{ "batch_id": "uuid", "total": 5, "completed": 4, "processing": 1, "failed": 0 }
```

### DELETE /api/documents/{doc_id}

Deletes document and associated data. Returns `{ "message": "Document deleted." }`.

---

## Analysis (`/api/analysis`)

### POST /api/analysis/extract/{doc_id}

Extract entities: PAN, GST, Aadhaar numbers, dates, amounts.

```json
// Response 200
{
  "document_id": "uuid",
  "entities": {
    "pan_numbers": ["ABCDE1234F"],
    "gst_numbers": ["29ABCDE1234F1Z5"],
    "aadhaar_numbers": ["XXXX-XXXX-1234"],
    "dates": ["2026-01-15"],
    "amounts": ["₹1,50,000"]
  }
}
```

### POST /api/analysis/qa

```json
// Request
{ "document_id": "uuid", "question": "What is the total amount?", "context_window": 3 }

// Response 200
{ "answer": "The total is ₹1,50,000.", "confidence": 0.92, "source_pages": [1] }
```

### POST /api/analysis/compare

```json
// Request
{ "document_id_1": "uuid-1", "document_id_2": "uuid-2" }

// Response 200
{ "similarities": ["Same vendor."], "differences": ["Amount differs."], "summary": "..." }
```

### POST /api/analysis/summarize/{doc_id}

```json
// Response 200
{ "document_id": "uuid", "summary": "Tax invoice from Acme Corp for ₹1,50,000 inclusive of 18% GST." }
```

---

## Compliance (`/api/compliance`)

### POST /api/compliance/check/{doc_id}

Run compliance check. Optional body:

```json
{ "regulations": ["GST", "Income Tax"], "strict_mode": true }
```

```json
// Response 200
{
  "document_id": "uuid",
  "compliant": false,
  "issues": [{ "rule": "GST-001", "severity": "high", "description": "Invalid GST format.", "location": "Page 1" }],
  "checked_at": "2026-07-30T08:05:00Z"
}
```

### GET /api/compliance/rules

List compliance rules. Optional query param: `category` (e.g., `GST`, `Income Tax`, `KYC`).

### GET /api/compliance/report/{doc_id}

Get latest compliance report for a document.

### GET /api/compliance/report/{doc_id}/pdf

Download compliance report as PDF. Response: binary with `Content-Type: application/pdf`.

---

## Payments (`/api/payments`)

### GET /api/payments/plans

**No auth required.** Lists subscription plans.

```json
// Response 200
{ "plans": [{ "plan_id": "basic", "name": "Basic", "price": 999, "currency": "INR", "features": ["50 docs/month", "Entity extraction"] }] }
```

### POST /api/payments/create-order

```json
// Request
{ "plan_id": "basic" }

// Response 200
{ "order_id": "order_ABC123", "amount": 999, "currency": "INR", "razorpay_key_id": "rzp_live_xxx" }
```

### POST /api/payments/verify

```json
// Request
{ "order_id": "order_ABC123", "payment_id": "pay_XYZ789", "signature": "razorpay-signature" }

// Response 200
{ "verified": true, "subscription": { "plan": "basic", "valid_until": "2026-08-30T08:00:00Z" } }
```

### GET /api/payments/subscription

Get current user's subscription status.

### POST /api/payments/webhook

Razorpay webhook. No auth — verifies Razorpay webhook signature internally.

---

## Admin (`/api/admin`)

All endpoints require `admin` role.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/admin/users` | List all users |
| PATCH | `/api/admin/users/{user_id}/role` | Change role (`{ "role": "analyst" }`) |
| PATCH | `/api/admin/users/{user_id}/status` | Activate/deactivate (`{ "is_active": false }`) |
| GET | `/api/admin/stats` | Platform statistics |

Valid roles: `admin`, `analyst`, `viewer`.

---

## Error Responses

```json
{ "detail": "Description of what went wrong." }
```

| Status | Meaning |
|--------|---------|
| 400 | Bad request / validation error |
| 401 | Missing or invalid token |
| 403 | Insufficient permissions |
| 404 | Resource not found |
| 413 | File too large (>50MB) |
| 422 | Unprocessable entity |
| 500 | Internal server error |

---

## Constraints

| Item | Value |
|------|-------|
| Supported files | PDF, PNG, JPG, JPEG, TIFF, BMP |
| Max file size | 50 MB |
| Batch upload limit | 20 files |
| Token expiration | 60 minutes |
| Processing | Async — poll status endpoint |
