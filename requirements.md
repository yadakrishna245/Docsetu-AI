# Requirements: DocSetu AI

## Project Charter

- **Project Name**: DocSetu AI
- **One-line Purpose**: AI-powered document compliance platform for Indian businesses
- **Primary Users**: Chartered Accountants (CAs), SME owners, compliance officers
- **Success Metric**: 100 paying subscribers within 6 months of launch
- **Hard Constraints**:
  - Must comply with DPDP Act 2023 (handling Indian PII)
  - Infrastructure cost under ₹50,000/month
- **Out of Scope**: Mobile app, Telegram bot, real-time regulatory feeds, multi-tenant white-label

---

## 1. Authentication & Authorization

### Requirement 1.1: User Registration
As a new user, I want to register with my email and password, so that I can access the DocSetu AI platform.

Acceptance Criteria:
- WHEN a user submits a valid email, password (min 8 chars, 1 uppercase, 1 number), and organization name THEN the system SHALL create an account with "pending_verification" status and send a verification email within 60 seconds.
- IF the email is already registered THEN the system SHALL reject registration with a 409 Conflict error and message "Email already in use."
- IF the password does not meet complexity requirements THEN the system SHALL return a 400 error listing the unmet criteria.

### Requirement 1.2: Email Verification
As a registered user, I want to verify my email address, so that I can activate my account.

Acceptance Criteria:
- WHEN a user clicks the verification link within 24 hours of registration THEN the system SHALL activate the account and redirect to the login page with a success message.
- IF the verification link is expired (>24 hours) THEN the system SHALL display an error and provide a "Resend Verification" button.
- WHEN a user requests a new verification email THEN the system SHALL invalidate previous links and send a fresh one.

### Requirement 1.3: User Login
As a registered user, I want to log in with my credentials, so that I can access my documents and compliance reports.

Acceptance Criteria:
- WHEN a user submits valid email and password THEN the system SHALL return a JWT access token (15 min expiry) and a refresh token (7 day expiry).
- IF credentials are invalid THEN the system SHALL return a 401 error without revealing whether the email or password was incorrect.
- IF a user fails login 5 times within 10 minutes THEN the system SHALL lock the account for 30 minutes and send a security alert email.

### Requirement 1.4: Password Reset
As a user who forgot their password, I want to reset it via email, so that I can regain access to my account.

Acceptance Criteria:
- WHEN a user requests a password reset THEN the system SHALL send a reset link (valid for 1 hour) to the registered email regardless of whether the email exists (to prevent enumeration).
- WHEN a user submits a new password via a valid reset link THEN the system SHALL update the password, invalidate all existing sessions, and confirm the change via email.

### Requirement 1.5: Role-Based Access Control
As an organization admin, I want to assign roles (Admin, CA, Viewer) to team members, so that I can control who can upload, analyze, and delete documents.

Acceptance Criteria:
- WHEN an Admin assigns a role to a user THEN the system SHALL update permissions immediately and reflect on the user's next API call.
- IF a user with "Viewer" role attempts to delete a document THEN the system SHALL return a 403 Forbidden error.
- IF a user with "CA" role uploads a document THEN the system SHALL allow it and assign ownership to that user.

---

## 2. Document Management

### Requirement 2.1: Single Document Upload
As a CA, I want to upload a single document (PDF, JPEG, PNG), so that I can process it for compliance checks.

Acceptance Criteria:
- WHEN a user uploads a file ≤ 25 MB in PDF, JPEG, or PNG format THEN the system SHALL store the file, return a document ID, and set status to "uploaded."
- IF the file exceeds 25 MB THEN the system SHALL reject the upload with a 413 error and message "File size exceeds 25 MB limit."
- IF the file format is not supported THEN the system SHALL return a 415 error listing accepted formats.

### Requirement 2.2: Batch Document Upload
As an SME owner, I want to upload up to 20 documents at once, so that I can process multiple invoices or filings together.

