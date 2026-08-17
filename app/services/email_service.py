import os
import smtplib
from email.message import EmailMessage
from typing import Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()


def resolve_sender_email(preferred_sender: Optional[str] = None) -> str:
    candidates = [
        preferred_sender,
        os.getenv("SMTP_FROM_EMAIL", "").strip(),
        os.getenv("GMAIL_FROM_EMAIL", "").strip(),
        os.getenv("SMTP_USERNAME", "").strip(),
        os.getenv("GMAIL_USERNAME", "").strip(),
    ]

    for candidate in candidates:
        if candidate and candidate.strip():
            return candidate.strip()

    raise ValueError(
        "No sender email is configured. Enter a sender address in the app or set SMTP_FROM_EMAIL or GMAIL_FROM_EMAIL."
    )


def get_email_config(
    preferred_sender: Optional[str] = None,
    preferred_username: Optional[str] = None,
    preferred_password: Optional[str] = None,
    smtp_host: Optional[str] = None,
    smtp_port: Optional[int] = None,
    use_tls: Optional[bool] = None,
) -> Dict[str, str | int | bool]:
    username = (preferred_username or os.getenv("SMTP_USERNAME", "").strip() or resolve_sender_email(preferred_sender)).strip()
    password = (preferred_password or os.getenv("SMTP_PASSWORD", "").strip() or os.getenv("GMAIL_APP_PASSWORD", "").strip()).strip()
    sender = resolve_sender_email(preferred_sender).strip()

    if not username or not password:
        raise ValueError(
            "Missing SMTP configuration. Enter the sender email, username, and password in the UI or configure SMTP_USERNAME and SMTP_PASSWORD in your environment/.env file."
        )

    host = (smtp_host or os.getenv("SMTP_HOST", "").strip() or os.getenv("GMAIL_SMTP_HOST", "").strip() or "smtp.gmail.com").strip()
    if not host:
        host = "smtp.gmail.com"

    gmail_default = host.lower().endswith("gmail.com") and not os.getenv("SMTP_HOST", "").strip() and not smtp_host
    port_default = "465" if gmail_default else (os.getenv("SMTP_PORT", "").strip() or os.getenv("GMAIL_SMTP_PORT", "587").strip() or "587")
    port_value = smtp_port or int(port_default)
    security = use_tls if use_tls is not None else (
        str(os.getenv("SMTP_USE_TLS", "")).lower() == "true"
        if os.getenv("SMTP_USE_TLS", "")
        else (not gmail_default)
    )

    return {
        "username": username,
        "password": password,
        "smtp_server": host,
        "smtp_port": int(port_value),
        "sender_name": os.getenv("SMTP_SENDER_NAME", "Drip automation"),
        "sender_email": sender,
        "use_tls": security,
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
        raise ValueError("A valid sender address must be configured before sending email.")

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
    password: Optional[str] = None,
    username: Optional[str] = None,
    smtp_host: Optional[str] = None,
    smtp_port: Optional[int] = None,
    use_tls: Optional[bool] = None,
) -> Dict[str, str]:
    config = get_email_config(
        preferred_sender=sender_email,
        preferred_username=username,
        preferred_password=password,
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        use_tls=use_tls,
    )
    sender_name = sender_name or str(config["sender_name"])
    sender_email = sender_email or str(config["sender_email"])

    message = build_email_message(
        recipient=recipient,
        subject=subject,
        body=body,
        sender_name=sender_name,
        sender_email=sender_email,
    )

    smtp_server = str(config["smtp_server"])
    port = int(config["smtp_port"])
    use_tls_flag = bool(config["use_tls"])

    if port == 465:
        with smtplib.SMTP_SSL(smtp_server, port) as server:
            server.login(str(config["username"]), str(config["password"]))
            server.send_message(message)
    else:
        with smtplib.SMTP(smtp_server, port) as server:
            if use_tls_flag:
                server.starttls()
            server.login(str(config["username"]), str(config["password"]))
            server.send_message(message)

    return {"status": "sent", "recipient": recipient, "subject": subject}


def send_bulk_emails(
    recipients: List[str],
    subject: str,
    body_template: str,
    sender_name: Optional[str] = None,
    sender_email: Optional[str] = None,
    password: Optional[str] = None,
    username: Optional[str] = None,
    smtp_host: Optional[str] = None,
    smtp_port: Optional[int] = None,
    use_tls: Optional[bool] = None,
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
            password=password,
            username=username,
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            use_tls=use_tls,
        )
        results.append(result)
    return results
