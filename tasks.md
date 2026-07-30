# Tasks - DocSethu AI

> Kiro-compatible task breakdown linked to requirements.
> ✅ = Done | 🚧 = In Progress | 🗺️ = Roadmap

---

## Phase 1: Core Platform (DONE ✅)

- [x] 1. Set up FastAPI project structure
  - Created app/, config/, db/, models/, routers/, services/ directories
  - Added environment-based config with Pydantic Settings
  - Set up SQLAlchemy + Alembic for migrations
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. Implement user authentication
  - Register endpoint with email + password hashing (bcrypt)
  - Login endpoint returning JWT access + refresh tokens
  - Get profile endpoint with token validation
  - Token refresh flow
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 3. Implement document upload with file validation
  - Accept PDF, JPG, PNG, TIFF uploads
  - Validate file size (max 20MB), MIME type, and extension
  - Store files in S3-compatible storage with unique keys
  - Return document metadata on successful upload
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 4. Build OCR service (Tesseract + PyPDF2 fallback)
  - Tesseract OCR for scanned images and image-based PDFs
  - PyPDF2 text extraction for native/digital PDFs
  - Auto-detect document type and route to correct extractor
  - Support Hindi + English (bilingual OCR)
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 5. Implement entity extraction (regex + LLM)
  - Regex patterns for PAN, GSTIN, Aadhaar, dates, amounts
  - LLM-based extraction for unstructured fields (names, addresses)
  - Confidence scoring per extracted entity
  - Structured JSON output with field mapping
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 6. Build compliance engine (rule-based + LLM hybrid)
  - Rule-based checks: GST rate validation, PAN format, date ranges
  - LLM-based checks: clause interpretation, anomaly flagging
  - Severity levels (critical, warning, info)
  - Compliance score calculation (0-100%)
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 7. Create React frontend
  - Dashboard with document stats and recent activity
  - Upload page with drag-and-drop and progress indicator
  - Documents list with search, filter, and pagination
  - Compliance view with issue breakdown and scores
  - Analytics page with charts (Recharts)
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 8. Build WhatsApp bot
  - Document upload via WhatsApp media messages
  - Entity extraction triggered by command
  - Compliance check results sent as formatted messages
  - Q&A mode for asking questions about uploaded documents
  - Session management per phone number
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 9. Implement document Q&A, comparison, summarization
  - Q&A: Ask natural language questions about document content
  - Comparison: Side-by-side diff of two documents with highlights
  - Summarization: Generate concise summaries with key points
  - Context-aware responses using document embeddings
  - _Requirements: 9.1, 9.2, 9.3, 9.4_

---

## Phase 2: Production Hardening (DONE ✅)

- [x] 10. Add Docker Compose setup
  - Multi-container: API, frontend, PostgreSQL, Redis, worker
  - Environment variable management via .env
  - Health checks and restart policies
  - Volume mounts for persistent data
  - _Requirements: 10.1, 10.2, 10.3_

- [x] 11. Add async background processing for uploads
  - Celery workers with Redis broker
  - OCR + extraction runs as background task
  - Status polling endpoint for processing state
  - Retry logic with exponential backoff
  - _Requirements: 11.1, 11.2, 11.3, 11.4_

- [x] 12. Add email verification + password reset
  - Email verification on registration (token-based)
  - Password reset via email with expiring token
  - Resend verification email endpoint
  - _Requirements: 12.1, 12.2, 12.3_

- [x] 13. Add RBAC (admin/analyst/viewer)
  - Three roles: admin (full access), analyst (read/write), viewer (read-only)
  - Role-based route guards on backend
  - Frontend UI adapts to user role
  - Admin can manage users and assign roles
  - _Requirements: 13.1, 13.2, 13.3, 13.4_

- [x] 14. Add batch upload (up to 20 files)
  - Multi-file upload endpoint accepting up to 20 files
  - Individual progress tracking per file
  - Partial success handling (some files fail, others succeed)
  - Batch status summary
  - _Requirements: 14.1, 14.2, 14.3_

