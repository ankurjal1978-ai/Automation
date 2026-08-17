from app.services.contact_service import detect_duplicate_emails, normalize_contact_row, validate_contact


def test_normalize_contact_row_strips_whitespace_and_lowercases_email():
    row = {
        "first_name": "  Alice  ",
        "last_name": "Smith",
        "email": " Alice.Smith@Example.com ",
        "company": " Acme ",
        "title": " VP ",
        "website": "https://acme.com",
        "industry": " SaaS ",
        "country": "USA",
        "campaign": "launch-seq",
    }

    cleaned = normalize_contact_row(row)

    assert cleaned["first_name"] == "Alice"
    assert cleaned["last_name"] == "Smith"
    assert cleaned["email"] == "alice.smith@example.com"
    assert cleaned["company"] == "Acme"


def test_validate_contact_accepts_valid_record():
    row = {
        "first_name": "Bob",
        "last_name": "Jones",
        "email": "bob@example.com",
        "company": "Northwind",
        "title": "Director",
        "website": "https://northwind.com",
        "industry": "Finance",
        "country": "Canada",
        "campaign": "spring-promo",
    }

    errors = validate_contact(row)
    assert errors == []


def test_validate_contact_flags_missing_required_fields_and_bad_email():
    row = {
        "first_name": "",
        "last_name": "",
        "email": "not-an-email",
        "company": "",
        "title": "",
        "website": "",
        "industry": "",
        "country": "",
        "campaign": "",
    }

    errors = validate_contact(row)

    assert any("first_name" in e for e in errors)
    assert any("email" in e for e in errors)


def test_detect_duplicate_emails_in_upload():
    rows = [
        {"email": "dup@example.com", "first_name": "A", "last_name": "A", "company": "C", "title": "T", "website": "https://c.com", "industry": "I", "country": "US", "campaign": "camp-1"},
        {"email": "dup@example.com", "first_name": "B", "last_name": "B", "company": "D", "title": "T", "website": "https://d.com", "industry": "I", "country": "US", "campaign": "camp-2"},
        {"email": "unique@example.com", "first_name": "C", "last_name": "C", "company": "E", "title": "T", "website": "https://e.com", "industry": "I", "country": "US", "campaign": "camp-3"},
    ]

    duplicates = detect_duplicate_emails(rows)
    assert duplicates == {"dup@example.com"}
