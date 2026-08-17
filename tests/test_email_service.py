import pytest

from app.services.email_service import build_email_message, get_email_config, resolve_sender_email


def test_get_email_config_reads_gmail_env(monkeypatch):
    monkeypatch.setenv("GMAIL_USERNAME", "sender@gmail.com")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "abcd-efgh-1234")
    monkeypatch.delenv("GMAIL_FROM_EMAIL", raising=False)

    config = get_email_config()

    assert config["username"] == "sender@gmail.com"
    assert config["password"] == "abcd-efgh-1234"
    assert config["smtp_server"] == "smtp.gmail.com"
    assert config["smtp_port"] == 465


def test_resolve_sender_email_prefers_gmail_from_email(monkeypatch):
    monkeypatch.setenv("GMAIL_USERNAME", "fallback@gmail.com")
    monkeypatch.setenv("GMAIL_FROM_EMAIL", "primary@gmail.com")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "abcd-efgh-1234")

    assert resolve_sender_email() == "primary@gmail.com"


def test_get_email_config_uses_explicit_sender_email(monkeypatch):
    monkeypatch.delenv("GMAIL_USERNAME", raising=False)
    monkeypatch.delenv("GMAIL_FROM_EMAIL", raising=False)
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "abcd-efgh-1234")

    config = get_email_config("selected@gmail.com")

    assert config["username"] == "selected@gmail.com"
    assert config["password"] == "abcd-efgh-1234"


def test_get_email_config_uses_explicit_password_override(monkeypatch):
    monkeypatch.delenv("GMAIL_APP_PASSWORD", raising=False)
    monkeypatch.setenv("GMAIL_USERNAME", "sender@gmail.com")

    config = get_email_config(preferred_password="override-app-pass")

    assert config["password"] == "override-app-pass"


def test_build_email_message_includes_recipient_and_body():
    msg = build_email_message(
        recipient="alice@example.com",
        subject="Welcome",
        body="Hello Alice,\nThanks for joining.",
        sender_name="Drip automation",
        sender_email="sender@gmail.com",
    )

    payload = msg.as_string()
    assert "alice@example.com" in payload
    assert "Welcome" in payload
    assert "Hello Alice" in payload
    assert "Drip automation" in payload


def test_get_email_config_requires_credentials(monkeypatch):
    monkeypatch.delenv("GMAIL_USERNAME", raising=False)
    monkeypatch.delenv("GMAIL_FROM_EMAIL", raising=False)
    monkeypatch.delenv("GMAIL_APP_PASSWORD", raising=False)

    with pytest.raises(ValueError):
        get_email_config()