- [x] 15. Add PDF export for compliance reports
  - Generate PDF reports with compliance scores and issues
  - Include extracted entities and document metadata
  - Branded header/footer with timestamp
  - Download endpoint returning PDF binary
  - _Requirements: 15.1, 15.2, 15.3_

- [x] 16. Add Razorpay payment integration
  - Order creation endpoint
  - Payment verification with signature validation
  - Webhook handler for async payment events
  - Subscription plan management (free/pro/enterprise)
  - _Requirements: 16.1, 16.2, 16.3, 16.4_

- [x] 17. Make WhatsApp bot state persistent
  - Store conversation state in Redis with TTL
  - Survive server restarts without losing user context
  - Session cleanup for inactive users (24hr TTL)
  - _Requirements: 17.1, 17.2, 17.3_

- [x] 18. Write integration tests
  - Auth flow tests (register → verify → login → refresh)
  - Upload + processing pipeline tests
  - Compliance engine tests with known documents
  - API contract tests for all endpoints
  - _Requirements: 18.1, 18.2, 18.3, 18.4_

- [x] 19. AWS SAM serverless deployment setup
  - SAM template with Lambda functions + API Gateway
  - S3 bucket for document storage
  - DynamoDB or RDS for metadata
  - IAM roles with least-privilege policies
  - _Requirements: 19.1, 19.2, 19.3, 19.4_

- [x] 20. GitHub Actions CI/CD
  - Lint + test on every PR
  - Build Docker images on merge to main
  - Deploy to staging on merge, production on tag
  - Secret management via GitHub Secrets
  - _Requirements: 20.1, 20.2, 20.3, 20.4_

- [x] 21. Rewrite documentation
  - Honest README with actual feature status
  - API documentation (OpenAPI/Swagger auto-generated)
  - Architecture decision records (ADRs)
  - Deployment guide (Docker, AWS, local dev)
  - _Requirements: 21.1, 21.2, 21.3, 21.4_

---

## Phase 3: Production Readiness (IN PROGRESS 🚧)

- [x] 22. Add PR template and Dependabot
  - PR template with checklist (tests, docs, breaking changes)
  - Dependabot config for Python and npm dependencies
  - Auto-merge for patch-level security updates
  - _Requirements: 22.1, 22.2, 22.3_

- [x] 23. Create Kiro-compatible specs
  - requirements.md with numbered functional requirements
  - design.md with architecture decisions and component diagrams
  - tasks.md (this file) with phased task breakdown
  - _Requirements: 23.1, 23.2, 23.3_

- [x] 24. Create production checklist
  - Pre-launch checklist covering security, performance, monitoring
  - Runbook for common operational tasks
  - Incident response playbook template
  - _Requirements: 24.1, 24.2, 24.3_

- [x] 25. Add linting (ruff for Python, ESLint for frontend)
  - Ruff configured with pyproject.toml (replaces flake8 + isort + black)
  - ESLint + Prettier for React frontend
  - Pre-commit hooks for both
  - CI fails on lint errors
  - _Requirements: 25.1, 25.2, 25.3, 25.4_

- [x] 26. Add rate limiting to API (slowapi)
  - slowapi middleware on all public endpoints
  - Configurable limits per endpoint (e.g., 10/min for upload, 100/min for read)
  - Custom error response on limit exceeded (429)
  - IP-based and user-based limiting
  - _Requirements: 26.1, 26.2, 26.3, 26.4_

- [ ] 27. Add input validation audit (OWASP Top 10 pass)
  - Audit all request bodies for injection vulnerabilities
  - Add Pydantic validators with strict type coercion
  - Sanitize file names and user-provided strings
  - SQL injection, XSS, path traversal checks
  - _Requirements: 27.1, 27.2, 27.3, 27.4_

- [ ] 28. Add audit logging on auth events and privileged actions
  - Log all login attempts (success + failure) with IP and timestamp
  - Log role changes, user creation/deletion by admins
  - Log document deletion and compliance overrides
  - Structured log format (JSON) for aggregation
  - _Requirements: 28.1, 28.2, 28.3, 28.4_

