from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from app.config import DB_PATH, REQUIRED_FIELDS
from app.database import get_connection, init_db
from app.services.contact_service import normalize_contact_row, validate_contact
from app.services.email_service import send_bulk_emails

load_dotenv()

st.set_page_config(page_title="Drip automation", layout="wide")


@st.cache_resource
def setup_database():
    init_db()


def save_contacts(df: pd.DataFrame, source_file: str = "uploaded_csv"):
    if df.empty:
        return {"saved": 0, "duplicate_count": 0, "invalid_count": 0}

    records = []
    duplicate_count = 0
    invalid_count = 0
    existing_emails = get_existing_emails()

    for row in df.to_dict(orient="records"):
        cleaned = normalize_contact_row(row)
        errors = validate_contact(cleaned)

        if errors:
            invalid_count += 1
            continue

        email = cleaned.get("email", "")
        if email in existing_emails:
            duplicate_count += 1
            continue

        records.append(
            {
                "first_name": cleaned.get("first_name", ""),
                "last_name": cleaned.get("last_name", ""),
                "email": cleaned.get("email", ""),
                "company": cleaned.get("company", ""),
                "title": cleaned.get("title", ""),
                "website": cleaned.get("website", ""),
                "industry": cleaned.get("industry", ""),
                "country": cleaned.get("country", ""),
                "campaign": cleaned.get("campaign", ""),
                "status": "valid",
                "source_file": source_file,
            }
        )
        existing_emails.add(email)

    conn = get_connection()
    try:
        conn.executemany(
            """
            INSERT OR IGNORE INTO contacts (
                first_name, last_name, email, company, title, website, industry,
                country, campaign, status, source_file
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    r["first_name"],
                    r["last_name"],
                    r["email"],
                    r["company"],
                    r["title"],
                    r["website"],
                    r["industry"],
                    r["country"],
                    r["campaign"],
                    r["status"],
                    r["source_file"],
                )
                for r in records
            ],
        )
        conn.commit()
    finally:
        conn.close()

    return {
        "saved": len(records),
        "duplicate_count": duplicate_count,
        "invalid_count": invalid_count,
    }


def load_contacts():
    conn = get_connection()
    try:
        return pd.read_sql_query("SELECT * FROM contacts ORDER BY id DESC", conn)
    finally:
        conn.close()


def count_contacts():
    conn = get_connection()
    try:
        return conn.execute("SELECT COUNT(*) FROM contacts").fetchone()[0]
    finally:
        conn.close()


def count_by_status(status: str):
    conn = get_connection()
    try:
        return conn.execute("SELECT COUNT(*) FROM contacts WHERE status = ?", (status,)).fetchone()[0]
    finally:
        conn.close()


def active_campaigns():
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT campaign, COUNT(*) AS count FROM contacts WHERE campaign IS NOT NULL AND campaign != '' GROUP BY campaign ORDER BY COUNT(*) DESC"
        ).fetchall()
        return rows
    finally:
        conn.close()


def get_existing_emails():
    conn = get_connection()
    try:
        rows = conn.execute("SELECT lower(email) AS email FROM contacts WHERE email IS NOT NULL AND email != ''").fetchall()
        return {row["email"] for row in rows}
    finally:
        conn.close()


def classify_contacts(df: pd.DataFrame):
    existing_emails = get_existing_emails()
    seen_emails = set()
    valid_rows = []
    duplicate_rows = []
    invalid_rows = []

    for row in df.to_dict(orient="records"):
        cleaned = normalize_contact_row(row)
        errors = validate_contact(cleaned)
        email = cleaned.get("email", "")

        if errors:
            cleaned["validation_errors"] = "; ".join(errors)
            invalid_rows.append(cleaned)
            continue

        if email in seen_emails or email in existing_emails:
            duplicate_rows.append(cleaned)
            continue

        seen_emails.add(email)
        valid_rows.append(cleaned)

    return valid_rows, duplicate_rows, invalid_rows


def process_csv(df: pd.DataFrame, source_name: str):
    df.columns = [str(column).strip() for column in df.columns]
    missing_fields = [field for field in REQUIRED_FIELDS if field not in df.columns]

    if missing_fields:
        st.error(f"CSV is missing required columns: {missing_fields}")
        return

    valid_rows, duplicate_rows, invalid_rows = classify_contacts(df)
    valid_count = len(valid_rows)
    duplicate_count = len(duplicate_rows)
    invalid_count = len(invalid_rows)

    st.success(f"CSV processed successfully. {valid_count} valid contacts, {duplicate_count} duplicate emails, {invalid_count} invalid rows.")

    if valid_rows:
        save_result = save_contacts(pd.DataFrame(valid_rows), source_name)
        st.info(f"Saved {save_result['saved']} valid contacts to SQLite.")

    if duplicate_rows:
        duplicate_emails = sorted({row["email"] for row in duplicate_rows})
        st.warning(f"Duplicate emails detected: {', '.join(duplicate_emails)}")

    if invalid_rows:
        with st.expander("Invalid rows", expanded=True):
            st.dataframe(pd.DataFrame(invalid_rows), use_container_width=True)

    st.subheader("Dashboard")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Contacts uploaded", len(df))
    col2.metric("Valid contacts", valid_count)
    col3.metric("Duplicate contacts", duplicate_count)
    col4.metric("Invalid contacts", invalid_count)
    col5.metric("Active campaigns", len(active_campaigns()))

    st.subheader("Contacts")
    st.dataframe(load_contacts(), use_container_width=True)


setup_database()

st.title("Drip automation")
st.caption("Phase 1: contact intake and validation")

st.sidebar.header("Actions")
if st.sidebar.button("Load sample data"):
    sample_path = Path(__file__).resolve().parent / "sample_contacts.csv"
    if sample_path.exists():
        sample_df = pd.read_csv(sample_path)
        process_csv(sample_df, sample_path.name)
    else:
        st.sidebar.warning("Sample CSV not found in the project folder.")

st.sidebar.subheader("SMTP send")
with st.sidebar:
    st.caption("Works with Gmail, Outlook, SendGrid, and other SMTP providers.")
    sender_email = st.text_input(
        "From email address",
        value=str(__import__('os').getenv("SMTP_FROM_EMAIL", "") or __import__('os').getenv("GMAIL_USERNAME", "") or __import__('os').getenv("GMAIL_FROM_EMAIL", "")),
        help="This is the address shown as the sender.",
        placeholder="you@example.com",
    )
    smtp_username = st.text_input(
        "SMTP username",
        value=str(__import__('os').getenv("SMTP_USERNAME", "") or __import__('os').getenv("GMAIL_USERNAME", "")),
        help="Usually the same as your email address, or your SMTP account login.",
        placeholder="your_account_or_email",
    )
    smtp_password = st.text_input(
        "SMTP password / app password",
        type="password",
        help="Use your SMTP password, Gmail App Password, or provider-specific token.",
        placeholder="Paste your password or app token",
    )
    smtp_host = st.text_input(
        "SMTP host",
        value=str(__import__('os').getenv("SMTP_HOST", "") or "smtp.gmail.com"),
        help="Example: smtp.gmail.com, smtp.office365.com, smtp.sendgrid.net",
    )
    smtp_port = st.number_input("SMTP port", min_value=1, max_value=65535, value=587, step=1)
    use_tls = st.selectbox("Security", options=["STARTTLS", "SSL"], index=0)
    campaign_subject = st.text_input("Email subject", value="Welcome to Drip automation")
    campaign_body = st.text_area(
        "Email body",
        value=(
            "<html><body style='font-family:Arial,sans-serif;background:#f5f7fb;padding:24px;'>"
            "<div style='max-width:640px;margin:auto;background:white;border-radius:12px;overflow:hidden;border:1px solid #e5e7eb;'>"
            "<img src='https://images.unsplash.com/photo-1552664730-d307ca884978?auto=format&fit=crop&w=1200&q=80' alt='Campaign hero' style='width:100%;height:220px;object-fit:cover;'>"
            "<div style='padding:24px 28px 32px;'>"
            "<p style='text-transform:uppercase;letter-spacing:1px;color:#5b6bff;font-size:12px;font-weight:bold;'>New campaign</p>"
            "<h2 style='margin:0 0 12px;font-size:28px;color:#111827;'>Hello {first_name},</h2>"
            "<p style='font-size:16px;color:#374151;line-height:1.7;'>Thanks for your interest in Drip automation. We help teams turn leads into qualified conversations with a simple, measurable outreach engine.</p>"
            "<p style='margin:20px 0;font-size:16px;color:#374151;line-height:1.7;'>Your workflow is now ready to test with smarter segmentation, cleaner follow-ups, and better visibility into who opened and engaged.</p>"
            "<div style='margin:24px 0;padding:16px 20px;background:#f3f4f6;border-radius:10px;'>"
            "<p style='margin:0;color:#111827;font-size:15px;'><strong>Campaign:</strong> {campaign_name}</p>"
            "<p style='margin:8px 0 0;color:#111827;font-size:15px;'><strong>Next step:</strong> Review your outreach cadence and schedule the next touchpoint.</p>"
            "</div>"
            "<p style='margin:20px 0 0;font-size:14px;color:#4b5563;'>Best,<br>Drip automation team</p>"
            "</div>"
            "</div>"
            "<img src='https://example.com/track-open?email={email}&campaign={campaign_name}&first_name={first_name}' width='1' height='1' alt='' style='display:none;'>"
            "</body></html>"
        ),
        height=220,
    )
    send_button = st.button("Send sample emails")

uploaded_file = st.file_uploader("Upload CSV contact list", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        process_csv(df, uploaded_file.name)
    except Exception as exc:
        st.error(f"Failed to process CSV: {exc}")

else:
    st.info("Upload a CSV file with the required contact fields to begin.")

    st.subheader("Dashboard")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Contacts uploaded", count_contacts())
    col2.metric("Valid contacts", count_by_status("valid"))
    col3.metric("Duplicate contacts", 0)
    col4.metric("Invalid contacts", 0)
    col5.metric("Active campaigns", len(active_campaigns()))

    st.subheader("Contacts")
    st.dataframe(load_contacts(), use_container_width=True)

if send_button:
    try:
        recipients = load_contacts()["email"].dropna().tolist()
        if not recipients:
            st.warning("There are no saved contacts to email yet. Upload a CSV first.")
        else:
            rendered_recipients = []
            for row in load_contacts().to_dict(orient="records"):
                first_name = (row.get("first_name") or "there").strip() or "there"
                email_value = (row.get("email") or "").strip()
                campaign_name = (row.get("campaign") or "launch-series").strip() or "launch-series"
                email_body = campaign_body.replace("{first_name}", first_name)
                email_body = email_body.replace("{email}", email_value)
                email_body = email_body.replace("{campaign_name}", campaign_name)
                rendered_recipients.append((email_value, email_body))

            sent = []
            for recipient, body in rendered_recipients:
                try:
                    send_bulk_emails(
                        [recipient],
                        campaign_subject,
                        body,
                        sender_name="Drip automation",
                        sender_email=(sender_email.strip() if sender_email else None),
                        username=(smtp_username.strip() if smtp_username else None),
                        password=(smtp_password.strip() if smtp_password else None),
                        smtp_host=(smtp_host.strip() if smtp_host else None),
                        smtp_port=int(smtp_port),
                        use_tls=(use_tls == "STARTTLS"),
                    )
                    sent.append(recipient)
                except Exception as exc:
                    st.warning(f"Failed to send to {recipient}: {exc}")

            if sent:
                st.success(f"Sent {len(sent)} email(s) using the configured SMTP provider.")
            else:
                st.error(
                    "No emails were sent. Check that the SMTP host, port, username, and password are valid."
                )
    except Exception as exc:
        st.error(f"SMTP sending is not configured correctly: {exc}")
        st.info(
            "Enter the SMTP host, username, and password in the sidebar or configure SMTP_* variables in a local .env file."
        )
