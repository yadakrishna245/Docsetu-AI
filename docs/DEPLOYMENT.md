# Deployment Guide - DocSetu AI

## Option 1: Docker Compose (Easiest)

The project includes a `docker-compose.yml` in the root directory with three services:

| Service  | Image/Build       | Port | Notes                        |
|----------|-------------------|------|------------------------------|
| backend  | FastAPI (custom)  | 8000 | Tesseract pre-installed      |
| frontend | React + nginx     | 3000 | Production build served      |
| redis    | redis:7-alpine    | 6379 | Caching & session store      |

### Steps

```bash
# 1. Copy the docker env template
cp .env.docker .env.docker.local

# 2. Edit with your actual API keys and secrets
#    At minimum set: OPENAI_API_KEY or GEMINI_API_KEY, JWT_SECRET_KEY
notepad .env.docker.local   # Windows
# nano .env.docker.local    # Linux

# 3. Build and run
docker-compose --env-file .env.docker.local up --build
```

### Access

- **Frontend**: http://localhost:3000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **API ReDoc**: http://localhost:8000/redoc

### Stopping

```bash
docker-compose down          # Stop containers
docker-compose down -v       # Stop and remove volumes (resets data)
```

---

## Option 2: Manual Local Setup

### Backend (FastAPI)

```bash
cd backend
python -m venv venv

# Activate virtual environment
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Prerequisites:**
- Python 3.10+
- Tesseract OCR installed and on PATH (or set `TESSERACT_CMD` env var)
- Redis running locally (optional — app degrades gracefully without it)

### Frontend (React)

```bash
cd frontend
npm install
npm run dev
```

Runs on http://localhost:5173 in dev mode (Vite default).

For production build:
```bash
npm run build
# Serve the dist/ folder with any static server
npx serve dist -l 3000
```

### WhatsApp Bot

```bash
cd whatsapp-bot
npm install
node index.js
```

Requires backend running. Configure webhook URL in your WhatsApp Business API settings.

---

## Option 3: AWS Serverless (Production)

Uses AWS SAM with the template at `infra/template.yaml`.

### Architecture

- **Compute**: Lambda + API Gateway (HTTP API)
- **Database**: DynamoDB (4 tables: users, documents, sessions, audit)
- **Storage**: S3 bucket for uploaded documents
- **Secrets**: SSM Parameter Store
- **Logging**: CloudWatch Logs
- **Security**: WAF (production stage only)

### Deploy via PowerShell Script

```powershell
# Deploy to dev
.\deploy.ps1 -Stage dev

# Deploy to production with API key
.\deploy.ps1 -Stage prod -OpenAIKey "sk-..."
```

### Deploy via GitHub Actions CI/CD

The pipeline is defined in `.github/workflows/deploy.yml`:

| Trigger            | Action              |
|--------------------|---------------------|
| Push to PR branch  | Deploy to `dev`     |
| Merge to `main`    | Deploy to `prod`    |
| Deploy failure     | Auto rollback       |

---

## Environment Variables

### Application Core

| Variable       | Default            | Description                          |
|----------------|--------------------|--------------------------------------|
| `APP_NAME`     | `DocSetu`          | Application name                     |
| `APP_ENV`      | `development`      | Environment: development/production  |
| `DEBUG`        | `true`             | Enable debug mode                    |
| `SECRET_KEY`   | —                  | App-level secret for signing         |
| `API_VERSION`  | `v1`               | API version prefix                   |
| `HOST`         | `0.0.0.0`          | Server bind host                     |
| `PORT`         | `8000`             | Server bind port                     |

### Database & Cache

| Variable       | Default                    | Description                  |
|----------------|----------------------------|------------------------------|
| `DATABASE_URL` | `sqlite:///./docsetu.db`   | SQLite connection string     |
| `REDIS_URL`    | `redis://localhost:6379/0` | Redis connection URL         |

### LLM Configuration

| Variable         | Default    | Description                         |
|------------------|------------|-------------------------------------|
| `LLM_PROVIDER`   | `openai`   | LLM backend: `openai` or `gemini`  |
| `OPENAI_API_KEY` | —          | OpenAI API key                      |
| `OPENAI_MODEL`   | `gpt-4`   | OpenAI model name                   |
| `GEMINI_API_KEY`  | —         | Google Gemini API key               |
| `GEMINI_MODEL`   | `gemini-pro` | Gemini model name                |

