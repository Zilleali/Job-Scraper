import os
from typing import List
import httpx
from dotenv import load_dotenv

from core.models import Job

load_dotenv()


def _format_job_message(job: Job) -> str:
    remote_badge = "\U0001f30d Remote" if job.remote else f"\U0001f4cd {job.location}"
    salary = f"\n\U0001f4b0 {job.salary}" if job.salary else ""
    tags = f"\n\U0001f3f7\ufe0f {', '.join(job.tags[:5])}" if job.tags else ""
    return (
        f"**{job.title}**\n"
        f"\U0001f3e2 {job.company}\n"
        f"{remote_badge}{salary}{tags}\n"
        f"\U0001f517 {job.url}\n"
        f"_Source: {job.source}_"
    )


def send_discord(jobs: List[Job], webhook_url: str | None = None) -> bool:
    url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL")
    if not url:
        return False

    if not jobs:
        return True

    for i in range(0, len(jobs), 5):
        batch = jobs[i : i + 5]
        embeds = []
        for job in batch:
            embeds.append({
                "title": job.title[:256],
                "url": job.url,
                "description": f"**{job.company}**\n{job.location}" + (f"\n\U0001f4b0 {job.salary}" if job.salary else ""),
                "color": 5814783,
                "footer": {"text": f"Source: {job.source}"},
            })

        payload = {
            "content": f"\U0001f195 **{len(batch)} new job(s) found**",
            "embeds": embeds,
        }

        try:
            with httpx.Client(timeout=15) as client:
                resp = client.post(url, json=payload)
                resp.raise_for_status()
        except Exception as e:
            print(f"[Discord] Error: {e}")
            return False

    return True


def send_slack(jobs: List[Job], webhook_url: str | None = None) -> bool:
    url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")
    if not url:
        return False

    if not jobs:
        return True

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"\U0001f195 {len(jobs)} new job(s) found"},
        }
    ]

    for job in jobs[:10]:
        text = _format_job_message(job)
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": text},
        })
        blocks.append({"type": "divider"})

    payload = {"blocks": blocks}

    try:
        with httpx.Client(timeout=15) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
        return True
    except Exception as e:
        print(f"[Slack] Error: {e}")
        return False


def notify_all(jobs: List[Job]) -> dict:
    results = {
        "discord": send_discord(jobs),
        "slack": send_slack(jobs),
        "count": len(jobs),
    }
    return results
