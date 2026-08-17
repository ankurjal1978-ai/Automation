# Drip automation

A local Streamlit proof of concept for a Gmail drip marketing orchestration engine.

## Phase 1 scope

This phase focuses on:

- CSV upload
- required field validation
- email validation
- duplicate detection
- SQLite storage
- dashboard metrics
- contact table display

Gmail sending, scheduling, and AI personalization are intentionally not implemented in this phase.

## Expected CSV columns

```text
first_name
last_name
email
company
title
website
industry
country
campaign
```

## Project structure

```text
Drip automation/
  app/
    __init__.py
    config.py
    database.py
    models.py
    services/
      __init__.py
      contact_service.py
  tests/
    test_contact_service.py
  .env.example
  .gitignore
  README.md
  requirements.txt
  app.py
  sample_contacts.csv
  data/
    .gitkeep
```

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

```powershell
streamlit run app.py
```

The local SQLite database is created automatically at `data/drip_automation.db`.

## Credentials

Keep credentials and secrets local. Copy `.env.example` to `.env` when later integrations need secrets, and do not commit `.env` or `.streamlit/secrets.toml`.
