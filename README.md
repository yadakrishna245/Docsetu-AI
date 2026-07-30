# DocSetu AI 🇮🇳

> India-first intelligent document analysis platform — OCR, compliance checking, and entity extraction for Indian businesses.

[![CI/CD](https://github.com/your-org/docsetu-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/docsetu-ai/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## What is DocSetu AI?

DocSetu AI is a document intelligence platform built specifically for Indian regulatory and business documents. Upload documents in English, Hindi, Tamil, Telugu, or Kannada — get instant compliance checks against GST, DPDP Act, SEBI, RBI, and MCA regulations.

**The problem:** Indian businesses deal with multilingual documents across dozens of regulatory frameworks. Manual compliance checking is slow, expensive, and error-prone.

**Our solution:** OCR + LLM-powered analysis that understands Indian document formats, extracts entities like PAN/Aadhaar/GSTIN, and checks compliance against 68 rules automatically.

---

## Features

### ✅ Built & Working

| Feature | Description |
|---------|-------------|
| **Multilingual OCR** | Tesseract-powered extraction for English, Hindi, Tamil, Telugu, Kannada |
| **Entity Extraction** | PAN, Aadhaar (with Verhoeff checksum validation), GSTIN, dates, amounts |
| **Compliance Engine** | 68 rules covering GST, DPDP Act, SEBI, RBI, MCA — 15 rule-based + LLM checks |
| **LLM Analysis** | OpenAI GPT-4 or Google Gemini for intelligent document understanding |
| **Document Q&A** | Ask questions about uploaded documents in natural language |
| **Document Comparison** | Side-by-side analysis of two documents |
| **Summarization** | Auto-generate document summaries |
| **WhatsApp Bot** | English + Hindi support via whatsapp-web.js |
| **8 Document Templates** | Pre-built templates for common Indian business documents |
| **PDF Reports** | Export compliance reports as PDF |
| **Batch Upload** | Process multiple documents in one go |
| **Background Processing** | Async processing for large documents |
| **Authentication** | JWT auth with email verification + password reset |
| **RBAC** | Three roles: admin, analyst, viewer |
| **Payments** | Razorpay integration for subscriptions |
| **Docker Compose** | One-command local deployment |
| **AWS Serverless** | SAM template + deploy.ps1 for production |
| **CI/CD** | GitHub Actions pipeline |

### 🗺️ Roadmap

| Feature | Status |
|---------|--------|
| Telegram Bot | Planned |
| Mobile App (React Native) | Planned |
| DigiLocker Integration | Planned |
| Tally/Zoho Integration | Planned |
| PostgreSQL support | Planned |
| Advanced analytics dashboard | Planned |
| Multi-tenant SaaS mode | Planned |

---

## Tech Stack

```
┌─────────────────────────────────────────────────┐
│                   Frontend                        │
│         React 18 + Vite + Tailwind CSS           │
└─────────────────────┬───────────────────────────┘
                      │ REST API
┌─────────────────────▼───────────────────────────┐
│                   Backend                         │
│        FastAPI (Python 3.11) + SQLAlchemy         │
├──────────────────────────────────────────────────┤
│  OCR Engine    │  LLM Layer     │  Compliance    │
│  (Tesseract)   │  (GPT-4/Gemini)│  (68 rules)   │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│                  Storage                          │
│     SQLite (local) / DynamoDB (AWS deploy)       │
└──────────────────────────────────────────────────┘
```

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, Tailwind CSS |
| Backend | FastAPI, Python 3.11, SQLAlchemy |
| Database | SQLite (dev), DynamoDB (production/AWS) |
| OCR | Tesseract with Indic language packs |
| LLM | OpenAI GPT-4 / Google Gemini (configurable) |
| Auth | JWT + bcrypt |
| Payments | Razorpay |
| Bot | whatsapp-web.js (Node.js) |
| Deploy | Docker Compose, AWS SAM, GitHub Actions |

---

## Getting Started

### Prerequisites

- Docker & Docker Compose
- OpenAI API key or Google Gemini API key

### Quick Start (Docker Compose)

```bash
# Clone the repository
git clone https://github.com/your-org/docsetu-ai.git
cd docsetu-ai

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
# OPENAI_API_KEY=sk-...
# or GEMINI_API_KEY=...
# RAZORPAY_KEY_ID=...
# RAZORPAY_KEY_SECRET=...
# JWT_SECRET=your-secret-key

# Start all services
docker compose up -d

# App available at:
# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Manual Setup (Development)

```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend (new terminal)
cd client
npm install
npm run dev
```

### AWS Deployment

```powershell
# Uses AWS SAM for serverless deployment
.\deploy.ps1 -Stage prod -Region ap-south-1
```

---

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login, returns JWT |
| POST | `/api/auth/verify-email` | Email verification |
| POST | `/api/auth/reset-password` | Password reset |

### Documents

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/documents/upload` | Upload single document |
| POST | `/api/documents/batch-upload` | Upload multiple documents |
| GET | `/api/documents` | List user's documents |
| GET | `/api/documents/{id}` | Get document details |
| DELETE | `/api/documents/{id}` | Delete document |

### Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/analysis/compliance` | Run compliance check |
| POST | `/api/analysis/extract-entities` | Extract PAN, Aadhaar, GSTIN, etc. |
| POST | `/api/analysis/summarize` | Generate document summary |
| POST | `/api/analysis/compare` | Compare two documents |
| POST | `/api/analysis/qa` | Ask questions about a document |

### Templates

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/templates` | List available templates |
| GET | `/api/templates/{id}` | Get template details |
| POST | `/api/templates/{id}/generate` | Generate document from template |

### Reports

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/reports/{analysis_id}/pdf` | Download compliance report as PDF |

### Admin

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/users` | List all users (admin only) |
| PUT | `/api/admin/users/{id}/role` | Update user role |

### Payments

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/payments/create-order` | Create Razorpay order |
| POST | `/api/payments/verify` | Verify payment |

---

## Compliance Rules

DocSetu AI ships with **68 compliance rules** covering:

| Regulation | Coverage |
|-----------|----------|
| **GST** | Invoice format, GSTIN validation, HSN codes, e-way bill thresholds |
| **DPDP Act 2023** | Data handling, consent requirements, breach notification |
| **SEBI** | Disclosure requirements, insider trading documentation |
| **RBI** | KYC documentation, transaction reporting |
| **MCA** | Company filing requirements, director documentation |

Each check runs as rule-based validation first, then LLM-enhanced analysis for context-aware compliance.

---

## Supported Languages

| Language | OCR | WhatsApp Bot |
|----------|-----|-------------|
| English | ✅ | ✅ |
| Hindi | ✅ | ✅ |
| Tamil | ✅ | — |
| Telugu | ✅ | — |
| Kannada | ✅ | — |

---

## Project Structure

```
docsetu-ai/
├── backend/
│   ├── main.py              # FastAPI app entry
│   ├── routes/              # API route handlers
│   ├── models/              # SQLAlchemy models
│   ├── services/
│   │   ├── ocr.py           # Tesseract OCR service
│   │   ├── llm.py           # GPT-4/Gemini integration
│   │   ├── compliance.py    # Rule engine
│   │   ├── entities.py      # PAN/Aadhaar/GSTIN extraction
│   │   └── pdf_export.py    # Report generation
│   ├── data/
│   │   └── compliance_rules.json  # 68 rules
│   ├── templates/           # 8 document templates
│   └── requirements.txt
├── client/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/           # Route pages
│   │   └── services/        # API client
│   ├── package.json
│   └── vite.config.js
├── whatsapp-bot/            # WhatsApp bot (Node.js)
├── docker-compose.yml
├── template.yaml            # AWS SAM template
├── deploy.ps1               # AWS deployment script
├── .github/workflows/       # CI/CD
└── README.md
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes* | OpenAI API key (*or use Gemini) |
| `GEMINI_API_KEY` | Yes* | Google Gemini API key (*or use OpenAI) |
| `JWT_SECRET` | Yes | Secret for JWT signing |
| `RAZORPAY_KEY_ID` | Yes | Razorpay key ID |
| `RAZORPAY_KEY_SECRET` | Yes | Razorpay secret |
| `SMTP_HOST` | Yes | Email server for verification |
| `SMTP_USER` | Yes | Email username |
| `SMTP_PASS` | Yes | Email password |
| `DATABASE_URL` | No | SQLite path (default: `./docsetu.db`) |

---

## Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

MIT — see [LICENSE](LICENSE) for details.

---

## Acknowledgements

- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) for multilingual text extraction
- [FastAPI](https://fastapi.tiangolo.com/) for the high-performance Python backend
- [whatsapp-web.js](https://github.com/pedroslopez/whatsapp-web.js) for WhatsApp integration
- India's regulatory bodies for publicly available compliance guidelines

---

<p align="center">
  Built with ❤️ in India, for India
</p>
