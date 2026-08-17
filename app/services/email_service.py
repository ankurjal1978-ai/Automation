import os
import smtplib
from email.message import EmailMessage
from typing import Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()


def resolve_sender_email(preferred_sender: Optional[str] = None) -> str:
    candidates = [
        preferred_sender,
        os.getenv("GMAIL_FROM_EMAIL", "").strip(),
        os.getenv("GMAIL_USERNAME", "").strip(),
    ]

    for candidate in candidates:
        if candidate and candidate.strip():
            return candidate.strip()

    raise ValueError(
        "No Gmail sender email is configured. Set GMAIL_USERNAME or GMAIL_FROM_EMAIL in your local .env file."
    )


def get_email_config() -> Dict[str, str | int]:
    username = resolve_sender_email().strip()
    password = os.getenv("GMAIL_APP_PASSWORD", "").strip()

    if not username or not password:
        raise ValueError(
            "Missing Gmail configuration. Set GMAIL_USERNAME or GMAIL_FROM_EMAIL and GMAIL_APP_PASSWORD in your environment/.env file."
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
    sender_email = sender_email or resolve_sender_email()

    if not sender_email:
        raise ValueError("A valid Gmail sender address must be configured before sending email.")

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
    sender_email = sender_email or resolve_sender_email()

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
    sender_email: Optional[str] = None,
) -> List[Dict[str, str]]:
    results: List[Dict[str, str]] = []
    sender_email = sender_email or resolve_sender_email()
    for recipient in recipients:
        if not recipient:
            continue
        body = body_template
        result = send_email(
            recipient,
            subject,
            body,
            sender_name=sender_name,
            sender_email=sender_email,
        )
        results.append(result)
    return results