Acceptance Criteria:
- WHEN a user uploads a batch of 1–20 files (each ≤ 25 MB) THEN the system SHALL accept all valid files, return individual document IDs for each, and queue them for processing.
- IF any file in the batch is invalid THEN the system SHALL accept valid files and return per-file error details for rejected ones (partial success).
- WHEN batch upload completes THEN the system SHALL send an email notification with a summary of accepted/rejected files.

### Requirement 2.3: Document Listing & Filtering
As a compliance officer, I want to list and filter my documents by status, date, and type, so that I can quickly find relevant documents.

Acceptance Criteria:
- WHEN a user requests their document list THEN the system SHALL return paginated results (default 20 per page) sorted by upload date descending.
- WHEN a user filters by status (uploaded, processing, completed, failed) THEN the system SHALL return only matching documents.
- IF the user has "Viewer" role THEN the system SHALL show only documents shared with them, not all organization documents.

### Requirement 2.4: Document Status Polling
As a user, I want to check the processing status of my document, so that I know when OCR and analysis are complete.

Acceptance Criteria:
- WHEN a user polls the status endpoint with a document ID THEN the system SHALL return the current status (uploaded, ocr_processing, extracting, compliance_checking, completed, failed) and percentage progress.
- IF processing fails THEN the system SHALL set status to "failed" with a human-readable error reason.

### Requirement 2.5: Document Deletion
As a document owner, I want to delete my documents, so that I can comply with data retention preferences.

Acceptance Criteria:
- WHEN a document owner or Admin deletes a document THEN the system SHALL soft-delete the record, remove the file from storage within 24 hours, and return a 200 confirmation.
- IF a non-owner non-Admin attempts deletion THEN the system SHALL return a 403 Forbidden error.
- WHEN a document is deleted THEN the system SHALL also remove associated OCR text, extracted entities, and compliance reports.

---

## 3. OCR & Extraction

### Requirement 3.1: Multi-Language OCR
As a CA, I want the system to extract text from documents in English, Hindi, and regional languages, so that I can process vernacular invoices and government documents.

Acceptance Criteria:
- WHEN a document is queued for OCR THEN the system SHALL auto-detect the language(s) and extract text with ≥ 95% accuracy for printed English text and ≥ 90% for Hindi/Devanagari.
- WHEN OCR is complete THEN the system SHALL store the extracted text and make it searchable.
- IF OCR confidence is below 70% for any page THEN the system SHALL flag that page for manual review.

### Requirement 3.2: Entity Extraction
As a compliance officer, I want the system to extract PAN, Aadhaar, GSTIN, dates, and monetary amounts from documents, so that I can auto-populate compliance reports.

Acceptance Criteria:
- WHEN OCR text is available THEN the system SHALL extract and validate: PAN (format ABCDE1234F), Aadhaar (12 digits with Verhoeff checksum), GSTIN (15-char format), dates (DD/MM/YYYY and variants), and INR amounts.
- WHEN entities are extracted THEN the system SHALL store them as structured JSON linked to the document ID with confidence scores.
- IF Aadhaar numbers are detected THEN the system SHALL mask all but the last 4 digits in any user-facing display (DPDP Act compliance).

---

## 4. AI Analysis

### Requirement 4.1: Document Q&A
As a CA, I want to ask natural-language questions about an uploaded document, so that I can quickly find specific information without reading the entire document.

Acceptance Criteria:
- WHEN a user submits a question about a processed document THEN the system SHALL return an answer with source page references within 10 seconds.
- IF the answer cannot be determined from the document THEN the system SHALL respond with "The document does not contain information to answer this question" rather than hallucinating.
- WHEN answering THEN the system SHALL cite the exact text passage(s) used to derive the answer.

### Requirement 4.2: Document Summarization
As an SME owner, I want a plain-language summary of my uploaded document, so that I can understand legal/financial documents without expertise.

Acceptance Criteria:
- WHEN a user requests a summary of a processed document THEN the system SHALL generate a structured summary (key facts, obligations, deadlines, amounts) within 15 seconds.
- WHEN the document is in Hindi THEN the system SHALL provide the summary in both Hindi and English.

### Requirement 4.3: Document Comparison
As a compliance officer, I want to compare two documents side-by-side, so that I can identify discrepancies between filings or invoice versions.

