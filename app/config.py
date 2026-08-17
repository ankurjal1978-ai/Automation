from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "drip_automation.db"
DATA_DIR = BASE_DIR / "data"

REQUIRED_FIELDS = [
    "first_name",
    "last_name",
    "email",
    "company",
    "title",
    "website",
    "industry",
    "country",
    "campaign",
]
