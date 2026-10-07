# Job Monitor – Safe Network & IT Job Tracker

A personal job monitoring tool focused on **Network Engineer**, **NOC Technician**, **IT Technician**, **Network Technician** and related roles.

Uses **only safe, public APIs and feeds** — no LinkedIn / Indeed / Glassdoor scraping.

**Repo:** https://github.com/Zilleali/Job-Scraper

---

## Features

| Feature | Details |
|---------|--------|
| Dashboard | Streamlit UI with filters, source toggles, run button, history table |
| Free APIs | Remotive · Remote OK · Arbeitnow (no keys needed) |
| Optional API | Adzuna (free signup) |
| Company pages | Greenhouse + Lever boards (Cloudflare, Stripe, Netflix, Palantir, etc.) |
| Deduplication | SQLite – never alert the same job twice |
| Notifications | Discord + Slack webhooks for **new** jobs only |
| Export | CSV / Excel download |
| Scheduling | System cron or run manually |

---

## Quick Start

```bash
git clone https://github.com/Zilleali/Job-Scraper.git
cd Job-Scraper

python3 -m venv venv
source venv/bin/activate          # Linux / Proxmox / macOS
# Windows: venv\Scripts\activate

pip install -r requirements.txt

# Optional: secrets
cp config/.env.example .env
# edit .env (Discord / Slack / Adzuna)

streamlit run app.py
```

Open the URL shown (usually http://localhost:8501).

---

## Search Filters (Dashboard Sidebar)

- **Keywords** – one per line (default: Network Engineer, NOC Technician, …)
- **Locations** – comma-separated (leave empty = any)
- **Countries** – for Adzuna (ISO codes: `us,gb,pk,de,ae,sa,sg,au` …)
- **Remote only** – toggle
- **Sources** – enable/disable Remotive, Remote OK, Arbeitnow, Adzuna, Companies

---

## Notifications Setup

### Discord

1. Open your Discord server → right-click a channel → **Edit Channel** → **Integrations** → **Webhooks** → **New Webhook**
2. Copy the **Webhook URL**
3. Paste it in the dashboard sidebar **or** put it in `.env`:
   ```
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
   ```
4. Click **Test Discord** in the sidebar

### Slack

1. Go to https://api.slack.com/apps → **Create New App** → **From scratch**
2. Under **Incoming Webhooks** → Activate → **Add New Webhook to Workspace**
3. Choose a channel → copy the Webhook URL
4. Paste it in the dashboard sidebar **or** put it in `.env`:
   ```
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
   ```
5. Click **Test Slack** in the sidebar

Only **new** jobs (not seen before) trigger notifications.

---

## Company Career Pages

The `companies` source polls public Greenhouse & Lever boards for companies that often hire network / infrastructure roles:

**Greenhouse:** Cloudflare, Stripe, Discord, Airbnb, Coinbase, Robinhood, DoorDash, Notion, Figma, Vercel, Linear, Anthropic, Plaid, Rippling, Gusto, Asana, Databricks, Scale AI, Anduril, SpaceX

**Lever:** Netflix, Spotify, Palantir, Twitch, Shopify

You can add more tokens in `sources/companies.py` (`KNOWN_BOARDS` list).

---

## Scheduling with Cron (Proxmox / Linux)

Example – every 6 hours:

```bash
0 */6 * * * cd /path/to/Job-Scraper && /path/to/venv/bin/python -c "
from core.models import SearchFilters
from core.orchestrator import run_search
filters = SearchFilters(
    keywords=['Network Engineer', 'NOC Technician', 'IT Technician', 'Network Technician'],
    remote_only=False,
    sources=['remotive', 'remoteok', 'arbeitnow', 'companies']
)
print(run_search(filters))
"
```

Make sure Discord/Slack URLs are in `.env` so notifications work headlessly.

---

## Project Structure

```
Job-Scraper/
├── app.py                  # Streamlit dashboard
├── requirements.txt
├── README.md
├── config/
│   ├── settings.yaml       # defaults
│   └── .env.example
├── core/
│   ├── models.py
│   ├── database.py         # SQLite + dedup
│   ├── orchestrator.py
│   └── notifier.py
├── sources/
│   ├── remotive.py
│   ├── remoteok.py
│   ├── arbeitnow.py
│   ├── adzuna.py
│   └── companies.py        # Greenhouse + Lever
└── utils/
    └── export.py
```

---

## Notes

- Always apply on the original job page.
- Respect rate limits of the free APIs.
- For personal use only.
- Adzuna free key: https://developer.adzuna.com

---

## License

MIT – use freely for personal job hunting.