- [ ] 29. Load test at 3x expected peak (3000 docs/day)
  - Locust or k6 test scripts simulating 3000 docs/day throughput
  - Measure P50, P95, P99 latency under load
  - Identify bottlenecks (DB, OCR, LLM calls)
  - Document capacity limits and scaling recommendations
  - _Requirements: 29.1, 29.2, 29.3, 29.4_

- [ ] 30. Security pen test / automated DAST scan
  - Run OWASP ZAP or Nuclei against staging environment
  - Fix all critical and high severity findings
  - Document accepted risks for medium/low findings
  - Schedule recurring monthly scans
  - _Requirements: 30.1, 30.2, 30.3, 30.4_

- [ ] 31. Create privacy policy page (DPDP Act compliance)
  - Draft privacy policy aligned with India's DPDP Act 2023
  - Data collection, processing, and retention disclosures
  - User rights: access, correction, erasure requests
  - Cookie consent and third-party data sharing notice
  - _Requirements: 31.1, 31.2, 31.3, 31.4_

- [ ] 32. Set up uptime monitoring (status page)
  - Uptime monitoring for API, frontend, and WhatsApp bot
  - Public status page (e.g., Betteruptime, Upptime)
  - Alerting via Slack/email on downtime
  - SLA tracking (target: 99.5% uptime)
  - _Requirements: 32.1, 32.2, 32.3, 32.4_

---

## Phase 4: Growth Features (ROADMAP 🗺️)

- [ ] 33. Telegram bot
  - Mirror WhatsApp bot functionality on Telegram
  - Inline keyboard for navigation
  - File upload and processing via Telegram media
  - _Requirements: 33.1, 33.2, 33.3_

- [ ] 34. Add more Indian languages (Bengali, Gujarati, Marathi)
  - Train/configure Tesseract for Bengali, Gujarati, Marathi scripts
  - LLM prompts adapted for multilingual entity extraction
  - UI language selector for regional language support
  - _Requirements: 34.1, 34.2, 34.3_

- [ ] 35. Template marketplace (user-generated)
  - Users can create and share extraction templates
  - Template rating and review system
  - Marketplace search and category filtering
  - Revenue share model for template creators
  - _Requirements: 35.1, 35.2, 35.3, 35.4_

- [ ] 36. Real-time regulatory update feed
  - Scrape/subscribe to Indian regulatory gazette updates
  - Auto-update compliance rules when regulations change
  - Notify affected users of rule changes
  - Changelog of compliance rule versions
  - _Requirements: 36.1, 36.2, 36.3, 36.4_

- [ ] 37. Tally / Zoho Books integration
  - Export extracted invoice data to Tally format
  - Zoho Books API integration for auto-reconciliation
  - Field mapping configuration per accounting system
  - _Requirements: 37.1, 37.2, 37.3_

- [ ] 38. Mobile app (React Native)
  - Camera capture for instant document scanning
  - Push notifications for processing completion
  - Offline mode with sync on reconnect
  - Biometric authentication
  - _Requirements: 38.1, 38.2, 38.3, 38.4_

- [ ] 39. Multi-tenant (organization accounts)
  - Organization-level data isolation
  - Team management (invite, remove, role assignment)
  - Shared document folders within organization
  - Organization-level billing and usage analytics
  - _Requirements: 39.1, 39.2, 39.3, 39.4_

- [ ] 40. DigiLocker / GST Portal API integration
  - DigiLocker API for verified document fetch
  - GST Portal integration for return filing verification
  - Auto-populate entity data from government sources
  - Consent-based data access flow
  - _Requirements: 40.1, 40.2, 40.3, 40.4_

---

## Summary

| Phase | Tasks | Done | Remaining |
|-------|-------|------|-----------|
| Phase 1: Core Platform | 9 | 9 | 0 |
| Phase 2: Production Hardening | 12 | 12 | 0 |
| Phase 3: Production Readiness | 11 | 5 | 6 |
| Phase 4: Growth Features | 8 | 0 | 8 |
| **Total** | **40** | **26** | **14** |

---

_Last updated: 2026-07-30_
_Generated for Kiro spec compatibility_