Acceptance Criteria:
- WHEN a user selects two documents for comparison THEN the system SHALL highlight key differences in entities (amounts, dates, party names) and return a structured diff report.
- IF the documents are of different types (e.g., invoice vs. GST return) THEN the system SHALL cross-reference matching fields (GSTIN, amounts, tax periods).

---

## 5. Compliance Engine

### Requirement 5.1: GST Compliance Check
As a CA, I want to validate invoices against GST rules (CGST/SGST/IGST rates, mandatory fields, GSTIN format), so that I can ensure clients' documents are filing-ready.

Acceptance Criteria:
- WHEN a user runs a GST compliance check on an invoice THEN the system SHALL verify: valid GSTIN, correct tax rate for HSN code, presence of mandatory fields (invoice number, date, supplier/buyer details, taxable value), and arithmetic accuracy.
- WHEN violations are found THEN the system SHALL list each violation with the specific GST rule reference (e.g., "Rule 46(b) of CGST Rules 2017") and severity (critical/warning).

### Requirement 5.2: Multi-Regulation Compliance Check
As a compliance officer, I want to check documents against DPDP Act, SEBI, RBI, and MCA regulations, so that I can ensure organizational compliance across frameworks.

Acceptance Criteria:
- WHEN a user selects a regulation framework and runs a compliance check THEN the system SHALL evaluate the document against the selected framework's rules and return a pass/fail/warning result per rule.
- IF PII is found in a document checked against DPDP Act THEN the system SHALL flag the specific data elements and recommend handling procedures (consent, purpose limitation, retention period).
- WHEN checking against MCA rules THEN the system SHALL verify director signatures, filing deadlines, and mandatory disclosures.

### Requirement 5.3: Compliance Report Generation
As a CA, I want to generate a downloadable PDF compliance report, so that I can share it with clients or attach it to filings.

Acceptance Criteria:
- WHEN a user requests a PDF report THEN the system SHALL generate a branded PDF containing: document summary, compliance status per rule, violation details, and recommended actions — within 30 seconds.
- WHEN the report is generated THEN the system SHALL store it for 90 days and provide a shareable link (with optional expiry).

---

## 6. Payments & Billing

### Requirement 6.1: View Subscription Plans
As a prospective subscriber, I want to view available plans with pricing and features, so that I can choose the right tier for my needs.

Acceptance Criteria:
- WHEN a user visits the pricing page THEN the system SHALL display all active plans with: name, monthly/annual price in INR, document quota, feature list, and a "Subscribe" CTA.
- WHEN a plan includes a free trial THEN the system SHALL clearly display trial duration and what happens after it ends.

### Requirement 6.2: Subscribe via Razorpay
As an SME owner, I want to subscribe and pay via Razorpay (UPI, cards, net banking), so that I can use familiar Indian payment methods.

Acceptance Criteria:
- WHEN a user selects a plan and clicks Subscribe THEN the system SHALL create a Razorpay subscription, redirect to the Razorpay checkout, and upon successful payment activate the plan within 60 seconds.
- IF payment fails THEN the system SHALL show a clear error, retain the user on the free tier, and allow retry.
- WHEN a subscription is activated THEN the system SHALL send a confirmation email with invoice and GST details.

### Requirement 6.3: Subscription Management
As a subscriber, I want to upgrade, downgrade, or cancel my subscription, so that I can adjust my plan as my needs change.

Acceptance Criteria:
- WHEN a user upgrades mid-cycle THEN the system SHALL prorate the charge and activate the new plan immediately.
- WHEN a user cancels THEN the system SHALL retain access until the current billing period ends and send a confirmation email.
- IF a user's document quota is exceeded THEN the system SHALL block new uploads and prompt an upgrade, without deleting existing documents.

---

## 7. Administration

### Requirement 7.1: User Management
As a platform admin, I want to view, search, and manage all users, so that I can handle support requests and enforce policies.

