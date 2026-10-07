# Job Monitor – Safe Network & IT Job Tracker

A personal job monitoring tool focused on **Network Engineer**, **NOC Technician**, **IT Technician** and related roles.

Uses only **safe, public APIs and feeds** (no LinkedIn / Indeed / Glassdoor scraping).

## Features

- Dashboard (Streamlit) with filters, source toggles, run button
- Sources: Remotive, Remote OK, Arbeitnow, optional Adzuna
- Strong deduplication (SQLite)
- Discord + Slack webhook notifications for **new** jobs only
- CSV / Excel export
- Runs on local machine or Proxmox

## Quick Start

```bash
git clone https://github.com/Zilleali/Job-Scraper.git
cd Job-Scraper
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp config/.env.example .env   # optional
streamlit run app.py
```

## Notes

- Always apply on the original job page.
- Respect rate limits of the free APIs.
- This tool is for personal use only.
