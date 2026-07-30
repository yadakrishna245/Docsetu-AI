# DocSetu AI - WhatsApp Bot

A WhatsApp bot interface for DocSetu AI that enables document processing, entity extraction,
compliance checking, and intelligent Q&A — all through WhatsApp messages. Supports bilingual
interaction in English and Hindi.

## Features

- **Document Upload** — Send images or PDFs directly via WhatsApp for OCR processing
- **Entity Extraction** — Extract structured data (names, dates, amounts, IDs) from documents
- **Compliance Check** — Verify documents against regulatory rules and flag issues
- **Q&A** — Ask questions about uploaded documents in natural language
- **Bilingual Support** — Interact in English or Hindi (switchable per user)
- **Persistent State** — All data survives bot restarts (see below)

## Quick Start

```bash
# 1. Install dependencies
npm install

# 2. Copy environment config
cp .env.example .env
# Edit .env with your values

# 3. Start the bot
node index.js

# 4. Scan the QR code displayed in terminal with WhatsApp
#    (Link a Device → scan QR)
```

## Available Commands

| Command       | Description                                      |
|---------------|--------------------------------------------------|
| `/help`       | Show all available commands and usage info        |
| `/extract`    | Extract entities from the last uploaded document  |
| `/compliance` | Run compliance check on the last uploaded document|
| `/ask <query>`| Ask a question about your uploaded documents      |
| `/status`     | Check processing status of current document       |
| `/language`   | Toggle between English and Hindi                  |

Send any image or PDF to upload a document for processing.

## Persistent State

User preferences, uploaded documents metadata, and conversation context are persisted to disk
via `store/persistentStore.js`. Data is stored in the `store/data/` directory as JSON files.

This means:
- User language preferences survive restarts
- Document references and extraction results are retained
- Conversation context is preserved across bot reboots
- No database required — file-based storage for simplicity

## Environment Variables

Create a `.env` file from `.env.example`:

| Variable             | Description                          | Default               |
|----------------------|--------------------------------------|-----------------------|
| `DOCSETU_API_URL`    | Backend API base URL                 | `http://localhost:8000` |
| `DOCSETU_API_KEY`    | API key for backend authentication   | —                     |
| `BOT_PORT`           | Port for health check HTTP server    | `3001`                |
| `RATE_LIMIT_MAX`     | Max requests per window per user     | `20`                  |
| `RATE_LIMIT_WINDOW`  | Rate limit window in seconds         | `60`                  |
| `LOG_LEVEL`          | Logging verbosity                    | `info`                |
| `DEFAULT_LANGUAGE`   | Default language (en/hi)             | `en`                  |

## Health Check

The bot exposes an HTTP health endpoint for monitoring:

```
GET http://localhost:{BOT_PORT}/health
```

Returns `200 OK` with:
```json
{ "status": "ok", "uptime": 12345, "connected": true }
```

Useful for Docker health checks, load balancers, or uptime monitoring.

## Rate Limiting

To prevent abuse, each user is limited to `RATE_LIMIT_MAX` messages per
`RATE_LIMIT_WINDOW` seconds. When exceeded, the bot responds with a friendly
"please wait" message. Admins can adjust limits via environment variables.

## Project Structure

```
whatsapp-bot/
├── index.js              # Entry point, QR auth, message router
├── commands/             # Command handlers (/extract, /ask, etc.)
├── store/
│   ├── persistentStore.js  # Disk-based state persistence
│   └── data/               # Persisted JSON files (auto-created)
├── utils/                # Helpers (rate limiter, logger, API client)
├── .env.example          # Environment variable template
└── package.json
```

## License

MIT
