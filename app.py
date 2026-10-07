import streamlit as st
from datetime import datetime
from pathlib import Path
import os
from dotenv import load_dotenv

from core.models import SearchFilters
from core.orchestrator import run_search, load_settings
from core.database import init_db, get_all_jobs
from utils.export import export_csv, export_excel, jobs_to_dataframe
from core.notifier import send_discord, send_slack

load_dotenv()
init_db()

st.set_page_config(
    page_title="Job Monitor – Network & IT Roles",
    page_icon="\U0001f4e1",
    layout="wide",
)

st.title("\U0001f4e1 Job Monitor")
st.caption("Safe job monitoring for Network Engineer / NOC / IT roles  •  Remote + Global")

with st.sidebar:
    st.header("Search Filters")

    default_keywords = [
        "Network Engineer",
        "Junior Network Engineer",
        "NOC Technician",
        "IT Technician",
        "Network Technician",
    ]
    keywords_text = st.text_area(
        "Keywords (one per line)",
        value="\n".join(default_keywords),
        height=140,
    )
    keywords = [k.strip() for k in keywords_text.splitlines() if k.strip()]

    locations_text = st.text_input(
        "Locations (comma separated, leave empty for any)",
        value="",
    )
    locations = [l.strip() for l in locations_text.split(",") if l.strip()]

    countries_text = st.text_input(
        "Countries for Adzuna (ISO codes, e.g. us,gb,pk,de,ae)",
        value="us,gb",
    )
    countries = [c.strip().lower() for c in countries_text.split(",") if c.strip()]

    remote_only = st.checkbox("Remote only", value=False)

    results_per_source = st.slider("Results per source", 10, 50, 25)

    st.divider()
    st.subheader("Sources")
    use_remotive = st.checkbox("Remotive", value=True)
    use_remoteok = st.checkbox("Remote OK", value=True)
    use_arbeitnow = st.checkbox("Arbeitnow", value=True)
    use_adzuna = st.checkbox("Adzuna (needs API key)", value=False)
    use_companies = st.checkbox("Company pages (Greenhouse + Lever)", value=True)

    enabled_sources = []
    if use_remotive:
        enabled_sources.append("remotive")
    if use_remoteok:
        enabled_sources.append("remoteok")
    if use_arbeitnow:
        enabled_sources.append("arbeitnow")
    if use_adzuna:
        enabled_sources.append("adzuna")
    if use_companies:
        enabled_sources.append("companies")

    st.divider()
    st.subheader("Notifications")
    discord_url = st.text_input("Discord Webhook URL", value=os.getenv("DISCORD_WEBHOOK_URL", ""), type="password")
    slack_url = st.text_input("Slack Webhook URL", value=os.getenv("SLACK_WEBHOOK_URL", ""), type="password")

    if st.button("Test Discord"):
        if discord_url:
            from core.models import Job
            test_job = Job(
                id="test",
                title="Test Notification",
                company="Job Monitor",
                location="Remote",
                url="https://example.com",
                source="test",
                remote=True,
            )
            ok = send_discord([test_job], webhook_url=discord_url)
            st.success("Discord test sent" if ok else "Discord failed – check URL")
        else:
            st.warning("Paste a Discord webhook URL first")

    if st.button("Test Slack"):
        if slack_url:
            from core.models import Job
            test_job = Job(
                id="test",
                title="Test Notification",
                company="Job Monitor",
                location="Remote",
                url="https://example.com",
                source="test",
                remote=True,
            )
            ok = send_slack([test_job], webhook_url=slack_url)
            st.success("Slack test sent" if ok else "Slack failed – check URL")
        else:
            st.warning("Paste a Slack webhook URL first")

col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    run_btn = st.button("\U0001f680 Run Search Now", type="primary", use_container_width=True)

with col2:
    export_csv_btn = st.button("\U0001f4e5 Export CSV", use_container_width=True)

with col3:
    export_xlsx_btn = st.button("\U0001f4ca Export Excel", use_container_width=True)

if run_btn:
    if not enabled_sources:
        st.error("Select at least one source")
    elif not keywords:
        st.error("Enter at least one keyword")
    else:
        filters = SearchFilters(
            keywords=keywords,
            locations=locations,
            countries=countries,
            remote_only=remote_only,
            results_per_source=results_per_source,
            sources=enabled_sources,
        )

        with st.spinner("Searching safe job sources..."):
            if discord_url:
                os.environ["DISCORD_WEBHOOK_URL"] = discord_url
            if slack_url:
                os.environ["SLACK_WEBHOOK_URL"] = slack_url

            result = run_search(filters)

        st.success(
            f"Fetched **{result['total_fetched']}** jobs  •  "
            f"**{result['new_jobs']}** new  •  "
            f"Sources: {result['per_source']}"
        )

        if result["new_jobs"] > 0:
            st.subheader("\U0001f195 New jobs this run")
            for job in result["new_job_list"]:
                with st.expander(f"{job.title} @ {job.company}"):
                    st.write(f"**Location:** {job.location}")
                    st.write(f"**Source:** {job.source}")
                    if job.salary:
                        st.write(f"**Salary:** {job.salary}")
                    st.markdown(f"[Apply / View]({job.url})")
                    if job.description:
                        st.caption(job.description[:400] + "...")

        if result.get("notifications"):
            st.info(f"Notifications: {result['notifications']}")

if export_csv_btn:
    path = export_csv()
    st.success(f"CSV saved to `{path}`")
    with open(path, "rb") as f:
        st.download_button("Download CSV", f, file_name=path.name, mime="text/csv")

if export_xlsx_btn:
    path = export_excel()
    st.success(f"Excel saved to `{path}`")
    with open(path, "rb") as f:
        st.download_button(
            "Download Excel",
            f,
            file_name=path.name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

st.divider()
st.subheader("\U0001f4cb Job History (last 200)")

records = get_all_jobs(limit=200)
if records:
    df = jobs_to_dataframe(records)
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "URL": st.column_config.LinkColumn("URL"),
        },
    )
else:
    st.info("No jobs stored yet. Run a search to get started.")

st.divider()
st.caption(
    "Sources: Remotive • Remote OK • Arbeitnow • Companies (Greenhouse/Lever) • Adzuna (optional)  |  "
    "Data is for personal monitoring only. Always apply on the original job page."
)