### Authentication

| Variable                          | Default  | Description                    |
|-----------------------------------|----------|--------------------------------|
| `JWT_SECRET_KEY`                  | —        | Secret for JWT signing         |
| `JWT_ALGORITHM`                   | `HS256`  | JWT algorithm                  |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `30`     | Token expiry in minutes        |

### File Handling

| Variable             | Default                        | Description                    |
|----------------------|--------------------------------|--------------------------------|
| `UPLOAD_DIR`         | `./uploads`                    | Upload storage directory       |
| `MAX_FILE_SIZE_MB`   | `10`                           | Max upload size in MB          |
| `ALLOWED_EXTENSIONS` | `.pdf,.png,.jpg,.jpeg,.docx`   | Comma-separated extensions     |

### OCR (Tesseract)

| Variable         | Default      | Description                          |
|------------------|--------------|--------------------------------------|
| `TESSERACT_CMD`  | `tesseract`  | Path to Tesseract binary             |
| `TESSERACT_LANG` | `eng`        | OCR language(s)                      |

### Vector Store

| Variable            | Default          | Description                      |
|---------------------|------------------|----------------------------------|
| `CHROMA_PERSIST_DIR`| `./chroma_data`  | ChromaDB persistence directory   |

### Logging

| Variable    | Default   | Description                          |
|-------------|-----------|--------------------------------------|
| `LOG_LEVEL` | `INFO`    | Logging level                        |
| `LOG_FILE`  | —         | Log file path (stdout if not set)    |

### CORS

| Variable       | Default          | Description                         |
|----------------|------------------|-------------------------------------|
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:5173` | Allowed origins |

### Email (SMTP)

| Variable          | Default | Description                             |
|-------------------|---------|-----------------------------------------|
| `SMTP_HOST`       | —       | SMTP server hostname                    |
| `SMTP_PORT`       | `587`   | SMTP port                               |
| `SMTP_USERNAME`   | —       | SMTP login username                     |
| `SMTP_PASSWORD`   | —       | SMTP login password                     |
| `SMTP_FROM_EMAIL` | —       | Sender email address                    |
| `APP_BASE_URL`    | —       | Base URL for email links                |

### Payments (Razorpay)

| Variable                  | Default | Description                      |
|---------------------------|---------|----------------------------------|
| `RAZORPAY_KEY_ID`         | —       | Razorpay public key              |
| `RAZORPAY_KEY_SECRET`     | —       | Razorpay secret key              |
| `RAZORPAY_WEBHOOK_SECRET` | —       | Webhook signature verification   |

---

## Running Tests

```bash
cd backend
pip install -r requirements-dev.txt

# Run all tests
pytest -v

# With coverage report
pytest --cov=. --cov-report=html
# Open htmlcov/index.html in browser
```

---

## Health Checks

| Service  | Endpoint                        | Expected Response       |
|----------|---------------------------------|-------------------------|
| Backend  | `GET http://localhost:8000/health` | `{"status": "healthy"}` |
| Frontend | `GET http://localhost:3000`       | HTTP 200                |
| Redis    | `redis-cli ping`                 | `PONG`                  |

---

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `TesseractNotFoundError` | Tesseract not installed or not on PATH | Install Tesseract. Windows: `choco install tesseract`. Linux: `apt install tesseract-ocr`. Set `TESSERACT_CMD` if not on PATH. |
| Emails not sending | SMTP not configured | Set SMTP env vars. Without them, emails are logged to console instead. |
| LLM features return errors | Missing API key | Set `OPENAI_API_KEY` or `GEMINI_API_KEY` and matching `LLM_PROVIDER`. |
| SQLite permission denied (Linux) | File/dir permissions | Ensure the app user has write access to the database file and its parent directory. |
| Redis connection refused | Redis not running | Start Redis or remove `REDIS_URL` (app runs without caching). |
| CORS errors in browser | Frontend origin not in allow list | Add your frontend URL to `CORS_ORIGINS`. |
| Docker build fails on ARM Mac | Tesseract image compatibility | Add `platform: linux/amd64` to backend service in docker-compose.yml. |
