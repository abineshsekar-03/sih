"""
alerts.py - Priority-based alerting via SendGrid (industry-standard
transactional email API, not raw smtplib).
Critical anomalies (high confidence) are sent as an immediate email;
medium-confidence ones are batched into a digest so operators aren't
overwhelmed with low-value notifications (fixes "alert fatigue").
"""

import os
import pandas as pd
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

SENDER_EMAIL = "alerts@yourproject.com"
RECIPIENT_EMAIL = "operator@example.com"
API_KEY = os.environ.get("SENDGRID_API_KEY")


def build_html(df: pd.DataFrame, title: str) -> str:
    if df.empty:
        return f"<p>{title}: no items.</p>"
    rows = "".join(
        f"<tr><td style='padding:6px 12px;border-bottom:1px solid #ddd'>{r.station_id}</td>"
        f"<td style='padding:6px 12px;border-bottom:1px solid #ddd'>{r.timestamp}</td>"
        f"<td style='padding:6px 12px;border-bottom:1px solid #ddd'>{r.attribution}</td>"
        f"<td style='padding:6px 12px;border-bottom:1px solid #ddd'>{r.confidence_pct if hasattr(r,'confidence_pct') else '-'}%</td>"
        "</tr>" for r in df.itertuples()
    )
    return f"""
    <h2>{title}</h2>
    <table style="border-collapse:collapse;width:100%;font-family:Arial,sans-serif">
        <tr style="background:#0B2E4F;color:white">
            <th style="padding:8px">Station</th><th style="padding:8px">Time</th>
            <th style="padding:8px">Issue</th><th style="padding:8px">Confidence</th>
        </tr>{rows}
    </table>"""


def send_email(subject: str, html_content: str):
    if not API_KEY:
        print(f"[SKIPPED - no SENDGRID_API_KEY set] Would send: '{subject}'")
        return
    message = Mail(from_email=SENDER_EMAIL, to_emails=RECIPIENT_EMAIL,
                    subject=subject, html_content=html_content)
    try:
        response = SendGridAPIClient(API_KEY).send(message)
        print(f"Email sent ('{subject}'). Status: {response.status_code}")
    except Exception as e:
        print(f"Failed to send '{subject}': {e}")


def dispatch_alerts(final_df: pd.DataFrame):
    """Splits by alert_priority (set by fusion.py) so operators get
    immediate emails only for what actually matters."""
    if final_df.empty:
        print("No anomalies to alert on.")
        return

    df = final_df.rename(columns={"confidence_%": "confidence_pct"})
    critical = df[df["alert_priority"].str.startswith("CRITICAL")]
    medium = df[df["alert_priority"].str.startswith("MEDIUM")]
    low = df[df["alert_priority"].str.startswith("LOW")]

    if not critical.empty:
        send_email(f"CRITICAL - {len(critical)} high-confidence anomalies",
                    build_html(critical, "Critical Anomalies (immediate action)"))
    if not medium.empty:
        send_email(f"Daily digest - {len(medium)} anomalies to review",
                    build_html(medium, "Medium-Confidence Anomalies (daily digest)"))
    print(f"Logged (not emailed): {len(low)} low-confidence items.")
