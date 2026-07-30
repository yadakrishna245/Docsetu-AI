# Status Page Setup (Upptime)

DocSetu AI uses [Upptime](https://upptime.js.org/) for free, open-source uptime monitoring.

## Setup Steps

1. Create a new repo `Docsetu-AI-status` on GitHub
2. Copy `upptime.yml` to `.upptimerc.yml` in that repo
3. Set repository secrets:
   - `API_URL`: Your deployed API URL (e.g., https://api.docsetu.ai)
   - `FRONTEND_URL`: Your frontend URL (e.g., https://app.docsetu.ai)
4. Enable GitHub Pages on the status repo
5. Upptime will check every 5 minutes and auto-generate a status page

## Features
- Checks every 5 minutes
- Auto-creates GitHub Issues for downtime
- Status page hosted on GitHub Pages (free)
- Response time graphs
- Historical uptime percentage
- RSS feed for subscribers

## Alternative: BetterUptime (paid, simpler)
If you prefer a managed solution:
1. Sign up at betteruptime.com
2. Add monitors for:
   - GET https://your-api-url/health (every 1 min)
   - GET https://your-frontend-url (every 3 min)
3. Set up status page at status.docsetu.ai
4. Add on-call schedule for alerts (Slack/SMS/email)
