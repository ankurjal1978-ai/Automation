import os
import smtplib
from email.message import EmailMessage
from typing import Dict, List, Optional


def get_email_config() -> Dict[str, str | int]:
    username = os.getenv("GMAIL_USERNAME", "").strip()
    password = os.getenv("GMAIL_APP_PASSWORD", "").strip()

    if not username or not password:
        raise ValueError(
            "Missing Gmail configuration. Set GMAIL_USERNAME and GMAIL_APP_PASSWORD in your environment/.env file."
        )

    return {
        "username": username,
        "password": password,
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 465,
        "sender_name": os.getenv("GMAIL_SENDER_NAME", "Drip automation"),
    }


def build_email_message(
    recipient: str,
    subject: str,
    body: str,
    sender_name: str = "Drip automation",
    sender_email: Optional[str] = None,
) -> EmailMessage:
    sender_email = sender_email or os.getenv("GMAIL_USERNAME", "")

    if not sender_email:
        raise ValueError("GMAIL_USERNAME must be set before sending email.")

    message = EmailMessage()
    message["From"] = f"{sender_name} <{sender_email}>"
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)
    return message


def send_email(
    recipient: str,
    subject: str,
    body: str,
    sender_name: Optional[str] = None,
    sender_email: Optional[str] = None,
) -> Dict[str, str]:
    config = get_email_config()
    sender_name = sender_name or str(config["sender_name"])
    sender_email = sender_email or str(config["username"])

    message = build_email_message(
        recipient=recipient,
        subject=subject,
        body=body,
        sender_name=sender_name,
        sender_email=sender_email,
    )

    with smtplib.SMTP_SSL(config["smtp_server"], int(config["smtp_port"])) as server:
        server.login(config["username"], config["password"])
        server.send_message(message)

    return {"status": "sent", "recipient": recipient, "subject": subject}


def send_bulk_emails(
    recipients: List[str],
    subject: str,
    body_template: str,
    sender_name: Optional[str] = None,
) -> List[Dict[str, str]]:
    results: List[Dict[str, str]] = []
    for recipient in recipients:
        if not recipient:
            continue
        body = body_template
        result = send_email(recipient, subject, body, sender_name=sender_name)
        results.append(result)
    return results