Acceptance Criteria:
- WHEN an admin searches users by email, organization, or role THEN the system SHALL return matching results with account status, plan, and last login date.
- WHEN an admin suspends a user THEN the system SHALL immediately invalidate their sessions and block login until reactivated.

### Requirement 7.2: Platform Analytics Dashboard
As a platform admin, I want to view usage statistics (uploads, OCR jobs, active users, revenue), so that I can monitor platform health and growth.

Acceptance Criteria:
- WHEN an admin opens the dashboard THEN the system SHALL display: daily/weekly/monthly active users, documents processed, OCR success rate, revenue (MRR), and compliance checks run — with data no more than 1 hour stale.
- WHEN an admin filters by date range THEN the system SHALL update all metrics accordingly.

---

## 8. WhatsApp Bot

### Requirement 8.1: Document Upload via WhatsApp
As a CA on the go, I want to upload documents by sending them via WhatsApp, so that I can initiate processing without opening the web app.

Acceptance Criteria:
- WHEN a verified user sends a PDF/image to the WhatsApp bot THEN the system SHALL acknowledge receipt within 5 seconds, link it to their account, and queue it for processing.
- IF the sender's phone number is not linked to an account THEN the system SHALL reply with a registration link and not process the document.
- WHEN processing completes THEN the system SHALL send a WhatsApp message with a brief summary and link to the full report.

### Requirement 8.2: WhatsApp Command Interface
As an SME owner, I want to run commands via WhatsApp (check status, list documents, get summary), so that I can interact with the platform conversationally.

Acceptance Criteria:
- WHEN a user sends "status <doc_id>" or "स्थिति <doc_id>" THEN the system SHALL reply with the document's current processing status in the detected language.
- WHEN a user sends "list" or "सूची" THEN the system SHALL reply with the 5 most recent documents (name, date, status).
- WHEN a user sends "help" or "मदद" THEN the system SHALL reply with available commands in both English and Hindi.

---

## Non-Functional Requirements

### Requirement NFR.1: Performance
As a user, I want the system to respond quickly, so that my workflow is not interrupted.

Acceptance Criteria:
- WHEN a 10-page PDF is submitted for OCR THEN the system SHALL complete text extraction in under 30 seconds.
- WHEN any non-LLM API endpoint is called THEN the system SHALL respond in under 500 milliseconds at p95 under normal load (≤ 100 concurrent users).
- WHEN an LLM-powered endpoint (Q&A, summarization) is called THEN the system SHALL respond in under 15 seconds at p95.

### Requirement NFR.2: Availability
As a business user, I want the platform to be reliably accessible, so that I can meet my compliance deadlines.

Acceptance Criteria:
- WHEN measured over any calendar month THEN the system SHALL maintain 99.5% uptime (≤ 3.6 hours downtime/month).
- WHEN planned maintenance is required THEN the system SHALL notify users at least 48 hours in advance and schedule it between 00:00–05:00 IST.

### Requirement NFR.3: Security & Privacy (DPDP Act Compliance)
As a user handling sensitive Indian business documents, I want my data to be protected per DPDP Act 2023, so that I am legally compliant.

Acceptance Criteria:
- WHEN data is stored THEN the system SHALL encrypt it at rest using AES-256.
- WHEN data is transmitted THEN the system SHALL use TLS 1.2 or higher.
- IF PII (Aadhaar, PAN) is detected THEN the system SHALL never log it in application logs, error reports, or analytics.
- WHEN a user requests data deletion THEN the system SHALL purge all their PII within 72 hours and provide confirmation.
- WHEN consent is collected THEN the system SHALL record purpose, timestamp, and withdrawal mechanism per DPDP Act Section 6.

### Requirement NFR.4: Scalability
As the platform grows, I want the system to handle increasing load, so that performance does not degrade.

Acceptance Criteria:
- WHEN daily document volume reaches 1,000 documents/day THEN the system SHALL maintain all performance SLAs without manual intervention.
- WHEN traffic spikes 3x above normal THEN the system SHALL auto-scale processing workers within 5 minutes.
- WHEN infrastructure costs are measured THEN the system SHALL remain under ₹50,000/month for up to 1,000 documents/day throughput.
